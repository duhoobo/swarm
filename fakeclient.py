import time
from random import randint
import socket
from socket import (
    create_connection, SOL_SOCKET, SO_RCVBUF, SO_SNDBUF
)
from gevent import Greenlet, GreenletExit

import script
from command import CommandSTATUS
from errors import BenchException, ServerClosed, CloseForcibly


INITIAL = 100000
STARTED = INITIAL + 1
CONNECT = INITIAL + 2
ACTING = INITIAL + 3
STANDBY = INITIAL + 4
TIMEDOUT = INITIAL + 5
FATAL = INITIAL + 6
KILLED = INITIAL + 7

_readable_status = {
    INITIAL: "initial",
    STARTED: "started",
    CONNECT: "connect",
    ACTING: "acting",
    STANDBY: "standby",
    TIMEDOUT: "timedout",
    FATAL: "fatal",
    KILLED: "killed"
}


def readable_status(status):
    return _readable_status.get(status, str(status))


class FakeClient(object):
    """
    A fake client with persistent connection.

    Driven by a dedicated greenlet, it will die trying to operate by the rules
    from the script orderly, round and round.
    """

    def __init__(self, swarm, server, script):
        self._swarm = swarm
        self._server = server
        self._socket = None
        self._greenlet = Greenlet(self._run)

        self._status = INITIAL
        self._prev_status = None
        self._script = script
        self._id = id(self)

    def _report(self, status):
        """
        Report to swarm immediately on status change
        """
        if status != self._status:
            self._swarm.commit(CommandSTATUS(self._id, status, self._status))
            self._status, self._prev_status = (status, self._status)

    def _reconnect_server(self):
        """
        Die trying
        """
        while True:
            try:
                # To scatter connect requests
                time.sleep(randint(1, 20))

                self._report(CONNECT)
                self._disconnect_server()
                self._socket = create_connection(self._server, 3)
                self._socket.setsockopt(SOL_SOCKET, SO_RCVBUF, 128)
                self._socket.setsockopt(SOL_SOCKET, SO_SNDBUF, 1024)

                break

            except socket.error as e:
                # A fact: `socket.timeout`, `socket.herror`, and
                # `socket.gaierror` are all subclasses of `socket.error`.
                self._report(e.args[0])
                continue

    def _disconnect_server(self):
        if self._socket:
            self._socket.close()
            self._socket = None

    def _run(self):
        try:
            self._report(STARTED)
            self._reconnect_server()

            while True:
                try:
                    self._report(ACTING)
                    script.execute(self, self._script)
                    self._report(STANDBY)

                except (socket.error, BenchException) as e:
                    self._report(e.args[0])
                    self._reconnect_server()

        except GreenletExit:
            self._report(KILLED)

        except:
            self._report(FATAL)
            # let gevent print this exception
            raise

        finally:
            self._disconnect_server()

    def start(self):
        self._greenlet.start()

    def stop(self):
        self._greenlet.kill()
        self._greenlet.join()

    def send_for_reply(self, data, reply_parser):
        """
        Called by object of Script.

        Exceptions raised here should be handled in `_run`.
        """
        self._socket.sendall(data)

        need = reply_parser(None)
        while need > 0:
            data = self._socket.recv(need)
            if not data:
                raise ServerClosed("server closed")

            need = reply_parser(data)

    def send_noreply(self, data):
        self._socket.sendall(data)

    def close_connection(self):
        raise CloseForcibly("client closed")
