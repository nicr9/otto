import abc
import os
import os.path
import sys
import json
import subprocess

from getpass import getpass
from lament import ConfigFile
from shutil import copyfile, copytree, rmtree

from otto import *

def bail(msg=None):
    info("\nExiting: %s" % msg if msg else "\nExiting...")
    sys.exit()

### Pack Info

def pack_root(pack):
    return LOCAL_DIR if pack == 'local' else GLOBAL_DIR

def pack_path(pack):
    """Determine a pack's directory."""
    return os.path.join(pack_root(pack), pack)

def get_packs(src_dir):
    with ConfigFile(os.path.join(src_dir, 'config.json')) as config:
        return config.get('packs', {})

### Manipulate Packs

def touch_pack(pack):
    """Make sure the pack directory exists, create config files as needed."""
    dest = pack_path(pack)
    ensure_dir(dest)

    root_config = os.path.join(pack_root(pack), 'config.json')
    with ConfigFile(root_config, True) as config:
        packs = config.setdefault('packs', {})
        packs[pack] = dest

    cmds_config = os.path.join(pack_path(pack), 'cmds.json')
    with ConfigFile(cmds_config, True) as local_cmds:
        cmds = local_cmds.setdefault('cmds', {})

def update_packs(src_dir, new_packs):
    with ConfigFile(os.path.join(src_dir, 'config.json'), True) as config:
        packs = config.setdefault('packs', {})
        packs.update(new_packs)

def move_pack(src_path, src_pack, dest_pack):
    dest = os.path.join(src_path, dest_pack)
    # Add pack to dest config
    with ConfigFile(os.path.join(src_path, 'config.json')) as config:
        config['packs'][dest_pack] = dest_pack
        del config['packs'][src_pack]

    # copytree to dest
    copytree(
            os.path.join(src_path, src_pack),
            dest,
            )

    # change cmd paths
    fix_cmds(dest)

def clone_pack(src_path, src_pack, dest_path, dest_pack=None):
    dest_pack = dest_pack or src_pack
    dest = os.path.join(dest_path, dest_pack)

    # Ensure dest dir
    ensure_dir(dest_path)

    # Add pack to dest config
    with ConfigFile(os.path.join(dest_path, 'config.json'), True) as config:
        packs = config.setdefault('packs', {})
        packs[dest_pack] = dest

    # copytree to dest
    copytree(
            os.path.join(src_path, src_pack),
            dest
            ) # TODO: What happens if this pack already exists?

    # change cmd paths
    fix_cmds(dest)

def rm_pack(pack):
    """Delete the pack folder and clear the entry from config.json."""
    parent_path = LOCAL_DIR if pack == 'local' else GLOBAL_DIR
    config_path = os.path.join(parent_path, 'config.json')
    target_path = pack_path(pack)

    # Remove pack from config
    with ConfigFile(config_path) as config:
        packs = config.get('packs', {})
        packs.pop(pack, None)

    # Delete pack dir
    if os.path.isdir(target_path):
        rmtree(target_path)

### Cmd Info

def cmd_split(name, default_pack=None):
    """Given the name of a cmd, split it into (pack, cmd).

    A default pack can be specified if the name cannot be split."""
    cmd_split = name.split(':')
    if len(cmd_split) >= 2:
        return cmd_split[:2]
    else:
        return default_pack, name

### Manipulate cmds

def fix_cmds(dest):
    """Change cmd.json cmds values from file names to absolute paths."""
    with ConfigFile(os.path.join(dest, 'cmds.json')) as config:
        cmds = config.setdefault('cmds', {})
        for key in cmds:
            rel_path = os.path.join(dest, "%s.py" % key)
            cmds[key] = os.path.abspath(rel_path)

def move_cmd(src, dest):
    """Move a cmd from one pack to an other."""
    src_pack, src_cmd = cmd_split(src)
    src_path = pack_path(src_pack)
    dest_pack, dest_cmd = cmd_split(dest)
    dest_path = pack_path(dest_pack)

    # Update old config
    src_pack_empty = False
    py_path = None
    with ConfigFile(os.path.join(src_path, 'cmds.json')) as config:
        py_path = config['cmds'].pop(src_cmd, None)

        if not config['cmds']:
            src_pack_empty = True

    # If cmds.json was corrupt, figure out src file path
    if not py_path:
        py_path = os.path.join(src_path, "%s.py" % src_cmd)

    # Make sure src file exists
    if not os.path.isfile(py_path):
        bail("Couldn't find %s.py" % src_cmd)

    # Touch dest_pack
    touch_pack(dest_pack)

    # Move .py
    copyfile(py_path, os.path.join(dest_path, "%s.py" % dest_cmd))

    # Update new config
    with ConfigFile(os.path.join(dest_path, 'cmds.json')) as config:
        config['cmds'][dest_cmd] = ''
    fix_cmds(dest_pack)

    return src_pack_empty

