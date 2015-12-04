import time
import yaml

from errors import InvalidScript
# from protocol import simple as protocol
from protocol import durian as protocol


options = {
    "action": {"must": True, "type": str, "default": None},
    "rounds": {"must": False, "type": int, "default": None,
               "default": 1},
    "sleep_between_rounds": {"must": False, "type": int, "default": 1},
    "sleep_after_action": {"must": False, "type": int, "default": 5},
}


def execute(client, script):
    for action in script:
        name = action["action"]
        rounds = action["rounds"]
        sleep_between_rounds = action["sleep_between_rounds"]
        sleep_after_action = action["sleep_after_action"]

        call = getattr(protocol, name)

        for n in xrange(rounds):
            call(client)
            time.sleep(sleep_between_rounds)

        time.sleep(sleep_after_action)


def load(script_file):
    with open(script_file, "r") as f:
        script = yaml.load(f)

        for n, action in enumerate(script):
            for key, value in options.iteritems():
                if value["must"] and key not in action:
                    raise InvalidScript("%s is required in action %d"
                                        % (key, n))
                if key in action:
                    action[key] = value["type"](action[key])
                else:
                    action[key] = value["default"]
        try:
            getattr(protocol, action["action"])
        except:
            raise InvalidScript("action '%s' not implemented yet"
                                % action["action"])

    if not script:
        raise InvalidScript("script file empty")

    return script
