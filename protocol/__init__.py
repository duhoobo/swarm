
def reply_parser_crlf():
    # To allow nested function to modify local variables defined in outer
    # scope.
    lastbyte = [""]

    def reply_parser(data=None):
        if data is None:
            return 1
        elif data == "\r":
            lastbyte[0] = data
            return 1
        elif data == "\n" and lastbyte[0] == "\r":
            return 0
        else:
            return 1

    return reply_parser
