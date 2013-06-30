import abc
import os
import os.path
import sys

OTTO_DIR = '.otto'
OTTO_CONFIG = os.path.join(OTTO_DIR, 'config.json')

class OttoCmd(object):
    __metaclass__ = abc.ABCMeta

    @classmethod
    def _name(cls):
        return cls.__name__.lower()

    @abc.abstractmethod
    def run(*args, **kwargs):
        """Otto command handler"""
        return

    def cmd_usage(self, args):
        print "Usage:\n  $ otto %s %s" % (self._name(), ' '.join(args))
        sys.exit()
