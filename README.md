# pystata-kernel

A simple Jupyter kernel for Stata based on [pystata](https://www.stata.com/python/pystata/). 
Requires Stata 17 or above.
Consider [stata_kernel](https://github.com/kylebarron/stata_kernel) instead if you have an 
older version of Stata. 

### Installation
To install `pystata-kernel`:

```python
pip install pystata-kernel
python -m pystata-kernel.install [--sys-prefix] [--prefix] [--conf-file]
```

Include `--sys-prefix` if you are installing `pystata-kernel` in a multi-user environment,
or `--prefix` if you want to specify a path yourself.

The kernel will try to determine the location of your Stata installation at startup. 
You can create a configuration file to preempt this detection with the `--conf-file` option.
Even if you do not include this option, the configuration file will still be created if the 
installer cannot find any Stata installation.

The location of the configuration file is:

- `[prefix]/etc/pykernel-stata.conf` if `--sys-prefix` or `--prefix` is specified.
-  `~/.pykernel-stata.conf` otherwise.

If a configuration file exists in both locations, the user version takes precedent. 

Syntax highlighting is the same as `stata_kernel`:

```sh
conda install nodejs -c conda-forge --repodata-fn=repodata.json
jupyter labextension install jupyterlab-stata-highlight
```
