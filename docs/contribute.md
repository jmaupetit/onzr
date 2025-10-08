## Install dependencies

Contributing to Onzr requires the following dependencies to be installed:

- [GNU Make](https://www.gnu.org/software/make/)
- [`uv`](https://docs.astral.sh/uv/)
- [VLC](https://www.videolan.org/vlc/)

!!! Note

    Depending on your operating system, use your favorite package manager
    (`brew`, `apt`, `pacman`, ...) to install them!

## Bootstrap the project

To quickly start contributing to this project, we've got you covered! Once
you've forked/cloned the project, use GNU Make to ease your life:

```sh
# Clone the forked project somewhere on your system
git clone git@github.com:my_username/onzr.git

# Enter the project's root directory
cd onzr

# Prepare your working environment
make bootstrap
```

You can now start the development server:

```sh
make run
```

Test Onzr development server in a new terminal as the server is still running
in the previous one:

```sh
uv run onzr artist 1 --top --ids | \
  uv run onzr add - && \
  uv run onzr play
```

!!! Question "Musical quiz"

    Enjoying what you ear? What is the artist who was given the ID `1`?

## Quality checks

You can run tests and linters using dedicated GNU Make rules:

```sh
# Run the tests suite
make test

# Linters!
make lint
```

!!! tip

    💡 Don't be surprised to ear strange noises during tests execution 😅

Happy hacking 😻
