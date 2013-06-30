from otto.utils import *
import os
import os.path

class New(OttoCmd):
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

DEFAULT_CMDS = {z._name(): z for z in OttoCmd.__subclasses__()}
