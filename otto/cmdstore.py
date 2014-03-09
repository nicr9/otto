import os.path
import imp
from otto import LOCAL_CMDS_DIR, CMDS_FILE
from otto.utils import info, bail, isOttoCmd, cmd_split, orange
from lament import ConfigFile


class CmdStore(object):
    def __init__(self):
        self.pack_keys = set()
        self.cmds_by_pack = {}
        self._pack_dirs = {}
        self._ready = False

    def init(self, default_cmds=None):
        self._ready = True
        self.pack_keys = set(['base'])
        self.cmds_by_pack['base'] = default_cmds

    def load_pack(self, pack_name, pack_dir):
        try:
            config_path = os.path.join(pack_dir, CMDS_FILE)
            with ConfigFile(config_path) as config:
                if 'cmds' in config:
                    for name, path in config['cmds'].iteritems():
                        self._add_cmd(
                                pack_name,
                                name,
                                path
                                )

        except Exception:
            orange("WARNING: %s may be corrupt, please run `otto dr`" % config_path)
        else:
            self._pack_dirs[pack_name] = pack_dir

    def _add_cmd(self, pack_name, cmd_name, cmd_path):
        assert os.path.isfile(cmd_path)
        self.pack_keys.add(pack_name)
        cmds = self.cmds_by_pack.setdefault(pack_name, {})
        cmds[cmd_name] = cmd_path

    def _load_cmd(self, pack_name, cmd_name, cmd_ref):
        """Because some cmds are stored in the cache as either a class or as a
        path to the .py file, this method is needed to disambiguate.

        Given the following arguments:
            pack_name: The pack a cmd belongs to.
            cmd_name: The name of the cmd.
            cmd_ref: Either the OttoCmd object or the path to it's file.

        This method will always return the corresponding OttoCmd class."""

        # Base cmds are already loaded
        if isOttoCmd(cmd_ref):
            return cmd_ref

        # Otherwise, import and return OttoCmd subclass
        try:
            cmd_module = imp.load_source(
                    cmd_name,
                    cmd_ref
                    )
            cmd_class = getattr(cmd_module, cmd_name.capitalize(), None)
            if not isOttoCmd(cmd_class):
                print cmd_name, "could not be loaded from", cmd_ref
            else:
                return cmd_class

        except SyntaxError as e:
            errmsg = "Syntax error found:\nFile:%s (%s, %s)" % e.args[1][:3]
            bail(errmsg)
        except Exception as e:
            raise e

    def list_cmds(self, pack=None):
        def _print_pack_contents(pack):
            if pack in self.pack_keys:
                print "* %s" % pack
                for cmd in self.cmds_by_pack[pack]:
                    print "  - %s" % cmd

        if pack is None:
            _print_pack_contents('base')
            for key in self.installed_packs():
                _print_pack_contents(key)
            _print_pack_contents('local')
        else:
            _print_pack_contents(pack)

    def _run(self, pack_name, cmd_name, *args, **kwargs):
        """Looks up cmd class in cache, initialises it and runs it."""
        cmd_ref = self.cmds_by_pack[pack_name][cmd_name]
        ottocmd = self._load_cmd(pack_name, cmd_name, cmd_ref)(self)
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
        if 'local' in self.cmds_by_pack:
            if cmd in self.cmds_by_pack['local']:
                return 'local'

        # Then check installed cmds
        for pack in self.installed_packs():
            if cmd in self.cmds_by_pack[pack]:
                return pack

        # Default to base cmds if able
        if cmd in self.cmds_by_pack['base']:
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
        ottocmd = self.cmds_by_pack[pack][cmd]
        if isinstance(ottocmd, unicode):
            ottocmd = self._load_cmd(pack, cmd, ottocmd)

        docs = ottocmd.__doc__
        if docs is None:
            print "%s:%s doesn't seem to have a docstring." % (pack, cmd)
        else:
            full_name = "%s:%s" % (pack, cmd)
            doc_lines = [line.lstrip(' ') for line in docs.split('\n')]

            print full_name
            print "=" * len(full_name)
            print '\n'.join(doc_lines)

    def export(self):
        return self._pack_dirs

    def is_available(self, pack, cmd):
        """Check whether a pack/cmd name pair is already in use."""
        if pack == 'base':
            return False
        elif pack not in self.cmds_by_pack:
            return True
        else:
            return cmd not in self.cmds_by_pack[pack]

    def is_used(self, pack, cmd):
        if pack in self.cmds_by_pack and cmd in self.cmds_by_pack[pack]:
            return True
        else:
            return False
