
def heartbeat(client):
    def make_request():
        return "SS|tcp.heartbeat|7|uid=123\r\n"

    # To allow nested function to modify local variables defined in outer
    # scope.
    last_byte = [""]

    def reply_parser(data=None):
        if data is None:
            return 1
        elif data == "\r":
            last_byte[0] = data
            return 1
        elif data == "\n" and last_byte[0] == "\r":
            return 0
        else:
            return 1

    client.send_for_reply(make_request(), reply_parser)
