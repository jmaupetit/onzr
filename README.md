# Onzr

The one-hour-late Deezer 💜 CLI.

> ⚠️ This project is a work in progress. It works in its core parts, but will
> not meet standard requirements for a decent player.

## Requirements

- [VLC](https://www.videolan.org/vlc/index.en_GB.html): we use VLC bindings to
  play tracks, so this is a strict requirement.

## Quick start guide

Onzr is a python package, it can be installed using Pip (or any other package
manager you may use):

```sh
$ pip install --user onzr
```

Once installed the `onzr` command should be available (if not check your `PATH`
definition). Before using Onzr, you should configure it (once for all):

```sh
$ onzr init
```

This command will prompt for an `ARL` token. If you don't know how to find it,
please follow
[this guide](https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie).

You may now explore commands and their usage:

```sh
$ onzr --help
```

## Commands

Remember that Onzr is a CLI (Command Line Interface) and that we love UNIX. That
being said, you won't be surprised to pipe Onzr commands to achieve what you
want.

```sh
$ onzr search --artist "Lady Gaga" --ids | \
    head -n 1 | \
    onzr artist --top --limit 20 --ids - | \
    onzr play --quality MP3_320 -
```

> In this example, we will be playing Lady Gaga's top 20 most listened tracks in
> MP3 high quality.

### `search`

Onzr works extensively using Deezer's identifiers (IDs) for artists, albums and
tracks. As you may not know them (yet?), you can start exploring Deezer using
the `search` command:

```sh
$ onzr search --help
```

You can search by artist, album or track using the corresponding flag, _e.g._ if
you are looking for Lady Gaga:

```sh
$ onzr search --artist "Lady Gaga"
```

The command output looks like:

```
              Search results
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        ID ┃ Artist                     ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│     75491 │ Lady Gaga                  │
│      6182 │ Lady                       │
│   7735426 │ Bradley Cooper             │
│       ... │ ...                        │
└───────────┴────────────────────────────┘
```

Use the `--ids` flag to only print identifiers to the standard output if your
intent is to pipe your search result to another command (e.g. `artist` or
`play`).

```sh
$ onzr search --artist "Lady Gaga" --ids | \
    head -n 1 | \
    onzr artist -
```

> 💡 The `-` argument of the `artist` command indicates to read artist ID from
> `stdin`.

Your search result piped to the artist command display the artist top tracks:

```
                                                    Artist tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┓
┃         ID ┃ Track                       ┃        ID ┃ Album                                   ┃    ID ┃ Artist    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━┩
│ 2947516331 │ Die With A Smile            │ 629506181 │ Die With A Smile                        │ 75491 │ Lady Gaga │
│ 3214169391 │ Abracadabra                 │ 706922941 │ Abracadabra                             │ 75491 │ Lady Gaga │
│    2603558 │ Poker Face                  │    253927 │ The Fame                                │ 75491 │ Lady Gaga │
│  561856742 │ Shallow                     │  74434962 │ A Star Is Born Soundtrack               │ 75491 │ Lady Gaga │
│  561856792 │ Always Remember Us This Way │  74434962 │ A Star Is Born Soundtrack               │ 75491 │ Lady Gaga │
│    4709947 │ Just Dance                  │    433789 │ The Fame Monster (International Deluxe) │ 75491 │ Lady Gaga │
│ 3262333871 │ Garden Of Eden              │ 722147851 │ MAYHEM                                  │ 75491 │ Lady Gaga │
│ 3262333851 │ Disease                     │ 722147851 │ MAYHEM                                  │ 75491 │ Lady Gaga │
│ 3262333891 │ Vanish Into You             │ 722147851 │ MAYHEM                                  │ 75491 │ Lady Gaga │
│    4709944 │ Telephone                   │    433789 │ The Fame Monster (International Deluxe) │ 75491 │ Lady Gaga │
└────────────┴─────────────────────────────┴───────────┴─────────────────────────────────────────┴───────┴───────────┘
```

> 💡 The `--strict` flag decrease fuzzyness in search results.

### `artist`

The `artist` command allows to explore artist top tracks and radios. So you want
to explore Eric Clapton's world (ID `192`)?

```sh
$ onzr artist --top 192
```

> 💡 Remember: you can use the `search` command as a starting point to achieve
> the same task if you don't remember artists IDs (I don't 😅):

