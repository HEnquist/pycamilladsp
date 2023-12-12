# Installation instructions
As the name suggests, pyCamillaDSP is a Python library. It is installed using the `pip` package manager.


## Dependencies

pyCamillaDSP only requires the `websocket-client` library.
The package is named slightly differently in different distributions:

| Distribution       | Package name             |
|--------------------|--------------------------|
| Fedora             | python3-websocket-client |
| Debian/Raspbian    | python3-websocket        |
| Arch               | python-websocket-client  |
| pypi.org (pip)     | websocket_client         |
| conda              | websocket_client         |


## About Python environments

In all cases it is recommended to create an isolated Python environment.
This ensures that the installation of the CamillaDSP libraries does not interfere with
the environment managed by the system package manager.
This is mainly an issue on Linux, where the default Python environment is managed by
the system package manager (for example `apt` on Debian and `dnf` on Fedora).
Letting pip install packages into this environment is not recommended
and may corrupt the system.
Recent versions of pip will refuse to do this unless started with the flag `--break-system-packages`.

There are several tools to set up Python environments.
For the sake of simplicity, this readme only deals with [conda](#conda) and [venv](#venv).


### conda

The `conda` package manager is used in the popular Anaconda Python distribution.
It's possible to use the full Anaconda package, but it includes much more than needed.
Instead it's recommended to use the Miniconda package.

Download Miniconda from https://docs.conda.io/en/latest/miniconda.html

Alternatively use Miniforge from https://github.com/conda-forge/miniforge

Conda creates a default `base` environment, but don't install any packages there.
It's better to create a specific environment.

To do that open a terminal and type:
```console
conda create --name camilladsp
```

Before an environment can be used, either for install packages into it,
or for running some application, it must be activated.

The command for that is: 

```console
> conda activate camilladsp
```

Now install the websocket-client library:

```console
> conda install websocket_client
```

Finally install pyCamillaDSP with pip, see [Installing](#installing)).


### venv

The standard Python library includes the `venv` tool that is used to create virtual Python environments.
This allows installing packages using pip separately, and prevents any issues from conflicts with the system package manager.
By default, all packages installed in the system environment are also available in the virtual environment.
See https://docs.python.org/3/library/venv.html for more details.

Create a new venv, located in `camilladsp/.venv` in the user home directory:

```console
> python -m venv ~/camilladsp/.venv
```

Activate the new environment:

- Linux & MacOS
  ```console
  > source ~/camilladsp/.venv/bin/activate
  ```

- Windows

  cmd.exe:
  ```console
  > %USERPROFILE%\camilladsp\.venv\Scripts\activate.bat
  ```

  PowerShell:
  ```console
  > $env:userprofile\camilladsp\.venv\Scripts\Activate.ps1
  ```

Finally install pyCamillaDSP with pip, see [Installing](#installing)).

Once the environment is ready, it's possible to use it without first activating.
This is done by simply using the python interpreter of the environment:

```console
> ~/camilladsp/.venv/bin/python some_script.py
```


## Recommendations for different operating systems

The way to set up a Python environment and install pyCamillaDSP depends on what operating system is used.
Linux normally comes with Python preinstalled, while Windows does not.
MacOS is somewhere in between in that it comes with a limited Python installation.

### Linux
Most linux distributions have the required Python 3.6 or newer installed by default.
Use the normal package manager to install python if required,
and then create a [virtual environment](#venv) for pyCamillaDSP.

It is also possible to use [Conda](#conda).

### Windows
Use Anaconda, miniconda, or miniforge. See [Conda](#conda).

### macOS
On macOS use either [conda](#conda), or Homebrew optionally with a [virtual environment](#venv). 

For Homebrew, install Python with `brew install python`, after which you can install the needed packages with pip, `pip3 install websocket_client`.

## Installing
Once a suitable environment has been set up, use `pip` to install pyCamillaDSP.

The `pip` package manager is normally installed by default together with Python.
The command is usually `pip`, but on some systems it's instead `pip3`.

### Directly from Github
The easiest way to install is to let pip fetch the files directly from Github.

The command for that is:
```console
pip install git+https://github.com/HEnquist/pycamilladsp.git
```
This installs the current version in the default branch `master`.

To install from another branch, or a tagged version, add `@` and the branch or tag name at the end.

To install the version tagged with `v2.0.0`, the command is:
```console
pip install git+https://github.com/HEnquist/pycamilladsp.git@v2.0.0
```

### Install from downloaded files
Download the library, either by `git clone` or by downloading a zip file of the code.
Then unpack the files, go to the folder containing the `setup.py` file and run: 
```console
pip install .
```



