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

def _config_dir_and_path(config_path):
    if config_path is None:
        config_dir = OTTO_DIR
        config_path = OTTO_CONFIG
    else:
        config_dir, _ = os.path.split(config_path)

    return config_dir, config_path

def open_config(config_path=None):
    """Opens config file, creates .otto/ folder if needed"""
    config_dir, config_path = _config_dir_and_path(config_path)

    ensure_dir(config_dir)

    # Try opening current config
    config = {}
    if os.path.isfile(config_path):
        with open(config_path, 'r') as j:
            config = json.load(j)

    return config

def save_config(config, config_path=None):
    """Save config to ./.otto/config.json"""
    config_dir, config_path = _config_dir_and_path(config_path)

    ensure_dir(config_dir)

    # Save
    with open(config_path, 'w') as j:
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
            sys.exit()

        if ans.isdigit():
            ans = int(ans)
        else:
            continue


        if 0 <= ans < len(values):
            return ans
        else:
            continue
