from otto import *
from otto.utils import *
from otto.config import CmdsConfig
from lament import ConfigFile
import os
import os.path

class New(OttoCmd):
    """Used to create boilerplate for new local commands.

For example, if you want to create a new command "do_something" with the argument "with" you would run the following:
  $ otto new do_something with

This will create a hidden directory with the boilerplate code ready for you to extend and a config file enabling the new command."""

    cmd_template = """import otto.utils as otto

class %s(otto.OttoCmd):
    def run(self, %s):
        pass
"""

    def run(self, *args):
        if not args:
            self.cmd_usage(['new_command_name', '[cmd_arg_1 ...]'])
        else:
            cmd_name = args[0]
            cmd_args = args[1:]

            file_name = cmd_name + '.py'
            cmd_path = os.path.join(LOCAL_CMDS_DIR, file_name)
            cmds_file = os.path.join(LOCAL_CMDS_DIR, 'cmds.json')

            # Create dir structure
            ensure_dir(LOCAL_CMDS_DIR)

            # Config
            with ConfigFile(LOCAL_CONFIG, True) as config:
                config['packs'] = {
                        'local': LOCAL_CMDS_DIR,
                        }

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

class Remember(OttoCmd):
    """Binds named arguments to a command.

For example, if you wanted to bind the value "this" to the do_something command's argument named "with":
  $ otto remember do_something with:this

To bind more complicated values, you can wrap the binding in quotes like this:
  $ otto remember do_something "with:something else altogether" """

    def run(self, *args):
        if not args:
            self.cmd_usage(['command_name', '[arg_to_remember1 ...]'])
        else:
            cmd_name = args[0]
            cmd_args = args[1:]

            # Split up args
            args_split = [z.split(':') for z in cmd_args if z.count(':') == 1]

            # Turn into dict
            args_d = dict(args_split)

            # Open local config
            with ConfigFile(LOCAL_CONFIG, True) as config:
                config.update(
                        remember={
                            cmd_name: args_d,
                            }
                        )

class Cleanext(OttoCmd):
    """This will erase all files with a particular extension from this directory and all sub directories.

For example, to clean up all .pyc files run the following:
  $ otto ext_cleanup pyc"""

    def run(self, ext):
        shell(r'find ./ -type f -name "*.%s" -exec rm -f {} \;' % ext)

class Pack(OttoCmd):
    """Turn .otto into a package to be distributed/installed"""

    def run(self, pack_name):
        from shutil import copytree, rmtree
        pack_path = os.path.basename(pack_name + '.opack')
        info("Packing up local commands...")

        # Copy .otto/
        copytree(LOCAL_DIR, pack_name)

        # Tar to .opack file
        shell(r'tar -czf %s %s' % (pack_path, pack_name))

        # Cleanup
        rmtree(pack_name)

class Install(OttoCmd):
    """Install a package as global commands"""

    def run(self, pack_path):
        pack_name = os.path.basename(pack_path).split('.opack')[0]

        # Open global config
        config = open_config(GLOBAL_CONFIG)

        # Add pack
        if 'packs' not in config:
            config['packs'] = []
        config['packs'].append(pack_name)

        # Save global config
        save_config(config, GLOBAL_CONFIG)

        # Untar pack
        shell(r'tar -xzf %s -C %s' % (pack_path, GLOBAL_CMDS_DIR))

class Uninstall(OttoCmd):
    """Interactive prompt to remove installed package"""
    def run(self):
        from shutil import rmtree
        # Get list of installed packages
        config = open_config(GLOBAL_CONFIG)
        if 'packs' in config:
            installed_packs = config['packs']
        else:
            info("No packs installed")
            bail()

        # Ask user which to uninstall
        dialog = Dialog("Which pack do you want to uninstall?")
        dialog.choose(installed_packs)
        info('Uninstalling %s...' % dialog.result)

        # Remove pack
        config['packs'].pop(dialog.index)
        save_config(config, GLOBAL_CONFIG)
        rmtree(os.path.join(GLOBAL_CMDS_DIR, dialog.result))

class gitcheck(OttoCmd):
    """Make sure no '# TODO:'s were left behind before commiting"""
    def run(self):
        import re
        outp = shell(r'git diff --cached').splitlines()
        info('The following lines with todos were found:')
        for line in outp:
            if re.search('#\s*TODO', line):
                if re.search('^[+-]', line):
                    print line

class wait(OttoCmd):
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
