from otto import *
from otto.utils import *
from otto.config import CmdsConfig
from lament import ConfigFile
import os
import os.path

class New(OttoCmd):
    """Used to create new cmds.

For example, if you want to create a new local cmds "new_cmd" with the argument "arg" you would run the following:
  $ otto new new_cmd arg

This will create a hidden directory, modify any config files and open vim with any boilerplate code ready for you to work on.

If you want to create a new packaged cmd, you can specify the pack like this:
  $ otto new pack_name:new_cmd
"""

    cmd_template = """import otto.utils as otto

class %s(otto.OttoCmd):
    def run(self, %s):
        pass
"""

    def _create_cmd(self, cmd_name, cmd_args, cmd_dir, pack_name, pack_config):
        file_name = cmd_name + '.py'
        cmd_path = os.path.join(cmd_dir, file_name)
        cmds_file = os.path.join(cmd_dir, 'cmds.json')

        # Create dir structure
        ensure_dir(cmd_dir)

        # Config
        with ConfigFile(pack_config, True) as config:
            packs = config.setdefault('packs', {})
            packs[pack_name] = cmd_dir

        with ConfigFile(cmds_file, True) as local_cmds:
            cmds = local_cmds.setdefault('cmds', {})
            cmds[cmd_name] = cmd_path

        # Create template for cmd
        with open(cmd_path, 'w') as cmd_file:
            cmd_file.write(
                    self.cmd_template % (
                            cmd_name.capitalize(),
                            ', '.join(cmd_args)
                            )
                    )

        # Allow user to implement new cmd
        edit_file(cmd_path)

    def _split(self, name):
        cmd_split = name.split(':')
        if len(cmd_split) >= 2:
            return cmd_split[:2]
        else:
            return 'local', name

    def _validate(self, pack, cmd):
        if pack == 'base':
            return False
        elif pack not in self._store.cmds:
            return True
        else:
            return cmd not in self._store.cmds[pack]

    def run(self, *args):
        if not args:
            self.cmd_usage(['new_cmd_name', '[cmd_arg_1 ...]'])
        else:
            pack, cmd = self._split(args[0])
            cmd_args = args[1:]

            if not self._validate(pack, cmd):
                info("Sorry, you can't do that")
                bail()

            if pack == 'local':
                self._create_cmd(cmd, cmd_args, LOCAL_CMDS_DIR, 'local', LOCAL_CONFIG)
            else:
                cmd_dir = os.path.join(GLOBAL_DIR, pack)
                self._create_cmd(cmd, cmd_args, cmd_dir, pack, GLOBAL_CONFIG)

class Edit(OttoCmd):
    """Edit local or packaged cmds.

If you want to edit a local cmd called "cmd_name":
  $ otto edit cmd_name

To edit packaged cmds, specify the pack like this:
  $ otto edit pack_name:cmd_name
"""

    def run(self, *args):
        if len(args) != 1:
            self.cmd_usage(['cmd_name'])
        else:
            pack, name = self._store.lookup(args[0])
            if pack == 'base':
                info("Sorry, you can't edit base cmds like %s" % name)
            else:
                cmd_path = self._store.cmds[pack][name]
                edit_file(cmd_path)

class Remember(OttoCmd):
    """Binds a list of arguments to a cmd.

For example, if you wanted to always pass the value "5" to the "cmd_name" cmd:
  $ otto remember cmd_name 5

You can bind as many arguments as you want separated by spaces. To bind values with spaces, you can wrap them in quotes like this:
  $ otto remember cmd_name "The cake is a lie"
"""

    def run(self, *args):
        if not args:
            self.cmd_usage(['cmd_name', '[arg_to_remember1 ...]'])
        else:
            cmd_name = args[0]
            cmd_args = args[1:]

            arg_d = {cmd_name: cmd_args}

            # Open local config
            with ConfigFile(LOCAL_CONFIG, True) as config:
                config.update(
                        remember=arg_d
                        )

class Pack(OttoCmd):
    """Turn .otto into a package to be distributed/installed"""

    def run(self, pack_name):
        pack_path = os.path.basename(pack_name + PACK_EXT)
        pack_root = './pack_root'

        # Make copy of .otto/
        info("Cloning local...")
        clone_pack(LOCAL_DIR, 'local', pack_root, pack_name)

        info("Cleaning up a bit...")
        shell(r'find %s -type f -name "*.pyc" -exec rm -f {} \;' % pack_root)

        # Tar up package
        info("Packing up...")
        shell(r'tar -czf %s %s' % (pack_path, pack_root))

        # Cleanup
        rmtree(pack_root)

class Install(OttoCmd):
    """Install a package as global cmds"""

    def run(self, pack_path):
        from shutil import copytree, rmtree
        pack_name = os.path.basename(pack_path).split(PACK_EXT)[0]
        install_temp = os.path.join(GLOBAL_DIR, '_installing') 

        ensure_dir(install_temp)

        # Untar pack
        shell(r'tar -xzf %s -C %s' % (
            pack_path, 
            install_temp,
            ))

        temp_dir = os.path.join(install_temp, pack_name)

        # Copy pack info to global config
        to_install = get_packs(temp_dir)
        for key, val in to_install.iteritems():
            to_install[key] = os.path.join(GLOBAL_DIR, val)
        update_packs(GLOBAL_DIR, to_install)

        # Fix paths to cmd files
        with ConfigFile(os.path.join(temp_dir, pack_name, 'cmds.json')) as cmds:
            for key, val in cmds['cmds'].iteritems():
                cmds['cmds'][key] = os.path.join(GLOBAL_DIR, val)

        # Copy pack cmds to GLOBAL_DIR
        copytree(
                os.path.join(temp_dir, pack_name),
                os.path.join(GLOBAL_DIR, pack_name),
                )

        # Clean up
        rmtree(install_temp)

class Uninstall(OttoCmd):
    """Interactive prompt to remove installed package"""
    def run(self):
        from shutil import rmtree
        # Get list of installed packages
        installed_packs = get_packs(GLOBAL_DIR)

        # Ask user which to uninstall
        dialog = Dialog("Which pack do you want to uninstall?")
        dialog.choose(installed_packs.keys())
        info('Uninstalling %s...' % dialog.result)

        # Remove pack from config
        with ConfigFile(GLOBAL_CONFIG) as config:
            config['packs'].pop(dialog.result)

        # Delete pack dir
        rmtree(os.path.join(GLOBAL_DIR, dialog.result))

class Wait(OttoCmd):
    """Pause for X number of seconds"""
    def run(self, secs):
        from time import sleep
        if secs.isdigit():
            max_secs = int(secs)
            with SingleLine() as disp:
                for t in range(int(secs), 0, -1):
                    disp(t)
                    sleep(1)

DEFAULT_CMDS = {z._name(): z for z in OttoCmd.__subclasses__()}
