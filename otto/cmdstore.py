"""The following terms are used throughout this file, I thought their use as variable names should be clarified and standardised:
* cmd - the name of an executable cmd.
* pack - the name of a collection of cmds.
* name - Ambiguous, either the name of a cmd or a pack:cmd pair (use cmd_split())
* ottocmd - cmd object.
* cmd_ref - either the path to a file containing code for a cmd, or the cmd object itself.
* pack_keys - a set of pack names.
* pack_cmds - {pack : {cmd: cmd_ref}}
"""
import os.path
import imp
from otto import LOCAL_CMDS_DIR
from otto.utils import info, bail, isOttoCmd

from lament import ConfigFile

CMDS_FILE = 'cmds.json'

def cmd_split(name):
    """Given a name, split into (pack, cmd).

    Pack should default to None if indeterminable."""
    if ':' in name:
        return name.split(':')[:2]
    else:
        return None, name

class CmdStore(object):
    """The CmdStore is a record of all cmds currently available to the user."""
    def __init__(self):
        self.pack_keys = set()
        self.pack_cmds = {}
        self._pack_dirs = {}

    def init_base(self, default_cmds=None):
        """Loads the base cmds."""
        self.pack_keys = set(['base'])
        self.pack_cmds['base'] = default_cmds

    def loadpack(self, pack, pack_dir):
        try:
            with ConfigFile(os.path.join(pack_dir, CMDS_FILE)) as config:
                if 'cmds' in config:
                    for name, path in config['cmds'].iteritems():
                        self._add_cmd(
                                pack,
                                name,
                                path
                                )
        except Exception as e:
            pass
        else:
            self._pack_dirs[pack] = pack_dir

    def _add_cmd(self, pack, cmd, path):
        assert os.path.isfile(path)
        self.pack_keys.add(pack)
        cmd_refs = self.pack_cmds.setdefault(pack, {})
        cmd_refs[cmd] = path

    def _load_cmd(self, pack, cmd, cmd_ref):
        # Base cmds are already loaded
        if isOttoCmd(cmd_ref):
            return cmd_ref

        # Otherwise, import and return OttoCmd subclass
        try:
            cmd_module = imp.load_source(
                    cmd,
                    cmd_ref
                    )
            cmd_class = getattr(cmd_module, cmd.capitalize(), None)
            if cmd_class is None:
                print cmd, "could not be loaded from", cmd_ref
            else:
                return cmd_class
        except SyntaxError as e:
            errmsg = "Syntax error found:\nFile:%s (%s, %s)" % e.args[1][:3]
            bail(errmsg)
        except Exception as e:
            raise e

    def _print(self, pack):
        if pack in self.pack_keys:
            print "* %s" % pack
            for cmd in self.pack_cmds[pack]:
                print "  - %s" % cmd

    def list_cmds(self, pack=None):
        if pack is None:
            self._print('base')
            for key in self.installed_packs():
                self._print(key)
            self._print('local')
        else:
            self._print(pack)

    def _run(self, pack, cmd, *args, **kwargs):
        cmd_ref = self.pack_cmds[pack][cmd]
        ottocmd = self._load_cmd(pack, cmd, cmd_ref)(self) # Import & __init__
        ottocmd.run(*args, **kwargs)

    def run(self, name, *args, **kwargs):
        pack, cmd = self.lookup(name)
        self._run(pack, cmd, *args, **kwargs)

    def installed_packs(self):
        """Returns a set of available pack names, excluding base and local."""
        return self.pack_keys - set(['base', 'local'])

    def find_pack(self, cmd):
        """Given a cmd, determine which pack it belongs to."""
        # Local cmds take presidence
        if 'local' in self.pack_cmds:
            if cmd in self.pack_cmds['local']:
                return 'local'

        # Then check installed cmds
        for key in self.installed_packs():
            if cmd in self.pack_cmds[key]:
                return key

        # Default to base cmds if able
        if cmd in self.pack_cmds['base']:
            return 'base'

    def lookup(self, name):
        """Given a name, determine the best possible pack and cmd."""
        pack, cmd = cmd_split(name)

        if pack is None:
            pack = self.find_pack(cmd)

        if self.is_used(pack, cmd):
            return pack, cmd
        else:
            bail("Couldn't lookup %s, are you sure it's installed?" % name)

    def docs(self, name):
        pack, cmd = self.lookup(name)
        docs = self.pack_cmds[pack][cmd].__doc__

        if docs is None:
            print "%s:%s doesn't seem to have a docstring." % (pack, cmd)
        else:
            title = "%s:%s" % (pack, cmd)
            print title
            print "=" * len(title)
            print docs

    def export(self):
        return self._pack_dirs

    def is_available(self, pack, cmd):
        if pack == 'base':
            return False
        elif pack not in self.pack_keys:
            return True
        else:
            return cmd not in self.pack_cmds[pack]

    def is_used(self, pack, cmd):
        if pack in self.pack_keys and cmd in self.pack_cmds[pack]:
            return True
        else:
            return False
