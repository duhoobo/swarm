
class BenchException(Exception):
    pass


class ServerClosed(BenchException):
    pass


class ActionTimeout(BenchException):
    pass


class InvalidReply(BenchException):
    pass


class InvalidScript(BenchException):
    pass
