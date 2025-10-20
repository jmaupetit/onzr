In this tutorial, you will learn how to set up Onzr and the basic philosophy
behind it.

!!! tip

    While following this tutorial, you will be invited to type shell commands.
    Every command appears in a code block as follow:

    ```sh
    echo "Hello world!"
    ```

    You can copy or type them in your terminal and type return at the end of
    the instruction to execute them.

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

## Configure Onzr

A basic configuration file is required to run Onzr. It should be created once
using the dedicated `init` command.

!!! Tip

    Before running this command, we invite you to get your **ARL token** that
    will be used to authenticate your requests to the Deezer API. This token
    value can be found stored in a session cookie once connected to
    [deezer.com](https://www.deezer.com) using your favorite web browser (see
    [detailed
    instructions](https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie)).

```sh
onzr init
```

When prompted, copy/paste your ARL token and validate by pressing ++enter++

That's it: Onzr is now configured 🎉 A configuration file (`settings.yaml`)
should have been generated at the following path (depending on your OS):

- **MacOS**: `~/Library/Application Support/onzr/settings.yaml`
- **Windows**: `%appdata%\watson\config`, which usually expands to `C:\Users\<user>\AppData\Roaming\onzr\settings.yaml`
- **Linux**: `~/.config/onzr/settings.yaml`

You can check the configuration path using the `config -p` command:

```sh
onzr config -p
```

And the configuration content using:

```sh
onzr config
```

You should see at least two defined settings:

```yaml
ARL: "your-arl-token"
DEEZER_BLOWFISH_SECRET: "supersecret"
```

!!! Tip "Edit your configuration"

    Feel free to customize Onzr's behavior by changing your settings such as the
    default audio quality:

    ```yaml
    ARL: "your-arl-token"
    DEEZER_BLOWFISH_SECRET: "supersecret"
    QUALITY: "FLAC"
    ```

    Configuration can be edited using the `onzr config -e` command.

For a complete list of configurable settings and configuration tips, please
refer to the [configuration documentation](./configuration.md).

## Run the web server

Onzr has been designed as a web server that streams and plays your music using
FastAPI and VLC respectively. It provides an HTTP API to interact with it,
_e.g._ control the player and the tracks queue.

To use Onzr you should run the web server by using the `serve` command:

```sh
onzr serve
```

If Onzr is properly installed and configured, you should see logs from the web
server displayed in your terminal. And as it's running as a foreground process,
you will need to start a new terminal to run new commands to act on it.

!!! Tip

    If you want to run the Onzr server as a background process, we recommend to
    lower the log-level so that it won't disturb your terminal flow:

    ```sh
    onzr serve --log-level error &
    ```

Make sure Onzr server is running by using the `state` command:

```sh
onzr state
```

If the server is up and running, you should get a description of the server
state. Meaning we can start playing with it and stream our favorite tracks.

## Search albums, artists and tracks

Onzr CLI uses Deezer API to explore available music tracks. When beginning with
Onzr, the first step is often a search. Let's say you want to explore
Radiohead's discography. The first step is to get its artist identifier (ID):

```sh
onzr search --artist Radiohead
```

The command output should look like:

```
              Search results
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        ID ┃ Artist                      ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│       399 │ Radiohead                   │
│ 177930417 │ Mau P                       │
│    171883 │ NTO                         │
│   7888234 │ Kelly Lee Owens             │
│      2762 │ Easy Star All-Stars         │
│  53477202 │ DJ Radiohead                │
│  12189436 │ Radio Head                  │
│ 258886601 │ radiohead two               │
│ 271721572 │ Coldplay, Radiohead, Hozier │
│  14009761 │ Radiohead Tribute Band      │
│   4674537 │ Radiodread                  │
└───────────┴─────────────────────────────┘
```

The identifier we are interested in for Radiohead is `399`. We can then use
this identifier to explore the artist top tracks:

```sh
onzr artist 399
```

