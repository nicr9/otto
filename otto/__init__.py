from os import getcwd
from os.path import join as path_join
from os.path import expanduser

# Misc constants
OTTO_VERSION = 'v0.7'
OTTO_DESC = "A workflow automator written in Python."
LOCAL_PACK = 'local'

# File names and extensions
PACK_EXT = '.opack'
ROOT_FILE = 'config.json'
CMDS_FILE = 'cmds.json'

# Global paths
GLOBAL_DIR = expanduser('~/.otto')
GLOBAL_CONFIG = path_join(GLOBAL_DIR, ROOT_FILE)

# Local paths
LOCAL_DIR = path_join(getcwd(), '.otto')
LOCAL_CONFIG = path_join(LOCAL_DIR, ROOT_FILE)
LOCAL_CMDS_DIR = path_join(LOCAL_DIR, LOCAL_PACK)
LOCAL_RES_DIR = path_join(LOCAL_DIR, 'res/')
