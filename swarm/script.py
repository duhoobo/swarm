import yaml
from time import sleep
from inspect import getcallargs
from random import randint
from importlib import import_module

from swarm.errors import InvalidScript


options = {
    "command": {
        "must": True, "type": str, "default": None,
        "range": False,
    },
    "args": {
        "must": False, "type": dict, "default": {},
        "range": False,
    },
    "rounds": {
        "must": False, "type": (int, list), "default": 1,
        "range": True,
    },
    "sleep_between_rounds": {
        "must": False, "type": (int, list), "default": 1,
        "range": True,
    },
    "sleep_after_action": {
        "must": False, "type": (int, list), "default": 1,
        "range": True,
    },
}


def _random_or_straight(value):
    if isinstance(value, list):
        return randint(value[0], value[1])
    else:
        return value


def execute(client, script):
    protocol = script["protocol"]

    for action in script["actions"]:
        name = action["command"]
        args = action["args"]
        rounds = _random_or_straight(action["rounds"])
        sleep_between_rounds = action["sleep_between_rounds"]
        sleep_after_action = action["sleep_after_action"]

        call = getattr(protocol, name)

        for n in xrange(rounds):
            call(client, **args)
            sleep(_random_or_straight(sleep_between_rounds))

        sleep(_random_or_straight(sleep_after_action))


def load(script_file):
    with open(script_file, "r") as f:
        script = yaml.load(f)

        try:
            protocol_module_name = script["protocol"]
        except:
            raise InvalidScript("protocol is missing")

        try:
            protocol = import_module(protocol_module_name)
        except ImportError:
            raise InvalidScript("protocol `%s` not exists"
                                % script["protocol"])

        for n, action in enumerate(script["actions"]):
            for key, value in options.iteritems():
                if value["must"] and key not in action:
                    raise InvalidScript("%s is required in action %d" %
                                        (key, n))
                if key in action:
                    if not isinstance(action[key], value["type"]):
                        raise InvalidScript("Invalid type for %s in"
                                            "action %d" % (key, n))

                    if value["range"] and isinstance(action[key], list):
                        a, b = action[key]
                        if (not isinstance(a, int) or not isinstance(b, int)
                                or a > b):
                            raise InvalidScript("Invalid range for %s in"
                                                "action %d" % (key, n))
                else:
                    action[key] = value["default"]
        try:
            func = getattr(protocol, action["command"])
            getcallargs(func, None, **action["args"])
        except AttributeError:
            raise InvalidScript("command '%s' not implemented yet" %
                                action["action"])
        except TypeError:
            raise InvalidScript("Invalid args for command '%s'" %
                                action["command"])

        script["protocol"] = protocol

    if not script:
        raise InvalidScript("script file empty")

    return script