The output should look like:

```
                           Artist collection
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃        ID ┃ Track                         ┃ Album        ┃ Artist    ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 138547415 │ Creep                         │ Pablo Honey  │ Radiohead │
│ 138539979 │ Let Down                      │ OK Computer  │ Radiohead │
│ 138539157 │ No Surprises                  │ No Surprises │ Radiohead │
│ 138539981 │ Karma Police                  │ OK Computer  │ Radiohead │
│ 138539977 │ Exit Music (For A Film)       │ OK Computer  │ Radiohead │
│ 138547587 │ Everything In Its Right Place │ Kid A        │ Radiohead │
│ 138546819 │ Jigsaw Falling Into Place     │ In Rainbows  │ Radiohead │
│ 138539973 │ Paranoid Android              │ OK Computer  │ Radiohead │
│ 138546811 │ All I Need                    │ In Rainbows  │ Radiohead │
│ 138546809 │ Weird Fishes / Arpeggi        │ In Rainbows  │ Radiohead │
└───────────┴───────────────────────────────┴──────────────┴───────────┘
```

In this top track list, we can find the track identifiers, title and album.

!!! Tip "Pro tip for power users ™"

    An alternative way to achieve the previous suite of commands is to leverage the
    power of UNIX shells by using the pipe operator (`|` character) that send the
    output of a command as input of another command (we say it is "piped" to the
    second command):

    ```sh
    onzr search --artist Radiohead --ids | # (1) \
        head -n 1 | # (2) \
        onzr artist - # (3)
    ```

    1. Only display identifiers using the `--ids` option
    2. Restrict to the first match using `head` command
    3. Use the `-` special flag so that Onzr expects identifiers coming from the standard input

And if we want the artist discography, we can use the `--albums` option:

```sh
onzr artist --albums --limit 100 399 # (1)
```

1. The `--limit` option is used here to avoid being limited to the 10 latest
   albums (API default page size it `10`).

The output should look like:

```
                                  Artist collection
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃        ID ┃ Album                                         ┃ Artist    ┃ Released   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 792320571 │ Hail to the Thief (Live Recordings 2003-2009) │ Radiohead │ 2025-08-13 │
│ 265569082 │ KID A MNESIA                                  │ Radiohead │ 2021-11-05 │
│  14879823 │ A Moon Shaped Pool                            │ Radiohead │ 2016-05-09 │
│  14880501 │ TKOL RMX 1234567                              │ Radiohead │ 2011-10-10 │
│  14880315 │ The King Of Limbs                             │ Radiohead │ 2011-02-18 │
│  14880659 │ In Rainbows                                   │ Radiohead │ 2007-12-28 │
│  14879789 │ Com Lag: 2+2=5                                │ Radiohead │ 2004-03-24 │
│  14879739 │ Hail To the Thief                             │ Radiohead │ 2003-06-09 │
│  14879753 │ I Might Be Wrong                              │ Radiohead │ 2001-11-12 │
│  14879749 │ Amnesiac                                      │ Radiohead │ 2001-03-12 │
│  ...      │ ...                                           │ ...       │ ...        │
│  14880711 │ Pablo Honey                                   │ Radiohead │ 1993-02-22 │
│  14880307 │ Anyone Can Play Guitar                        │ Radiohead │ 1993-01-25 │
│  14880783 │ Creep                                         │ Radiohead │ 1992-09-21 │
│ 423524437 │ Creep EP                                      │ Radiohead │ 1992-09-21 │
│ 121893052 │ Drill EP                                      │ Radiohead │ 1992-05-05 │
└───────────┴───────────────────────────────────────────────┴───────────┴────────────┘
```

I hear you from here saying:

> — Ok that great, but we are here to listen to music, not get creepy identifiers!

Loud and clear, let's continue to the next section to listen good music!

## Add tracks to queue

Onzr queue should be considered as a volatile playlist that you can modify
on-the-fly. You may add tracks to the queue using the `add` command:

