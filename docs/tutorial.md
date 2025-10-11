In this tutorial, you will learn how to set up Onzr and the basic philosophy
behind it.

## Install Onzr

### Requirements

Onzr is a Python package, but it depends on [VLC media
player](https://www.videolan.org/vlc/) to play your music. You need to make
sure it's installed on your machine; don't be afraid most (every?) operating
systems are compatible.

[Python](https://www.python.org) should also be installed in your machine. If
you are using a UNIX-based operating system such as MacOS or GNU/Linux, it
should already be installed. Make sure your version of python is at least
Python `11.0` by typing the following command in your favorite terminal:

```sh
python --version
```

Example output may be something like: `Python 3.12.8`

### Install Onzr in your user space

!!! tip

    Make sure `pip` is installed for your Python version by typing the following
    command in a terminal:

    ```sh
    pip --version
    ```

    This command should not fail and the output may look like:

    ```
    pip 25.1.1 from /home/julien/.local/lib/python3.12/site-packages/pip (python 3.12)
    ```

    If `pip` is not installed, please follow the [official
    documentation](https://pip.pypa.io/en/stable/installation/) to install it.

We will use the `pip` package manager to install `onzr` in your user space:

```sh
pip install --user onzr
```

!!! info "Use your preferred installation method"

    In this tutorial, we invite you to install Onzr in your user space, but
    you can choose to install it globally (for all users), or using another package
    manager than Pip. It's up to you to choose the most convenient method to install
    a Python package in your machine.

Once installed, the `onzr` command can be called from your favorite terminal.
You can test it by typing:

```sh
onzr --help
```
