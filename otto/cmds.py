from otto.utils import OttoCmd, OTTO_DIR, OTTO_CONFIG
import os
import os.path
import json

class New(OttoCmd):
    cmd_template = """import otto.utils as otto

class %s(otto.OttoCmd):
    def run(self, %s):
        pass
"""

    def run(self, *args):
        cmd_name = args[0]
        cmd_args = args[1:]
        if cmd_name is None:
            self.cmd_usage(['new_command_name', '[cmd_arg_1 ...]'])
        else:
            path = cmd_name + '.py'

            # Ensure .otto/ exists
            if not os.path.isdir(OTTO_DIR):
                os.mkdir(OTTO_DIR)

            # Try opening current config
            config = {}
            if os.path.isfile(OTTO_CONFIG):
                with open(OTTO_CONFIG, 'r') as j:
                    config = json.load(j)

            # Add local_cmds section to config
            if 'local_cmds' not in config:
                config['local_cmds'] = {}
            config['local_cmds'][cmd_name] = path

            # TODO: Add section with kwargs for cmd to config

            # Save
            with open(OTTO_CONFIG, 'w') as j:
                json.dump(config, j, indent=4)

            # TODO: Create arg_list for cmd_template

            with open(os.path.join(OTTO_DIR, path), 'w') as cmd_file:
                cmd_file.write(
                        self.cmd_template % (
                                cmd_name.capitalize(),
                                ', '.join(cmd_args)
                                )
                        )

DEFAULT_CMDS = {z._name(): z for z in OttoCmd.__subclasses__()}
