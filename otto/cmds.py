from otto.utils import *
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
            path = cmd_name + '.py'

            config = open_config()

            # Add local_cmds section to config
            if 'local_cmds' not in config:
                config['local_cmds'] = {}
            config['local_cmds'][cmd_name] = path

            save_config(config)

            with open(os.path.join(OTTO_DIR, path), 'w') as cmd_file:
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

            config = open_config()

            # Split up args
            args_split = [z.split(':') for z in cmd_args if z.count(':') == 1]

            # Turn into dict
            args_d = dict(args_split)

            config[cmd_name] = args_d

            save_config(config)

class Cleanext(OttoCmd):
    """This will erase all files with a particular extension from this directory and all sub directories.

For example, to clean up all .pyc files run the following:
  $ otto ext_cleanup pyc"""

    def run(self, ext):
        shell(r'find ./ -type f -name "*.%s" -exec rm -f {} \;' % ext)

DEFAULT_CMDS = {z._name(): z for z in OttoCmd.__subclasses__()}