```sh
$ onzr search --artist "Eric Clapton" --ids | \
    head -n 1 | \
    onzr artist --top -
```

And there it is! Eric Clapton's top tracks:

```
                                                              Artist tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━┓
┃         ID ┃ Track                                      ┃        ID ┃ Album                                       ┃  ID ┃ Artist       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━┩
│    1140658 │ It's Probably Me                           │    122264 │ Fields Of Gold - The Best Of Sting 1984 -   │ 368 │ Sting        │
│            │                                            │           │ 1994                                        │     │              │
│ 1933842237 │ Tears in Heaven (Acoustic Live)            │ 360638237 │ Unplugged (Live)                            │ 192 │ Eric Clapton │
│    1175620 │ Cocaine                                    │    125707 │ The Cream Of Clapton                        │ 192 │ Eric Clapton │
│ 1940201287 │ Layla (Acoustic; Live at MTV Unplugged,    │ 361895437 │ Clapton Chronicles: The Best of Eric        │ 192 │ Eric Clapton │
│            │ Bray Film Studios, Windsor, England, UK,   │           │ Clapton                                     │     │              │
│            │ 1/16/1992; 1999 Remaster)                  │           │                                             │     │              │
│    4654895 │ Tears in Heaven                            │    428364 │ Rush (Music from the Motion Picture         │ 192 │ Eric Clapton │
│            │                                            │           │ Soundtrack)                                 │     │              │
│    1175626 │ Wonderful Tonight                          │    125707 │ The Cream Of Clapton                        │ 192 │ Eric Clapton │
│     920186 │ I Shot The Sheriff                         │    103610 │ 461 Ocean Boulevard                         │ 192 │ Eric Clapton │
│ 1933842267 │ Layla (Acoustic Live)                      │ 360638237 │ Unplugged (Live)                            │ 192 │ Eric Clapton │
│ 1940201257 │ Change the World                           │ 361895437 │ Clapton Chronicles: The Best of Eric        │ 192 │ Eric Clapton │
│            │                                            │           │ Clapton                                     │     │              │
│ 2253499407 │ Ten Long Years                             │ 433761157 │ Riding With The King (20th Anniversary      │ 192 │ Eric Clapton │
│            │                                            │           │ Deluxe Edition)                             │     │              │
└────────────┴────────────────────────────────────────────┴───────────┴─────────────────────────────────────────────┴─────┴──────────────┘
```

Do you prefer a radio inspired by Eric Clapton?

```sh
$ onzr artist --radio 192
```

Enjoy:

```
                                                              Artist tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃         ID ┃ Track                                   ┃        ID ┃ Album                                    ┃   ID ┃ Artist            ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ 1933842277 │ Running on Faith (Acoustic Live)        │ 360638237 │ Unplugged (Live)                         │  192 │ Eric Clapton      │
│   82323110 │ The Joker                               │   8258840 │ Greatest Hits 1974-78                    │ 3351 │ Steve Miller Band │
│    2526114 │ Little Rachel                           │    247643 │ There's One In Every Crowd               │  192 │ Eric Clapton      │
│   32140181 │ Diamonds on the Soles of Her Shoes      │   3095471 │ Graceland (25th Anniversary Deluxe       │ 1445 │ Paul Simon        │
│            │                                         │           │ Edition)                                 │      │                   │
│ 1933843327 │ Old Love (Acoustic Live)                │ 360638327 │ Unplugged (Deluxe Edition) (Live)        │  192 │ Eric Clapton      │
│ 1358779882 │ Ride Across The River (Remastered 1996) │ 226696942 │ Brothers In Arms (Remastered 1996)       │  176 │ Dire Straits      │
│    1065651 │ The Sensitive Kind                      │    115480 │ Zebop!                                   │  553 │ Santana           │
│   68094422 │ One of These Nights (2013 Remaster)     │   6670363 │ One of These Nights (2013 Remaster)      │  210 │ Eagles            │
│  410006462 │ Rattle That Lock (Live At Pompeii 2016) │  48716252 │ Live At Pompeii                          │ 5114 │ David Gilmour     │
│    1040945 │ Me and Bobby McGee                      │    113728 │ Pearl (Legacy Edition)                   │ 1658 │ Janis Joplin      │
└────────────┴─────────────────────────────────────────┴───────────┴──────────────────────────────────────────┴──────┴───────────────────┘
```

