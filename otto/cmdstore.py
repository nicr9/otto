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
    def __init__(self):
        self.pack_keys = set()
        self.pack_cmds = {}
        self._dirs = {}
        self._ready = False

    def init(self, default_cmds=None):
        self._ready = True
        self.pack_keys = set(['base'])
        self.pack_cmds['base'] = default_cmds

    def loadpack(self, pack, cmds_dir):
        try:
            with ConfigFile(os.path.join(cmds_dir, CMDS_FILE)) as config:
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
            self._dirs[pack] = cmds_dir

    def _add_cmd(self, pack, name, cmd):
        assert os.path.isfile(cmd)
        self.pack_keys.add(pack)
        cmds = self.pack_cmds.setdefault(pack, {})
        cmds[name] = cmd

    def _load_cmd(self, pack, name, cmd_ref):
        if isOttoCmd(cmd_ref):
            return cmd_ref
        try:
            cmd_module = imp.load_source(
                    name,
                    cmd_ref
                    )
            cmd_class = getattr(cmd_module, name.capitalize(), None)
            if cmd_class is None:
                print name, "could not be loaded from", cmd_ref
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

    def _run(self, pack, name, *args, **kwargs):
        cmd = self.pack_cmds[pack][name]
        ottocmd = self._load_cmd(pack, name, cmd)(self) # Import & __init__
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

        # default to base cmds if able
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
            cmd_name = "%s:%s" % (pack, cmd)
            print cmd_name
            print "=" * len(cmd_name)
            print docs

    def export(self):
        return self._dirs

    def is_available(self, pack, cmd):
        if pack == 'base':
            return False
        elif pack not in self.pack_cmds:
            return True
        else:
            return cmd not in self.pack_cmds[pack]

    def is_used(self, pack, cmd):
        if pack in self.pack_cmds and cmd in self.pack_cmds[pack]:
            return True
        else:
            return False
