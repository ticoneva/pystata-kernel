'''
pystata-kernel
Version: 0.2.5
A simple Jupyter kernel based on pystata.
Requires Stata 17 and stata_setup.
'''

from ipykernel.ipkernel import IPythonKernel
from .config import get_config
import os
import sys
from packaging import version

class PyStataKernel(IPythonKernel):
    implementation = 'pystata-kernel'
    implementation_version = '0.2.5'
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
        self.noecho = False
        self.quietly = False
        self.magic_handler = None
        self.env = None

    def launch_stata(self, path, edition, splash=True):
        """
        We modify stata_setup to make splash screen optional
        """
        if not os.path.isdir(path):
            raise OSError(path + ' is invalid')

        if not os.path.isdir(os.path.join(path, 'utilities')):
            raise OSError(path + " is not Stata's installation path")

        sys.path.append(os.path.join(path, 'utilities'))
        import pystata
        if version.parse(pystata.__version__) >= version.parse("0.1.1"):
            # Splash message control is a new feature of pystata-0.1.1
            pystata.config.init(edition,splash=splash)
        else:
            pystata.config.init(edition)

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):

        # Launch Stata if it has not been launched yet
        if not self.stata_ready:
            env = self.env = get_config()
            self.launch_stata(env['stata_dir'],env['edition'],
                    False if env['splash']=='False' else True)

            # This can only be imported after locating Stata
            import pystata
            
            if env['echo'] not in ('True','False','None'):
                raise OSError("'" + env['echo'] + "' is not an acceptable value for 'echo'.")

            # Set graph format
            if env['graph_format'] == 'pystata':
                pass
            else:
                from pystata.config import set_graph_format
                set_graph_format(env['graph_format'])

            # Magics
            from .magics import StataMagics
            self.magic_handler = StataMagics()

            self.stata_ready = True

        # Read settings from env dict every time so that these can be modified by magics 
        # for each cell.
        if self.env['echo'] == 'None':
            self.noecho = True
            self.echo = False
        elif self.env['echo'] == 'True':
            self.noecho = False
            self.echo = True
        else:
            self.noecho = False
            self.echo = False
        self.quietly = False
        
        # Process magics
        code = self.magic_handler.magic(code,self)              
        
	# Execute Stata code after magics
        if code != '':
            # Supress echo?
            if self.noecho and not self.quietly:
                from .helpers import noecho_run
                noecho_run(code)
            else:
                from pystata.stata import run
                run(code, quietly=self.quietly, inline=True, echo=self.echo)

        self.shell.execution_count += 1

        return {'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
            }
