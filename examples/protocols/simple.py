
def heartbeat(client, uid):
    def make_request():
        return "hello %s\r\n" % str(uid)

    client.send_noreply(make_request())


def close_connection(client):
    client.close_connection()
