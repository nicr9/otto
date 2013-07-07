import os
import os.path

# Paths
GLOBAL_CMDS_DIR = os.path.expanduser('~/.otto')
GLOBAL_CONFIG = os.path.join(GLOBAL_CMDS_DIR, 'config.json')
LOCAL_CMDS_DIR = os.path.join(os.getcwd(), '.otto')
LOCAL_CONFIG = os.path.join(LOCAL_CMDS_DIR, 'config.json')
