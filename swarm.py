#!/usr/bin/env python

import gevent.monkey
gevent.monkey.patch_all()

import click
from resource import getrlimit, setrlimit, RLIMIT_NOFILE

from signal import (
    signal, SIG_IGN, SIGHUP, SIGINT, SIGTERM, SIGPIPE
)
from gevent import get_hub
from gevent.server import StreamServer
from gevent.queue import Queue
from collections import defaultdict

import script
from fakeclient import FakeClient, readable_status
from command import (
    CommandINCR, CommandDECR, CommandQUIT, CommandSTATUS
)


class TCPGateway(StreamServer):
    banner = """
    ===============================
    Welcome to Swarm Remote Console
    ===============================
    """

    usage = (
        "Usage:\n"
        "incr 1000\\n -- Start 1000 new connections\n"
        "decr 100\\n  -- Close 100 random connections\n"
        "stop\\n      -- Stop swarm benchmarker remotely\n"
        "quit\\n      -- Close this control session\n"
        "help\\n      -- Help\n"
    )

    def __init__(self, swarm, listener):
        super(TCPGateway, self).__init__(listener, handle=self._handler,
                                         spawn=2)
        self._swarm = swarm
        print "Listening on %s" % str(listener)

    def _handler(self, sock, address):
        """
        Called by a new greenlet.

        `sock` will be closed by `StreamServer` after this handler exits.
        But, this greenlet/connection won't be kill naturally if we don't use
        `pool` with StreamServer`.
        """
        try:
            self._welcome(sock)

            cmdline = ""
            while True:
                # Read the data one byte per time. We don't need performance
                # here
                char = sock.recv(1)
                if not char:
                    # peer closed
                    break

                if char == "\n":
                    if not self._process_request(sock, cmdline):
                        break
                    cmdline = ""
                else:
                    cmdline += char
        except Exception as e:
            print e
            # just let this greenlet die
            pass

    def _welcome(self, sock):
        sock.sendall(self.banner + "\n")
        sock.sendall(self.usage + "\n")

    def _process_request(self, sock, cmdline):
        if not cmdline:
            return True

        print cmdline

        parts = cmdline.split()
        cmd = parts[0].lower()
        send_ok = False
        standby = True

        if cmd in ["incr", "decr"]:
            try:
                amount = int(parts[1])
            except:
                sock.sendall("Invalid Command\n")
                return

            self._swarm.commit(
                CommandINCR(amount) if cmd == "incr" else CommandDECR(-amount)
            )
            send_ok = True

        elif cmd == "stop":
            self._swarm.commit(CommandQUIT())
            send_ok = True

        elif cmd == "quit":
            standby = False

        else:
            sock.sendall(self.usage + "\n")

        if send_ok:
            sock.sendall("OK\n")

        return standby


class Counters(object):
    def __init__(self):
        self._total = 0
        self._realtime = defaultdict(set)
        self._aggregates = defaultdict(int)

    def update(self, id, status, prev_status):
        if prev_status:
            self._realtime[prev_status].discard(id)
        self._realtime[status].add(id)
        self._aggregates[status] += 1

    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        self._total = value

    def reset(self):
        self._total = 0
        self._realtime = defaultdict(set)
        self._aggregates = defaultdict(int)

    def __str__(self):
        r = ", ".join(["%s: %d" % (readable_status(s), len(t)) for s, t in
                       self._realtime.iteritems() if t])
        a = ", ".join(["%s: %d" % (readable_status(s), c) for s, c in
                       self._aggregates.iteritems()])

        return ("Realtime: total: %d, %s\nAggregates: %s"
                % (self._total, r or "empty", a or "empty"))

    def __repr__(self):
        return "<Counters instance>"


class Swarm(object):
    def __init__(self, listener, server, script_file):
        self._continue = True
        self._stat_timer = None
        self._server = server

        # To save some memory, make all fakeclients share the same script
        self._script = script.load(script_file)
        self._raise_rlimit()
        self._register_signals()

        self._tcpgateway = TCPGateway(self, listener)
        self._commandq = Queue()
        self._counters = Counters()
        self._fakeclients = {}

        print "Try to bench server at %s using %s" % (server, script_file)

    def _raise_rlimit(self):
        soft, hard = getrlimit(RLIMIT_NOFILE)
        print "Default RLIMIT_NOFILE: (%d, %d)" % (soft, hard)
        setrlimit(RLIMIT_NOFILE, (hard, hard))

    def _start_timers(self):
        loop = get_hub().loop
        self._stat_timer = loop.timer(5, 10)
        self._stat_timer.start(self._regularly_stat)

    def _stop_timers(self):
        self._stat_timer.stop()

    def _register_signals(self):
        signal(SIGHUP, SIG_IGN)
        signal(SIGPIPE, SIG_IGN)
        signal(SIGINT, self._stop)
        signal(SIGTERM, self._stop)

    def _regularly_stat(self):
        print "<%s" % ("-" * 10,)
        print self._counters
        print "%s>" % ("-" * 20,)

    def _process_command(self, command):
        if isinstance(command, (CommandINCR, CommandDECR)):
            self._spawn(command.amount)

        elif isinstance(command, CommandQUIT):
            self._continue = False

        elif isinstance(command, CommandSTATUS):
            self._counters.update(command.id, command.status,
                                  command.prev_status)

        else:
            # Just ignore unrecognized commands
            pass

    def _spawn(self, amount=1):
        toadd, amount = (amount > 0), abs(amount)

        if toadd:
            for n in xrange(amount):
                client = FakeClient(self, self._server, self._script)
                client.start()
                self._fakeclients[id(client)] = client
                self._counters.total += 1

        else:
            for n in xrange(amount):
                try:
                    (__, client) = self._fakeclients.popitem()
                    client.stop()
                    self._counters.total -= 1
                except:
                    break

    def _reap(self):
        for __, client in self._fakeclients.iteritems():
            client.stop()

        self._counters.reset()

    def commit(self, command, block=True, timeout=None):
        self._commandq.put(command, block, timeout)

    def run_forever(self):
        self._tcpgateway.start()
        self._start_timers()

        while self._continue:
            command = self._commandq.get(block=True, timeout=None)
            self._process_command(command)

        print "Stopping..."

        self._stop_timers()
        self._tcpgateway.stop()
        self._reap()

    def _stop(self, signum, frame):
        print "Got signal %s, to quit" % signum
        self.commit(CommandQUIT())


@click.command()
@click.option("--script", "-s", is_flag=False, required=True,
              type=click.Path(exists=True, dir_okay=False),
              help="Script file which defines actions")
def cmdline(script):
    from settings import listener, server

    swarm = Swarm(listener, server, script)
    swarm.run_forever()


if __name__ == "__main__":
    cmdline()
