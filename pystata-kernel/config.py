import os
import sys
from pathlib import Path
from configparser import ConfigParser, NoSectionError

def get_config():
    global_config_path = Path(os.path.join(sys.prefix,'etc','pystata-kernel.conf'))
    user_config_path = Path('~/python/pystata-kernel.conf').expanduser()

    env = {'stata_dir': '/opt/stata', 'edition': 'se'}

    try:
        if user_config_path.is_file():
            config = ConfigParser()
            config.read(str(user_config_path))
        else:
            config = ConfigParser()
            config.read(str(global_config_path))

        env.update(dict(config.items('pystata-kernel')))
    except:
        pass

    return env