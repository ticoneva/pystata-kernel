# pystata-kernel

A simple Jupyter kernel for Stata based on [pystata](https://www.stata.com/python/pystata/). Requires Stata 17 or above.
Consider [stata_kernel](https://github.com/kylebarron/stata_kernel) instead if you have an older version of Stata. 

### Installation
To install `pystata-kernel`:

```python
pip install pystata-kernel
python -m pystata-kernel.install [--sys-prefix] [--prefix]
```

Include `--sys-prefix` if you are installing `pystata-kernel` in a multi-user environment,
or `--prefix` if you want to specify a path yourself.

The installation script will try to determine the location of your Stata installation
and write it to a configuration file. 
You can manually modify this file if the installation script fails to detect your
stata installation. 
The configuration file is saved under:

- `[prefix]/etc/pykernel-stata.conf` if `--sys-prefix` or `--prefix` is specified.
-  `~/.pykernel-stata.conf` otherwise.

If a configuration file exists in both locations, the user version takes precedent. 

Syntax highlighting is the same as `stata_kernel`:

```sh
conda install nodejs -c conda-forge --repodata-fn=repodata.json
jupyter labextension install jupyterlab-stata-highlight
```
