# Onzr, the one-hour-late Deezer 💜 CLI.

> Pronounced onze heure (11 O-Clock à-la-française) 🤡

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jmaupetit/onzr/quality.yml)
![PyPI - Version](https://img.shields.io/pypi/v/onzr)

!!! warning

    This project is still at an early stage. It works in its core parts, but
    will not meet standard requirements for a decent player.

## Requirements

- [Python](https://www.python.org): 3.11+
- [VLC](https://www.videolan.org/vlc/index.en_GB.html): we use VLC bindings to
  play tracks, so this is a strict requirement.

## Quick start guide

Onzr is a python package, it can be installed using Pip (or any other package
manager you may use):

```sh
pip install --user onzr
```

Once installed the `onzr` command should be available (if not check your `PATH`
definition). Before using Onzr, you should configure it (once for all):

```sh
onzr init
```

This command will prompt for an `ARL` token. If you don't know how to find it,
please follow
[this guide](https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie).

You may now explore commands and their usage:

```sh
onzr --help
```

Onzr is based on an HTTP client/server architecture, hence, once installed, you
should run the server before starting to use it:

```sh
onzr serve --log-level error &
```

In this case, the server is ran as a background job; see the `serve` command
documentation for details about running Onzr server.

Play your first album:

```sh
onzr search --artist "Billie Eilish" --ids --first | \
    onzr artist --albums --ids --limit 1 - | \
    onzr album --ids - | \
    onzr add - && \
    onzr play
```

Aaand, tada 🎉

In this command, we look for the latest Billie Eilish album, add it to the
queue and play it instantly!

## Documentation

The complete documentation of the project is available at:
[https://jmaupetit.github.io/onzr/](https://jmaupetit.github.io/onzr/)

## License

This work is released under the MIT License.
