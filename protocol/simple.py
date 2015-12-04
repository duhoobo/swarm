
def heartbeat(client):
    def make_request():
        return "hello"

    client.send_noreply(make_request())
