from pkg_resources import Requirement, resource_filename
from subprocess import call as shcall
from os.path import join as path_join
from os.path import isfile

from otto import *
from otto.config import OttoConfig
from otto.cmds import BASE_CMDS
from otto.utils import bail


class OttoDispatcher(object):
    def __init__(self):
        # Default config/conmands
        self.config = OttoConfig()
        self.config.packs.init_base(BASE_CMDS)

        # Check ~/.otto for changes to config
        self.config.update_from_file(GLOBAL_CONFIG)

        # Check ./.otto for changes to config/available commands
        self.config.update_from_file(LOCAL_CONFIG)

    def list_cmds(self):
        self.config.packs.list_cmds()

    def print_docs(self, cmd):
        self.config.packs.print_manpage(cmd)

    def handle(self, cmd, args):
        if not args:
            args = self.config.remember.get(cmd, [])
        try:
            self.config.packs.run(cmd, *args)
        except KeyboardInterrupt:
            bail()

        self.tone()

    def tone(self):
        if self.config.tone:
            local_path = path_join(LOCAL_RES_DIR, self.config.tone)
            global_path = resource_filename(
                    Requirement.parse("otto"),
                    self.config.tone)

            if isfile(local_path):
                path = local_path
            elif isfile(global_path):
                path = global_path
            else:
                print "Tried looking for tone at %s" % global_path
                bail("tone not found: %s" % self.config.tone)

            try:
                shcall(['aplay', '-q', path])
            except Exception as e:
                bail("Couldn't play tone: %s" % e)
