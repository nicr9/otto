import os.path
import imp
from otto import LOCAL_CMDS_DIR, CMDS_FILE
from otto.utils import info, bail, isOttoCmd, cmd_split
from lament import ConfigFile


class CmdStore(object):
    def __init__(self):
        self.packs = set()
        self.cmds = {}
        self._dirs = {}
        self._ready = False

    def init(self, default_cmds=None):
        self._ready = True
        self.packs = set(['base'])
        self.cmds['base'] = default_cmds

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
        self.packs.add(pack)
        cmds = self.cmds.setdefault(pack, {})
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

    def list_cmds(self, pack=None):
        def _print_pack_contents(pack):
            if pack in self.packs:
                print "* %s" % pack
                for cmd in self.cmds[pack]:
                    print "  - %s" % cmd

        if pack is None:
            _print_pack_contents('base')
            for key in self.installed_packs():
                _print_pack_contents(key)
            _print_pack_contents('local')
        else:
            _print_pack_contents(pack)

    def _run(self, pack, name, *args, **kwargs):
        cmd = self.cmds[pack][name]
        ottocmd = self._load_cmd(pack, name, cmd)(self) # Import & __init__
        ottocmd.run(*args, **kwargs)

    def run(self, name, *args, **kwargs):
        pack, cmd = self.lookup(name)
        self._run(pack, cmd, *args, **kwargs)

    def installed_packs(self):
        """Returns a set of available pack names, excluding base and local."""
        return self.packs - set(['base', 'local'])

    def find_pack(self, cmd):
        """Given a cmd, determine which pack it belongs to."""
        # Local cmds take presidence
        if 'local' in self.cmds:
            if cmd in self.cmds['local']:
                return 'local'

        # Then check installed cmds
        for key in self.installed_packs():
            if cmd in self.cmds[key]:
                return key

        # default to base cmds if able
        if cmd in self.cmds['base']:
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
        # Find OttoCmd class
        pack, cmd = self.lookup(name)
        ottocmd = self.cmds[pack][cmd]
        if isinstance(ottocmd, unicode):
            ottocmd = self._load_cmd(pack, cmd, ottocmd)

        docs = ottocmd.__doc__
        if docs is None:
            print "%s:%s doesn't seem to have a docstring." % (pack, cmd)
        else:
            cmd_name = "%s:%s" % (pack, cmd)
            doc_lines = [line.lstrip(' ') for line in docs.split('\n')]

            print cmd_name
            print "=" * len(cmd_name)
            print '\n'.join(doc_lines)

    def export(self):
        return self._dirs

    def is_available(self, pack, cmd):
        """Check whether a pack/cmd name pair is already in use."""
        if pack == 'base':
            return False
        elif pack not in self.cmds:
            return True
        else:
            return cmd not in self.cmds[pack]

    def is_used(self, pack, cmd):
        if pack in self.cmds and cmd in self.cmds[pack]:
            return True
        else:
            return False
