import abc
import os
import os.path
import sys
import json

OTTO_DIR = '.otto'
OTTO_CONFIG = os.path.join(OTTO_DIR, 'config.json')

class OttoCmd(object):
    """Base class for all `otto` commands"""
    __metaclass__ = abc.ABCMeta

    @classmethod
    def _name(cls):
        return cls.__name__.lower()

    @abc.abstractmethod
    def run(*args, **kwargs):
        """Otto command handler"""
        return

    def cmd_usage(self, args):
        """Print useage for this command and exit"""
        print "Usage:\n  $ otto %s %s" % (self._name(), ' '.join(args))
        sys.exit()

def open_config():
    """Opens config file, creates .otto/ folder if needed"""
    _ensure_otto_dir()

    # Try opening current config
    config = {}
    if os.path.isfile(OTTO_CONFIG):
        with open(OTTO_CONFIG, 'r') as j:
            config = json.load(j)

    return config

def save_config(config):
    """Save config to ./.otto/config.json"""
    _ensure_otto_dir()

    # Save
    with open(OTTO_CONFIG, 'w') as j:
        json.dump(config, j, indent=4)

def _ensure_otto_dir():
    # Ensure .otto/ exists
    if not os.path.isdir(OTTO_DIR):
        os.mkdir(OTTO_DIR)
