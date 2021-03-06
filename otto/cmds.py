import os
import os.path

from lament import ConfigFile

from otto import *
from otto.utils import *
from otto.config import CmdsConfig

class New(OttoCmd):
    """Used to create new cmds.

    To create a new local cmd "new_cmd" with the argument "arg" you would run the following:
	$ otto new new_cmd arg

    This will create the folder .otto/ along with the necessary config files and open vim with the boilerplate code ready for you to work on.

    If you would prefer to create a the new cmd in a pack, you can specify the pack like this:
	$ otto new pack_name:new_cmd"""

    cmd_template = """import otto.utils as otto

class %s(otto.OttoCmd):
    def run(self, %s):
        pass"""

    def _create_cmd(self, cmd_name, cmd_args, cmd_dir, pack_name, pack_config):
        file_name = cmd_name + '.py'
        cmd_path = os.path.join(cmd_dir, file_name)
        cmds_file = os.path.join(cmd_dir, CMDS_FILE)

        touch_pack(pack_name)

        with ConfigFile(cmds_file, True) as local_cmds:
            local_cmds['cmds'][cmd_name] = cmd_path

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

    def run(self, *args):
        if not args:
            self.cmd_usage(['new_cmd_name', '[cmd_arg_1 ...]'])
        else:
            pack, cmd = cmd_split(args[0], 'local')
            cmd_args = args[1:]

            if not self._store.is_available(pack, cmd):
                bail("Sorry, you can't do that")

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
	$ otto edit pack_name:cmd_name"""

    def run(self, *args):
        if len(args) != 1:
            self.cmd_usage(['cmd_name'])
        else:
            pack, name = self._store.lookup(args[0])
            if pack == 'base':
                info("Sorry, you can't edit base cmds like %s" % name)
            else:
                cmd_path = self._store.cmds_by_pack[pack][name]
                edit_file(cmd_path)

class Mv(OttoCmd):
    """Move a cmd from one pack to an other."""

    def run(self, src, dest):
        src_pack, src_cmd = cmd_split(src, default_pack='local')
        dest_pack, dest_cmd = cmd_split(dest, default_pack='local')
        dest_file = os.path.join(pack_path(dest_pack), "%s.py" % dest_cmd)

        # Work out exactly what actions to do
        moving = src_pack != dest_pack
        renaming = src_cmd != dest_cmd

        # Perform those actions
        if moving:
            info("Moving...")
            move_cmd(src, dest)
        if renaming:
            info("Renaming...")
            rename_cmd(dest_pack, src_cmd, dest_cmd)
        if not (moving or renaming):
            bail("Nothing to do.")

        # Clean up
        if pack_empty(src_pack):
            info("Source pack is empty, deleting it...")
            src_root = pack_root(src_pack)
            rm_pack(src_root, src_pack)
            del_pack(src_root, src_pack)

        info("Done!")

class Remember(OttoCmd):
    """Binds a list of arguments to a cmd.

    For example, if you wanted to always pass the value "5" to the "cmd_name" cmd:
	$ otto remember cmd_name 5

    You can bind as many arguments as you want separated by spaces. To bind values that contain spaces, you can wrap them in quotes like this:
	$ otto remember cmd_name "The cake is a lie" """

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
    """Turn all local cmds into a package to be distributed/installed.

    The resulting .opack file and the pack it contains will get their name from the argument you provide:
	$ otto pack pack_name"""

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
    """Install any pack from a .opack.

    You specify the .opack like so:
	$ otto install my_pack.opack

    If the .opack contains multiple packs, it will ask you to choose which to install."""

    def run(self, pack_path):
        from shutil import copytree, rmtree
        install_temp = os.path.join(GLOBAL_DIR, '_installing')

        ensure_dir(install_temp)

        # Untar pack
        if os.path.isfile(pack_path):
            shell(r'tar -xzf %s -C %s' % (
                pack_path,
                install_temp,
                ))
        else:
            bail("%s doesn't exist" % pack_path)

        temp_dir = os.path.join(install_temp, 'pack_root')

        # Copy pack info to global config
        to_install = get_packs(temp_dir)
        if len(to_install) > 1:
            d = Dialog("Which pack would you like to install")
            pack_name = d.result
        elif len(to_install) == 1:
            pack_name = to_install.keys()[0]
        else:
            bail("No packs found in %s" % pack_path)
        clone_pack(temp_dir, pack_name, GLOBAL_DIR)

        # Clean up
        rmtree(install_temp)

class Uninstall(OttoCmd):
    """Remove installed packages.

    This cmd takes no arguments and will guide you through the process interactively."""

    def run(self, *args):
        from shutil import rmtree
        # Get list of installed packages
        installed_packs = get_packs(GLOBAL_DIR)

        # Ask user which to uninstall
        dialog = Dialog("Which pack do you want to uninstall?")
        dialog.choose(installed_packs)
        info('Uninstalling %s...' % dialog.key)

        pack = dialog.key
        rm_pack(GLOBAL_DIR, pack)
        del_pack(GLOBAL_DIR, pack)

class Wait(OttoCmd):
    """A simple timer.

    To pause for 5 seconds:
	$ otto wait 5"""

    def run(self, secs):
        from time import sleep
        if secs.isdigit():
            max_secs = int(secs)
            with SingleLine() as disp:
                for t in range(int(secs), 0, -1):
                    disp(t)
                    sleep(1)

class Dr(OttoCmd):
    """Diagnose and repair problems."""

    @staticmethod
    def _file_check(cmd_name, path):
        file_name = os.path.basename(path)

        # Compare cmd name to file name w/o extention
        return cmd_name == file_name[:-3]

    def run(self):
        restore_global = os.path.isdir(GLOBAL_DIR)
        restore_local = os.path.isdir(LOCAL_DIR)

        if restore_global:
            info("Restoring global config files...")
            packs = rebuild_root_config(GLOBAL_DIR)

            for pack, path in packs.iteritems():
                cmds = rebuild_cmd_config(path)

                # Rename any files that don't match up with OttoCmd
                rename_files = {name: file_path
                        for name, file_path in cmds.iteritems()
                        if not self._file_check(name, file_path)}
                for name, old_path in rename_files.iteritems():
                    new_path = os.path.join(path, "%s.py" % name)
                    move(old_path, new_path)
                    cmds[name] = new_path

                # Update pack config with any changes
                pack_cmds_config = os.path.join(pack_path(pack), CMDS_FILE)
                with ConfigFile(pack_cmds_config) as config:
                    config['cmds'] = cmds

                if cmds:
                    info("Pack '%s' contains:" % pack)
                    bullets(cmds.keys())
                else:
                    info("Pack '%s' is empty, deleting it..." % pack)
                    rm_pack(GLOBAL_DIR, pack)
                    del_pack(GLOBAL_DIR, pack)

        if restore_local:
            info("Restoring local config files...")
            packs = rebuild_root_config(LOCAL_DIR)

            for pack, path in packs.iteritems():
                cmds = rebuild_cmd_config(path)

                # Rename any files that don't match up with OttoCmd
                rename_files = {name: file_path
                        for name, file_path in cmds.iteritems()
                        if not self._file_check(name, file_path)}
                for name, old_path in rename_files.iteritems():
                    new_path = os.path.join(path, "%s.py" % name)
                    move(old_path, new_path)
                    cmds[name] = new_path

                # Update pack config with any changes
                pack_cmds_config = os.path.join(pack_path(path), CMDS_FILE)
                with ConfigFile(pack_cmds_config) as config:
                    config['cmds'] = cmds

                if cmds:
                    info("Local pack %s contains:" % pack)
                    bullets(cmds.keys())
                else:
                    info("Local pack '%s' is empty, deleting it..." % pack)
                    rm_pack(LOCAL_DIR, pack)
                    del_pack(LOCAL_DIR, pack)

        if restore_global or restore_local:
            info("Done")
        else:
            info("Nothing to do!")

BASE_CMDS = {z._name(): z for z in OttoCmd.__subclasses__()}
