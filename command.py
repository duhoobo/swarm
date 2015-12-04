
class Command(object):
    pass


class CommandINCR(Command):
    def __init__(self, amount):
        self.amount = amount


class CommandDECR(Command):
    def __init__(self, amount):
        self.amount = amount


class CommandQUIT(Command):
    pass


class CommandSTATUS(Command):
    def __init__(self, id, status, prev_status):
        self.id = id
        self.status = status
        self.prev_status = prev_status
