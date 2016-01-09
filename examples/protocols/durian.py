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
