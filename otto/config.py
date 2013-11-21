import os.path
import imp
from otto import LOCAL_CMDS_DIR
from otto.utils import info, bail, isOttoCmd

from lament import *

CMDS_FILE = 'cmds.json'

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
                                os.path.join(cmds_dir, path)
                                )
        except Exception as e:
            pass
        else:
            self._dirs[pack] = cmds_dir

    def _add_cmd(self, pack, name, cmd):
        assert isinstance(cmd, OttoCmd) or os.path.isfile(cmd)
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
            print "Whoops, syntax error found:"
            print "File:%s (%s, %s)" % e.args[1][:3]
            sys.exit()
        except Exception as e:
            raise e

    def _print(self, pack):
        if pack in self.packs:
            print "* %s" % pack
            for cmd in self.cmds[pack]:
                print "  - %s" % cmd

    def list_cmds(self, pack=None):
        if pack is None:
            installed = self.packs - set(['base', 'local'])
            self._print('base')
            for key in installed:
                self._print(key)
            self._print('local')
        else:
            self._print(pack)

    def _run(self, pack, name, *args, **kwargs):
        cmd = self.cmds[pack][name]
        ottocmd = self._load_cmd(pack, name, cmd)() # Import & __init__
        ottocmd.run(*args, **kwargs)

    def run(self, name, *args, **kwargs):
        pack, cmd = self.lookup(name)
        self._run(pack, cmd, *args, **kwargs)

    def lookup(self, name):
        pack, cmd = None, None
        if ':' in name:
            pack, cmd = name.split(':')[:2]
            if pack not in self.cmds:
                info("Couldn't find %s, are you sure it's installed?" % pack)
                bail()

        else:
            if 'local' in self.cmds:
                if name in self.cmds['local']:
                    pack = 'local'

            installed = self.packs - set(['base', 'local'])
            for key in installed:
                if name in self.cmds[key]:
                    pack = key

            if name in self.cmds['base']:
                pack = 'base'

            cmd = name

        if pack and cmd:
            return pack, cmd
        else:
            info("Couldn't lookup '%s'" % name)
            bail()

    def docs(self, name):
        pack, cmd = self.lookup(name)
        docs = self.cmds[pack][cmd].__doc__
        if docs is None:
            print "%s:%s doesn't seem to have a docstring." % (pack, cmd)
        else:
            cmd_name = "%s:%s" % (pack, cmd)
            print cmd_name
            print "=" * len(cmd_name)
            print docs

    def export(self):
        return self._dirs

class CmdsConfig(LamentConfig):
    @config('cmds', dict)
    def cmds(self, config, obj):
        config.update(obj)

class OttoConfig(LamentConfig):
    @config('packs', CmdStore)
    def packs(self, config, obj):
        for key, val in obj.iteritems():
            config.loadpack(key, val)
        return config

    @export('packs')
    def ex_packs(self, config):
        return config.export()

    @config('remember', dict)
    def remember(self, config, obj):
        config.update(obj)
        return config

    @config('tone', str)
    def tone(self, config, obj):
        if not isfile(obj):
            return config
        return obj