### `mix`

The `mix` command generates playlists using various artists definition. You can
generate a "The Big Four" playlist on-the-fly as follow:

```sh
$ onzr mix --limit 4 Metallica Slayer Megadeth Anthrax
```

There it is 💫

```
                                                                  Onzr Mix tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┓
┃         ID ┃ Track                                     ┃        ID ┃ Album                                                   ┃   ID ┃ Artist    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━┩
│ 1483825282 │ Nothing Else Matters (Remastered 2021)    │ 256250622 │ Metallica (Remastered 2021)                             │  119 │ Metallica │
│    3089034 │ Symphony Of Destruction                   │    299179 │ Countdown To Extinction (Expanded Edition - Remastered) │ 3487 │ Megadeth  │
│    2428039 │ Got The Time                              │    239256 │ Madhouse: The Very Best Of Anthrax                      │ 3580 │ Anthrax   │
│   65690449 │ Raining Blood                             │   6439870 │ Reign In Blood (Expanded)                               │ 3048 │ Slayer    │
│    3089054 │ Tornado Of Souls (2004 Remix)             │    299180 │ Rust In Peace (2004 Remix / Expanded Edition)           │ 3487 │ Megadeth  │
│ 1483825242 │ The Unforgiven (Remastered 2021)          │ 256250622 │ Metallica (Remastered 2021)                             │  119 │ Metallica │
│    3088984 │ A Tout Le Monde (Remastered 2004)         │    299176 │ Youthanasia (Expanded Edition - Remastered)             │ 3487 │ Megadeth  │
│    2428036 │ Antisocial                                │    239256 │ Madhouse: The Very Best Of Anthrax                      │ 3580 │ Anthrax   │
│   92153590 │ Only                                      │   9353244 │ Sound of White Noise - Expanded Edition                 │ 3580 │ Anthrax   │
│  651520622 │ Repentless                                │  90904272 │ Repentless                                              │ 3048 │ Slayer    │
│   61382107 │ Symphony Of Destruction (Remastered 2012) │   6014586 │ Countdown To Extinction (Deluxe Edition - Remastered)   │ 3487 │ Megadeth  │
│  424562692 │ Master Of Puppets (Remastered)            │  51001232 │ Master Of Puppets (Deluxe Box Set / Remastered)         │  119 │ Metallica │
│    1104106 │ Bring The Noise                           │    119083 │ Attack Of The Killer B's                                │ 3580 │ Anthrax   │
│   65724647 │ South Of Heaven                           │   6443119 │ South Of Heaven                                         │ 3048 │ Slayer    │
│   65690440 │ Angel Of Death                            │   6439870 │ Reign In Blood (Expanded)                               │ 3048 │ Slayer    │
│ 1483825212 │ Enter Sandman (Remastered 2021)           │ 256250622 │ Metallica (Remastered 2021)                             │  119 │ Metallica │
└────────────┴───────────────────────────────────────────┴───────────┴─────────────────────────────────────────────────────────┴──────┴───────────┘
```

