import os
import os.path

# Config file names
ROOT_FILE = 'config.json'
CMDS_FILE = 'cmds.json'

# Global paths
GLOBAL_DIR = os.path.expanduser('~/.otto')
GLOBAL_CONFIG = os.path.join(GLOBAL_DIR, ROOT_FILE)

# Local paths
LOCAL_DIR = os.path.join(os.getcwd(), '.otto')
LOCAL_CONFIG = os.path.join(LOCAL_DIR, ROOT_FILE)
LOCAL_CMDS_DIR = os.path.join(LOCAL_DIR, 'local')

# Other constants
PACK_EXT = '.opack'
OTTO_VERSION = 'v0.6'
OTTO_DESC = "A workflow automator written in Python."

