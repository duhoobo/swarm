from . import reply_parser_crlf


def heartbeat(client):
    def make_request():
        return "SS|tcp.heartbeat|7|uid=123\r\n"

    client.send_for_reply(make_request(), reply_parser_crlf())


def create_chatroom(client):
    def make_request():
        return "SS|chat.createroom|16|uid=123&roomid=7\r\n"

    client.send_for_reply(make_request(), reply_parser_crlf())


def enter_chatroom(client):
    def make_request():
        return "SS|chat.enterroom|16|uid=123&roomid=7\r\n"

    client.send_for_reply(make_request(), reply_parser_crlf())


def leave_chatroom(client):
    def make_request():
        return "SS|chat.outroom|16|uid=123&root=7\r\n"

    client.send_for_reply(make_request(), reply_parser_crlf())


def close_chatroom(client):
    def make_request():
        return "SS|chat.closeroom|16|uid=123&roomid=7\r\n"

    client.send_for_reply(make_request(), reply_parser_crlf())


def close_connection(client):
    client.close_connection()
