import os
import os.path

# Global paths
GLOBAL_DIR = os.path.expanduser('~/.otto')
GLOBAL_CONFIG = os.path.join(GLOBAL_DIR, 'config.json')

# Local paths
LOCAL_DIR = os.path.join(os.getcwd(), '.otto')
LOCAL_CONFIG = os.path.join(LOCAL_DIR, 'config.json')
LOCAL_CMDS_DIR = os.path.join(LOCAL_DIR, 'local')