> 💡 You may adapt the `--limit 10` option to have more or less tracks
> per-artist (defaults to `10`).

Guess what? You can have more magic by generating a "deep mix" 🪄

```sh
$ onzr mix --deep --limit 4 Metallica Slayer Megadeth Anthrax
```

Hello serendipity 🎉

```
                                                                  Onzr Mix tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃         ID ┃ Track                               ┃        ID ┃ Album                                                 ┃    ID ┃ Artist           ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│    2114570 │ Whiskey In The Jar                  │    212391 │ Garage Inc.                                           │   119 │ Metallica        │
│    2150150 │ King Nothing                        │    215356 │ Load                                                  │   119 │ Metallica        │
│    3089054 │ Tornado Of Souls (2004 Remix)       │    299180 │ Rust In Peace (2004 Remix / Expanded Edition)         │  3487 │ Megadeth         │
│    3089033 │ Skin O' My Teeth (2004 Remastered)  │    299179 │ Countdown To Extinction (Expanded Edition -           │  3487 │ Megadeth         │
│            │                                     │           │ Remastered)                                           │       │                  │
│  622118452 │ Burn in Hell                        │  85244752 │ Puritanical Euphoric Misanthropia                     │   123 │ Dimmu Borgir     │
│    1103953 │ Indians                             │    119067 │ Among The Living                                      │  3580 │ Anthrax          │
│   15523788 │ Forest                              │   1434890 │ Toxicity                                              │   458 │ System of a Down │
│  660680372 │ The Rise of Chaos                   │  92670482 │ The Rise of Chaos                                     │  5761 │ Accept           │
│ 1043401402 │ Maggots (30th Anniversary Remix)    │ 165336412 │ Scumdogs of the Universe (30th Anniversary)           │ 13096 │ GWAR             │
│  654764302 │ Sleepwalker (2019 - Remaster)       │  91551662 │ United Abominations (2019 - Remaster)                 │  3487 │ Megadeth         │
│  130250228 │ We Care a Lot                       │  13810432 │ We Care a Lot (Deluxe Band Edition Remastered)        │  2255 │ Faith No More    │
│   76391259 │ Jihad (Album Version)               │   7574563 │ Christ Illusion                                       │  3048 │ Slayer           │
│   65690421 │ Divine Intervention (Album Version) │   6439868 │ Divine Intervention                                   │  3048 │ Slayer           │
│    5194654 │ Practice What You Preach            │    476227 │ Practice What You Preach                              │ 13193 │ Testament        │
│ 1084230662 │ In My World                         │ 174179242 │ Persistence Of Time (30th Anniversary Remaster)       │  3580 │ Anthrax          │
│ 1503494282 │ Transitions from Persona to Object  │ 261075002 │ We Are the Romans                                     │  9419 │ Botch            │
└────────────┴─────────────────────────────────────┴───────────┴───────────────────────────────────────────────────────┴───────┴──────────────────┘
```

As expected, you can pipe your mix with the `--ids` flag to the `play` command:

```sh
$ onzr mix --ids --deep --limit 4 Metallica Slayer Megadeth Anthrax | \
    onzr play -
```

### `play`

The `play` command does what it says: it plays a track IDs list passed as
arguments. Most of times as we already demonstrated, it will be the last command
of a UNIX pipe:

```sh
$ onzr search --artist "Go go penguin" --ids | \
    head -n 1 | \
    onzr artist --ids - | \
    onzr play --quality MP3_320 --shuffle -
```

> This command plays "Go go penguin" top tracks in high-quality MP3 with a
> random order (see the `--shuffle` option).

> 💔⚠️ Please note that for now the **FLAC** format quality does not work at
> all.

## Quick hacking guide (for developers)

Install dependencies in a working environment:

```sh
$ make bootstrap
```

Run linters:

```sh
$ make lint
```

Run tests:

```sh
$ make test
```

## License

This work is released under the MIT License.