```sh
onzr add 138539157
```

In this case, we've added the track with the `138539157` identifier to the
queue. Since you may not remember Deezer identifier from your favorite tracks,
the `add` command is often the last command of a more complete pipeline,
_e.g._:

```sh
onzr search --artist "Radiohead" --ids | # (1) \
    head -n 1 | \
    onzr artist --top --ids - | # (2) \
    onzr add - # (3)
```

1. Note that we use the `--ids` option to only display artists identifiers
2. Note that we use the `--ids` option to only display tracks identifiers
3. Note that the `add` command also accepts the `-` special operator to read
   identifiers from the standard input (`stdint`)

In this case, we will add Radiohead's top-10 tracks to the queue. This is a
classical pipeline.

!!! Tip

    If you want a fresh start and remove all queued tracks, use the `clear`
    command:

    ```sh
    onzr clear
    ```

    Note that this will also stop the player.

## Enjoy your music

Once you filled Onzr's queue, you can start playing it!

```sh
onzr play
```

By default, if the queue has just been filled and left untouched, the `play`
command will start playing the first track. If the player is paused, it will
resume playing.

If you prefer playing a particular queued track, you can also start playing
from its rank in the queue. To get the list of queued tracks, you can use the
`queue` command, get the rank of your favorite track and then play it:

```sh
onzr queue
```

The output should look like:

```
                           Queued tracks
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Rank ┃ Track                         ┃ Album        ┃ Artist    ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│    1 │ Creep                         │ Pablo Honey  │ Radiohead │
│    2 │ No Surprises                  │ No Surprises │ Radiohead │
│    3 │ Let Down                      │ OK Computer  │ Radiohead │
│    4 │ Karma Police                  │ OK Computer  │ Radiohead │
│    5 │ Everything In Its Right Place │ Kid A        │ Radiohead │
│    6 │ Exit Music (For A Film)       │ OK Computer  │ Radiohead │
│    7 │ Jigsaw Falling Into Place     │ In Rainbows  │ Radiohead │
│    8 │ All I Need                    │ In Rainbows  │ Radiohead │
│    9 │ Weird Fishes / Arpeggi        │ In Rainbows  │ Radiohead │
│   10 │ Paranoid Android              │ OK Computer  │ Radiohead │
└──────┴───────────────────────────────┴──────────────┴───────────┘
```

If you want to start playing _Jigsaw Falling Into Place_ use its rank:

```sh
onzr play --rank 7
```

## Control the player

As you may expect, there are few commands that do what they say to control the
player:

- `pause`: toggle pause
- `next`: play next track in queue
- `previous`: play previous track in queue
- `stop`: stop the player without clearing the queue

!!! Tip

    If you want to follow currenly played tracks in real-time you may use the
    `now` command:

    ```sh
    onzr now -f
    ```

## Create playlists on-the-fly

One last thing: the `mix` command is Onzr's secret sauce! This command can
create playlists on the fly given a list of artists names. Let's see it in
action:

```sh
onzr mix "avishai cohen" "go go penguin" "yom" --limit 20 --ids | # (1) \
    shuf | # (2) \
    shuf | \
    onzr add -
```

1. Note that we use quotes for each artist (since they may have spaces or
   special characters in their names)
2. The `shuf` command shuffles standard input lines

With this command we add 60 tracks to the queue (20 tracks per artist) in a
random order. By default, we consider the `--limit` first artist's top-tracks
(defaults to 10).

So if you want to go deeper and discover artists inspired from the ones you
choose, use the `--deep` option to get tracks from each artist's radio. There
is a great chance that you discover new sounds:

```sh
onzr mix --deep "avishai cohen" "go go penguin" "yom" --limit 20 --ids | \
    shuf | \
    shuf | \
    onzr add -
```

!!! Tip

    The cool thing about this `mix --deep` command is that if you run it twice,
    you won't have the same mix, since artist's radio are randomly created.
