import os
import sys
from pathlib import Path
from configparser import ConfigParser, NoSectionError
from .utils import find_dir_edition

def get_config():
    global_config_path = Path(os.path.join(sys.prefix,'etc','pystata-kernel.conf'))
    user_config_path = Path('~/.pystata-kernel.conf').expanduser()

    stata_dir,stata_ed = find_dir_edition()
        
    env = {'stata_dir': stata_dir, 'edition': stata_ed}

    for cpath in (global_config_path,user_config_path):
        try:
            if cpath.is_file():
                config = ConfigParser()
                config.read(str(cpath))
            env.update(dict(config.items('pystata-kernel')))
        except:
            pass

    return env