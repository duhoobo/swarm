`swarm`
=======


`swarm` is a simple benchmarking framework built upon `gevent`.  It can be
used to generate massive simultaneous and persistent TCP connections to a 
server, while each connection interacts with the server using your custom
protocol.

`swarm` does not create any connections on startup, you have to telnet to it
to control its behavior.



How to install
--------------

    python setup.py install



How to use
----------

1. Implement the protocol module for your server. This module should be 
consist of functions you want to use in the script descripted in step 2.
`swarm` provides several examples in `examples/protocol`:

        # examples/protocols/durian.py
        from swarm.protocol import reply_parser_crlf


        def heartbeat(client):
            def make_request():
                return "heartbeat\r\n"

            client.send_for_reply(make_request(), reply_parser_crlf())


        def enter_chatroom(client):
            def make_request():
                return "enter_chatroom\r\n"

            client.send_for_reply(make_request(), reply_parser_crlf())


        def leave_chatroom(client):
            def make_request():
                return "leave_chatroom\r\n"

            client.send_for_reply(make_request(), reply_parser_crlf())


        def close_connection(client):
            client.close_connection()


2. Write a script (in yaml) that defines actions for each connection to 
perform in order. This script will be executed by every connection repeatedly.
Also, under the `examples` directory, an example script using above custom
protocol is provided.

        # examples/scripts/example.yml
        
        protocol: durian
        actions:
          - command: heartbeat
            args:
              uid: 123 
            rounds: [2, 10] 
            sleep_between_rounds: [1, 5]
            sleep_after_action: [1, 5]

          - command: create_chatroom
            args:
              uid: 123 
              rid: 7
            rounds: 1
            sleep_between_rounds: 0
            sleep_after_action: [1, 5]


3. Run `swarm` with your script (Check out `swarm --help` first).


        swarm --listen 127.0.0.1:8400 --server 127.0.0.1:8080 \
            --script /path/to/examples/scripts/example.yml \
            --protocol-dir /path/to/examples/protocols/

4. Use your favorite TCP client (`nc`, `telnet` etc.) to connect to `swarm`
listening address, and then you will see what to do next.

        % telnet 127.0.0.1 8400
        laptop:notes:% telnet 127.0.0.1 8412
        Trying 127.0.0.1...
        Connected to 127.0.0.1.
        Escape character is '^]'.

            ===============================
            Welcome to Swarm Remote Console
            ===============================
            
        Usage:
        incr 1000\n -- Start 1000 new connections
        decr 100\n  -- Close 100 random connections
        stop\n      -- Stop swarm benchmarker remotely
        quit\n      -- Close this control session
        help\n      -- Help

5. Checkout the output of `swarm`. The running state will be printed 
periodically.



API
---

In order to provide the ability to communicate with your server though TCP 
connection for your protocol's implementation, `swarm` executes each action
(the function defined in protocol module) with a instance of `FakeClient` as
the first argument, which has the following network-relative methods:

* `send_for_reply(request, reply_parser)` - Send the request and wait for the 
reply. 

    * `request` should be a string (binary or not) containing the whole 
    request.
    
    * `reply_parser` should be a function object which is used to parse the
    reply. It tells `swarm` how much bytes of data left to read for this reply 
    though its return value.

* `send_noreply(request)` - Send the request and no reply needed.

    * `request` should be a string (binary or not) containing the whole 
    request.

* `close_connection()` - Just close the underlying TCP connection. `swarm` will
create a new connection and start a new iteration for the script.



###Notice

* Don't do any blocking operations `gevent` does not support in your protocol.
You've been warned.



Directives
----------

Once your protocol module is ready, you can tell every connection how to act
by writing a script. 

You have to learn some yaml first, and then you can use the directives
provided by `swarm` to make up your benchmark plan:

* `protocol` - protocol module name. The location of its parent directory is 
specified with command line option `--protocol-dir` of `swarm`.

* `actions` - array of actions. Each action object is consist of:

    * `command` - One of the functions from the protocol module.
    
    * `args` - Extra arguments (beside the instance of `FakeClient`) this 
    command can accept.
    
    * `rounds` - How many rounds to execute for this action per iteration. This
    directive accepts both integer and two-elements array (`swarm` takes it as
    a range and select a integer in it randomly).
    
    * `sleep_between_rounds` - How many seconds to sleep between every round.
    This directive accepts both integer and two-elements array (`swarm` takes
    it as a range and select a integer in it randomly).
    
    * `sleep_after_action` - How many seconds to sleep when current action
    completed. This directive accepts both integer and two-elements array
    (`swarm` taks it as a range and select a integer in it randomly).



Tuning your OS
--------------


To reduce memory usage, `swarm` configures every connection with minimum value
for send/receve buffer by default.

To increase concurrency of `swarm`, you still have to

* raise the open files limit,

* increase the system port range,

or `swarm` will fail you at some point. :)



TODO
----

Please do tell me what you need, my goddess.


