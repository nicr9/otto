import os
import os.path

# Misc constants
OTTO_VERSION = 'v0.7'
OTTO_DESC = "A workflow automator written in Python."
LOCAL_PACK = 'local'

# File names and extensions
PACK_EXT = '.opack'
ROOT_FILE = 'config.json'
CMDS_FILE = 'cmds.json'

# Global paths
GLOBAL_DIR = os.path.expanduser('~/.otto')
GLOBAL_CONFIG = os.path.join(GLOBAL_DIR, ROOT_FILE)

# Local paths
LOCAL_DIR = os.path.join(os.getcwd(), '.otto')
LOCAL_CONFIG = os.path.join(LOCAL_DIR, ROOT_FILE)
LOCAL_CMDS_DIR = os.path.join(LOCAL_DIR, LOCAL_PACK)
