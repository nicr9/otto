import abc
import os
import os.path
import sys
import json
import subprocess

OTTO_DIR = '.otto'
OTTO_CONFIG = os.path.join(OTTO_DIR, 'config.json')

USER_EXIT = "\n\nExiting..."

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
    ensure_dir(OTTO_DIR)

    # Try opening current config
    config = {}
    if os.path.isfile(OTTO_CONFIG):
        with open(OTTO_CONFIG, 'r') as j:
            config = json.load(j)

    return config

def save_config(config):
    """Save config to ./.otto/config.json"""
    ensure_dir(OTTO_DIR)

    # Save
    with open(OTTO_CONFIG, 'w') as j:
        json.dump(config, j, indent=4)

def ensure_dir(path):
    """Looks for directory, creates it if it doesn't exist"""
    if not os.path.isdir(path):
        os.mkdir(path)

def bold(msg):
    print "\033[1m%s\033[0m" % msg

def info(msg):
    print "\033[94m%s\033[0m" % msg

def shell(cmd):
    outp = ''
    try:
        print "\033[1m $ %s \033[0m" % cmd
        outp = subprocess.check_output(cmd, shell=True)
    except CalledProcessError as e:
        pass
    finally:
        return outp

def choose_dialog(values, header=None):
    if header is not None:
        bold(header)

    for indx, val in enumerate(values):
        print " %d) %s" % (indx, val)

    result = -1
    while True:
        try:
            ans = raw_input(">>> ")
        except KeyboardInterrupt:
            print USER_EXIT
            return

        if ans.isdigit():
            ans = int(ans)
        else:
            continue


        if 0 <= ans < len(values):
            return ans
        else:
            continue