def clone_all(src, dest): # TODO: Test this
    """Clone a dir containing multiple packs to a different location."""
    ensure_dir(dest)

    # Add pack to dest config
    with ConfigFile(os.path.join(src, 'config.json')) as config:
        src_packs = config.setdefault('packs', {})
        for pack_name, pack_path in src_packs:
            clone_pack(
                    os.path.join(src, pack_path),
                    pack_name,
                    os.path.join(dest, pack_path),
                    pack_name,
                    )

    update_packs(dest, src_packs)

class OttoCmd(object):
    """Base class for all `otto` commands."""
    __metaclass__ = abc.ABCMeta

    def __init__(self, store):
        self._store = store

    @classmethod
    def _name(cls):
        return cls.__name__.lower()

    @abc.abstractmethod
    def run(*args, **kwargs):
        """Otto command handler."""
        return

    def cmd_usage(self, args):
        """Print useage for this command and exit."""
        print "Usage:\n  $ otto %s %s" % (self._name(), ' '.join(args))
        sys.exit()

isOttoCmd = lambda cmd: OttoCmd in getattr(cmd, '__bases__', [])

def _config_dir_and_path(config_path):
    if config_path is None:
        config_dir = LOCAL_DIR
        config_path = LOCAL_CONFIG
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
        os.makedirs(path)

def blue_format(msg):
    return "\033[94m%s\033[0m" % str(msg)

def bold_format(msg):
    return "\033[1m%s\033[0m" % str(msg)

def blue(msg):
    print blue_format(msg)

def info(msg):
    print bold_format(msg)

def shell(cmd, echo=True, stdout=False):
    outp = ''
    try:
        if echo:
            blue(" $ %s" % cmd)
        if stdout:
            subprocess.call(cmd, shell=True)
        else:
            outp = subprocess.check_output(cmd, shell=True)
    except CalledProcessError as e:
        pass
    finally:
        return outp

def edit_file(file_path):
    subprocess.call(['vim', file_path])

class Dialog(object):
    def __init__(self, header):
        self.header = header
        self.result = None

    def _validate(self):
        if self.result is not None:
            raise Exception("This dialog has already been used")

    def choose(self, values, subvalue=None):
        self._validate()

        if self.header is not None:
            info("%s : " % self.header)

        indexed = values.keys() if isinstance(values, dict) else values
        for indx, val in enumerate(indexed):
            if subvalue:
                print " %d) %s" % (indx, val[subvalue])
            else:
                print " %d) %s" % (indx, val)

        while True:
            try:
                ans = raw_input(">>> ")
            except KeyboardInterrupt:
                bail()

            if ans.isdigit():
                ans = int(ans)
            else:
                continue

            if 0 <= ans < len(values):
                key = indexed[ans] if isinstance(values, dict) else ans
                self.result = values[key]
                self.index = ans
                break
            else:
                continue

    def input(self, default=None, parse=None):
        self._validate()

        if default is None or default is "":
            prompt = "%s : " % self.header
        else:
            prompt = "%s [%s] : " % (self.header, default)

        bold_prompt = bold_format(prompt)

        while True:
            try:
                temp = raw_input(bold_prompt)
            except KeyboardInterrupt:
                bail()

            if temp == "" and default is None:
                print "Try again"
                continue
            else:
                temp = temp if temp != "" else default
                try:
                    self.result = temp if not parse else parse(temp)
                except:
                    raise Exception(
                            "Failed to parse input %s using %s" % (temp, str(parse))
                            )
                break

    def yesno(self, yes='y', no='n'):
        self._validate()

        prompt = bold_format("%s (%s/%s) : " % (self.header, yes, no))

        try:
            temp = raw_input(prompt)
        except KeyboardInterrupt:
            bail()

        if temp == yes:
            self.result = True
        elif temp == no:
            self.result = False
        else:
            bail()

    def secret(self):
        self._validate()

        try:
            self.result = getpass("%s : " % self.header)
        except KeyboardInterrupt:
            bail()

class ChangePath(object):
    def __init__(self, path='~'):
        self._base_dir = os.getcwd()
        self._dest_dir = os.path.expanduser(path)

    def __enter__(self):
        os.chdir(self._dest_dir)

    def __exit__(self, a, b, c):
        os.chdir(self._base_dir)

class SingleLine(object):
    def __init__(self):
        self.stdout = sys.stdout
        self.last_val = 0

    def __enter__(self):
        def f(val):
            val_len = len(str(val))
            len_diff = self.last_val - val_len
            if len_diff > 0:
                self.stdout.write("\r%s%s" % (val, ' ' * len_diff))
            else:
                self.stdout.write("\r%s" % val)
            self.stdout.flush()
            self.last_val = val_len

        return f

    def __exit__(self, a, b, c):
        self.stdout.write("\n")

def debug_on():
    global shell

    def _debug(cmd, *args):
        blue(" $ %s" % cmd)
        return ''

    shell = _debug
