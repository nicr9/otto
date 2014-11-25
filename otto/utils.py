import abc
import os
import os.path
import sys
import json
import subprocess
import re

from getpass import getpass
from lament import ConfigFile
from shutil import move, copytree, rmtree

from otto import *

def rebuild_root_config(path):
    def _ottopack_pair(path):
        dir_path = os.path.dirname(path)
        pack_name = dir_path.split('/')[-1]
        return pack_name, dir_path

    find_raw = shell('find %s -name "%s"' % (path, CMDS_FILE), echo=False)
    results = dict(_ottopack_pair(line) for line in find_raw.splitlines())

    config_path = os.path.join(path, ROOT_FILE)
    with ConfigFile(config_path) as config:
        config['packs'] = results

    return results

def rebuild_cmd_config(path):
    def _ottocmd_name(code):
        match = re.search("^class (.*?)\(", code)
        if match:
            return match.group(1).lower()

    file_pattern = os.path.join(path, '*.py')
    grep_raw = shell('grep %s -He "^class .*("' % file_pattern, echo=False)
    grep_results = [line.split(':')[:2] for line in grep_raw.splitlines()]
    results = {_ottocmd_name(cmd): path for path, cmd in grep_results}

    # Clean up any bad results found
    if None in results:
        del results[None]

    cmds_config = os.path.join(path, CMDS_FILE)
    with ConfigFile(cmds_config) as config:
        config['cmds'] = results

    return results

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
    with ConfigFile(os.path.join(src_dir, ROOT_FILE)) as config:
        return config.get('packs', {})

def pack_empty(pack):
    path = pack_path(pack)
    with ConfigFile(os.path.join(path, CMDS_FILE)) as config:
        return len(config.get('cmds', {})) == 0

### Manipulate Packs

def touch_pack(pack):
    """Make sure the pack directory exists, create config files as needed."""
    dest = pack_path(pack)
    ensure_dir(dest)

    root_config = os.path.join(pack_root(pack), ROOT_FILE)
    with ConfigFile(root_config, True) as config:
        packs = config.setdefault('packs', {})
        packs[pack] = dest

    cmds_config = os.path.join(pack_path(pack), CMDS_FILE)
    with ConfigFile(cmds_config, True) as local_cmds:
        cmds = local_cmds.setdefault('cmds', {})

def update_packs(src_dir, new_packs):
    with ConfigFile(os.path.join(src_dir, ROOT_FILE), True) as config:
        packs = config.setdefault('packs', {})
        packs.update(new_packs)

def move_pack(src_path, src_pack, dest_pack):
    dest = os.path.join(src_path, dest_pack)
    # Add pack to dest config
    with ConfigFile(os.path.join(src_path, ROOT_FILE)) as config:
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
    with ConfigFile(os.path.join(dest_path, ROOT_FILE), True) as config:
        packs = config.setdefault('packs', {})
        packs[dest_pack] = dest

    # copytree to dest
    copytree(
            os.path.join(src_path, src_pack),
            dest
            ) # TODO: What happens if this pack already exists?

    # change cmd paths
    fix_cmds(dest)

def rm_pack(parent_path, pack):
    """Clear any entries relating to a pack from it's parent's ROOT_FILE."""
    config_path = os.path.join(parent_path, ROOT_FILE)

    # Remove pack from config
    with ConfigFile(config_path) as config:
        packs = config.get('packs', {})
        packs.pop(pack, None)

def del_pack(parent_path, pack):
    """Delete the folder associated with a pack."""
    target_path = pack_path(pack)

    # Delete pack dir
    if os.path.isdir(target_path):
        rmtree(target_path)

def rename_ottocmd(src_cmd, dest_cmd, file_path):
    """Edits OttoCmd name within a file."""
    command = r"sed -i 's/class %s(otto.OttoCmd):/class %s(otto.OttoCmd):/' %s"
    shell(command % (
        src_cmd.capitalize(),
        dest_cmd.capitalize(),
        file_path
        ))

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
    with ConfigFile(os.path.join(dest, CMDS_FILE)) as config:
        cmds = config.setdefault('cmds', {})
        for key in cmds:
            rel_path = os.path.join(dest, "%s.py" % key)
            cmds[key] = os.path.abspath(rel_path)

def move_cmd(src, dest):
    """Move a cmd from one pack to an other."""
    src_pack, src_cmd = cmd_split(src, default_pack='local')
    src_path = pack_path(src_pack)
    dest_pack, dest_cmd = cmd_split(dest, default_pack='local')
    dest_path = pack_path(dest_pack)

    rename = src_cmd != dest_cmd

    # Verify old config
    src_cmds_json = os.path.join(src_path, CMDS_FILE)
    if not os.path.isfile(src_cmds_json):
        bail("Can't mv %s:%s, config not found." % (src_pack, src_cmd))

    # Update old config
    py_path = None
    with ConfigFile(src_cmds_json) as config:
        py_path = config['cmds'].pop(src_cmd, None)

    # If CMDS_FILE was corrupt, figure out src file path
    if not py_path:
        py_path = os.path.join(src_path, "%s.py" % src_cmd)

    # Make sure src file exists
    if not os.path.isfile(py_path):
        bail("Couldn't find %s.py" % src_cmd)

    # Touch dest_pack
    touch_pack(dest_pack)

    # Move .py
    dest_file = os.path.join(dest_path, "%s.py" % dest_cmd)
    move(py_path, dest_file)

    # Update new config
    with ConfigFile(os.path.join(dest_path, CMDS_FILE)) as config:
        config['cmds'][dest_cmd] = ''
    fix_cmds(dest_path)

    # Remove compiled file (*.pyc)
    try:
        os.remove(os.path.join(src_path, "%s.pyc" % src_cmd))
    except OSError:
        pass

def clone_all(src, dest): # TODO: Test this
    """Clone a dir containing multiple packs to a different location."""
    ensure_dir(dest)

    # Add pack to dest config
    with ConfigFile(os.path.join(src, ROOT_FILE)) as config:
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
        info("Usage:")
        blue("  $ otto %s %s" % (self._name(), ' '.join(args)))
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
    """Save config to LOCAL_CONFIG"""
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

def orange_format(msg):
    return "\033[91m%s\033[0m" % str(msg)

def bold_format(msg):
    return "\033[1m%s\033[0m" % str(msg)

def blue(msg):
    print blue_format(msg)

def orange(msg):
    print orange_format(msg)

def info(msg):
    print bold_format(msg)

def bullets(messages, bullet="-"):
    for message in messages:
        print " {} {}".format(bullet, message)

def shell(cmd, echo=True, stdout=False):
    outp = ''
    try:
        if echo:
            blue("  $ %s" % cmd)
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
                # self.index
                key = indexed[ans] if isinstance(values, dict) else ans
                self.index = ans

                # self.result
                self.result = values[key]

                # self.key
                if isinstance(values, dict):
                    self.key = key
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
            prompt = bold_format("%s : " % self.header)
            self.result = getpass(prompt)
        except KeyboardInterrupt:
            bail()

class ChangePath(object):
    def __init__(self, path='~'):
        self._base_dir = os.getcwd()
        self._dest_dir = os.path.expanduser(path)

    def __enter__(self):
        os.chdir(self._dest_dir)
        orange("-> %s" % os.getcwd())

    def __exit__(self, a, b, c):
        orange("-> %s" % self._base_dir)
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
