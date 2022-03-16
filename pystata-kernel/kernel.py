'''
pystata-kernel
Version: 0.1.5
A simple Jupyter kernel based on pystata.
Requires Stata 17 and stata_setup.
'''

from ipykernel.ipkernel import IPythonKernel
import stata_setup
from .config import get_config

class PyStataKernel(IPythonKernel):
    implementation = 'pystata-kernel'
    implementation_version = '0.1.5'
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

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):

        # Launch Stata if it has not been launched yet
        if not self.stata_ready:
            env = get_config()
            stata_setup.config(env['stata_dir'],env['edition'])
            self.stata_ready = True
        
        # Execute Stata code
        from pystata import stata as _stata
        _stata.run(code, quietly=False, inline=True)

        return {'status': 'ok',
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
            }