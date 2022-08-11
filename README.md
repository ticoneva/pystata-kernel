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

- `[prefix]/etc/pystata-kernel.conf` if `--sys-prefix` or `--prefix` is specified.
-  `~/.pystata-kernel.conf` otherwise.

If a configuration file exists in both locations, the user version takes precedent. 

Syntax highlighting is the same as `stata_kernel`:

```sh
conda install nodejs -c conda-forge --repodata-fn=repodata.json
jupyter labextension install jupyterlab-stata-highlight
```

### Configuration

The following settings are permitted inside the configuration file:

- `stata_dir`: Stata installation directory.
- `edition`: Stata edition. Acceptable values are 'be', 'se' and 'mp'.
    Default is 'be'.
- `graph_format`: Graph format. Acceptable values are 'png', 'pdf', 'svg' and 'pystata'.
    Specify the last option if you want to use `pystata`'s setting. Default is 'png'. 
- `echo`: If set to 'True', the kernel will echo the command while running a cell with only
    a single command. This setting has no effect on cells containing multiple commands.
    Default is 'False'.

Settings must be under the title `[pystata-kernel]`. Example:

```
[pystata-kernel]
stata_dir = /opt/stata
edition = mp
graph_format = svg
echo = True
```

### Default Graph Format

Both `pystata` and `stata_kernel` default to the SVG image format. 
`pystata-kernel` defaults to the PNG image format instead for several reasons:

- Jupyter does not show SVG images from untrusted notebooks ([link 1](https://stackoverflow.com/questions/68398033/svg-figures-hidden-in-jupyterlab-after-some-time)).
- Notebooks with empty cells are untrusted ([link 2](https://github.com/jupyterlab/jupyterlab/issues/9765)).
- SVG images cannot be copied and pasted directly into Word or PowerPoint.

These issues make the SVG format unsuitable for use in a pedagogical setting, 
which is my primary use of a Jupyter kernel for Stata. 
