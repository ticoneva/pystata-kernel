'''
pystata-kernel
Version: 0.1.19
A simple Jupyter kernel based on pystata.
Requires Stata 17 and stata_setup.
'''

from ipykernel.ipkernel import IPythonKernel
from .config import get_config
import os
import sys

class PyStataKernel(IPythonKernel):
    implementation = 'pystata-kernel'
    implementation_version = '0.1.19'
    language = 'stata'
    language_version = '17'
    language_info = {
        'name': 'stata',
        'mimetype': 'text/x-stata',
		'codemirror_mode': 'stata',
        'file_extension': '.do',
    }
    banner = "pystata-kernel: a Jupyter kernel for Stata based on pystata"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stata_ready = False
        self.shell.execution_count = 0
        self.echo = False
        self.suppress = False

    def launch_stata(self, path, edition, splash=True):
        """
        We modify stata_setup to make splash screen optional
        """
        if not os.path.isdir(path):
            raise OSError(path + ' is invalid')

        if not os.path.isdir(os.path.join(path, 'utilities')):
            raise OSError(path + " is not Stata's installation path")

        sys.path.append(os.path.join(path, 'utilities'))
        from pystata import config
        config.init(edition,splash=splash)

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):

        # Launch Stata if it has not been launched yet
        if not self.stata_ready:
            env = get_config()
            self.launch_stata(env['stata_dir'],env['edition'],
                    False if env['splash']=='False' else True)

            # pystata must be loaded after stata_setup
            from pystata.config import set_graph_format 

            # Set graph format
            if env['graph_format'] == 'pystata':
                pass
            else:
                set_graph_format(env['graph_format'])

            if env['echo'] not in ('True','False','None'):
                raise OSError("'" + env['echo'] + "' is not an acceptable value for 'echo'.")
            else:
                if env['echo'] == 'None':
                    self.suppress = True
                elif env['echo'] == 'True':
                    self.echo = True

            self.stata_ready = True
        
        # Execute Stata code
        from pystata.stata import run
        
        if self.suppress == True:        
            code = "noisily: " + code.replace("\n","\nnoisily: ") 
        run(code, quietly=self.suppress, inline=True, echo=self.echo)
        self.shell.execution_count += 1

        return {'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
            }
