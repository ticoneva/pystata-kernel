import argparse
import json
import os
import sys

from jupyter_client.kernelspec import KernelSpecManager
from IPython.utils.tempdir import TemporaryDirectory
from pkg_resources import resource_filename
from shutil import copyfile
from pathlib import Path
from textwrap import dedent

kernel_json = {
    "argv": [sys.executable, "-m", "pystata-kernel", "-f", "{connection_file}"],
    "display_name": "Stata",
    "language": "stata",
}

def install_my_kernel_spec(user=True, prefix=None):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755) # Starts off as 700, not user readable
        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, sort_keys=True)

        # Copy logo to tempdir to be installed with kernelspec
        logo_path = resource_filename('pystata-kernel', 'logo-64x64.png')
        copyfile(logo_path, os.path.join(td, 'logo-64x64.png'))

        print('Installing Jupyter kernel spec')
        KernelSpecManager().install_kernel_spec(td, 'pystata', user=user, replace=True, prefix=prefix)

def install_conf(conf_file):
    """
    From stata_kernel, but the conf here is much simplier.
    """

    # By avoiding an import of .utils until we need it, we can
    # complete the installation process in virtual environments
    # without needing this submodule nor its downstream imports.
    from .utils import find_path
    stata_dir = os.path.dirname(find_path())
    if not stata_dir:
        msg = """\
            WARNING: Could not find Stata path.
            Please specify it manually in configuration file: 
            """
        print(dedent(msg),str(conf_file))
    
    conf_default = dedent(
        """\
    [pystata-kernel]
    # Directory containing stata executable.
    stata_dir = {}
    edition = mp
    """.format(stata_dir))

    with conf_file.open('w') as f:
        f.write(conf_default)

def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False # assume not an admin on non-Unix platforms

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', action='store_true',
        help="Install to the per-user kernels registry. Default if not root.")
    ap.add_argument('--sys-prefix', action='store_true',
        help="Install to sys.prefix (e.g. a virtualenv or conda env)")
    ap.add_argument('--prefix',
        help="Install to the given prefix. "
             "Kernelspec will be installed in {PREFIX}/share/jupyter/kernels/")
    ap.add_argument(
        '--no-conf-file', action='store_true',
        help="Skip the creation of a default user configuration file.")             
    args = ap.parse_args(argv)

    if args.sys_prefix:
        args.prefix = sys.prefix
    if not args.prefix and not _is_root():
        args.user = True

    install_my_kernel_spec(user=args.user, prefix=args.prefix)
    if not args.no_conf_file:
        if args.user:
            conf_file = Path('~/.pystata-kernel.conf').expanduser()
        else:
            conf_dir = os.path.join(args.prefix,'etc')
            if not Path(os.path.join(args.prefix,'etc')).is_dir():
                os.mkdir(conf_dir)
            conf_file = Path(os.path.join(conf_dir,'pystata-kernel.conf'))
        if not conf_file.is_file():
            install_conf(conf_file)

if __name__ == '__main__':
    main()
