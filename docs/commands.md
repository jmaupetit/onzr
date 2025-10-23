# Command Line Interface (CLI)

```
$ onzr --help

 Usage: onzr [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.              │
│ --show-completion             Show completion for the current shell, to copy it or   │
│                               customize the installation.                            │
│ --help                        Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────╮
│ init       Intialize onzr player.                                                    │
│ config     Display or edit Onzr's configuration.                                     │
│ search     Search tracks, artists and/or albums.                                     │
│ artist     Get artist popular track ids.                                             │
│ album      Get album tracks.                                                         │
│ mix        Create a playlist from multiple artists.                                  │
│ add        Add one (or more) tracks to the queue.                                    │
│ queue      List queue tracks.                                                        │
│ clear      Empty queue.                                                              │
│ now        Show details about the track that is being played and the player status.  │
│ play       Play queued tracks.                                                       │
│ pause      Pause/resume playing.                                                     │
│ stop       Stop playing queue.                                                       │
│ next       Play next track in queue.                                                 │
│ previous   Play previous track in queue.                                             │
│ serve      Run onzr http server.                                                     │
│ state      Get server state.                                                         │
│ version    Get program version.                                                      │
│ openapi    Get Onzr HTTP API OpenAPI schema.                                         │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

Remember that Onzr is a CLI (Command Line Interface) and that we love UNIX. That
being said, you won't be surprised to pipe Onzr commands to achieve what you
want.

```sh
onzr search --artist "Lady Gaga" --ids --first | \
    onzr artist --top --limit 20 --ids - | \
    onzr add -
```

In this example, we will be adding Lady Gaga's top 20 most listened tracks to
the player queue.

## `init`

The `init` command creates Onzr configuration file:

```sh
onzr init
```

It is supposed to be run **once** to be able to start the server or to use
other commands.

!!! Tip

    This command will prompt for an `ARL` token. If you don't know how to find
    it, please follow [this
    guide](https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie).

## `config`

The `config` command provides various operations related to Onzr's
configuration. By default, it will display your current configuration in YAML
format.

```sh
onzr config
```

The output should look like:

```yaml
ARL: "configuredarl"
# QUALITY: MP3_128
# DEBUG: false
# SCHEMA: http
# HOST: localhost
# PORT: 9473
# API_ROOT_URL: /api/v1
# TRACK_STREAM_ENDPOINT: /queue/{rank}/stream
DEEZER_BLOWFISH_SECRET: "g4el58wc0zvf9na1"
# THEME:
#   # Base palette
#   primary_color: "#9B6BDF"
#   secondary_color: "#75D7EC"
#   tertiary_color: "#E356A7"
#   # Entities
#   title_color: "#9B6BDF"
#   artist_color: "#75D7EC"
#   album_color: "#E356A7"
#   # Messages
#   alert_color: "red"
```

Using the `--path` (or `-p`) option will only display the configuration file
path:

```sh
onzr -p
```

```
/home/johndoe/.config/onzr/settings.yaml
```

And you can also edit your configuration using the `--edit` (or `-e`):

```sh
onzr config -e
```

It will start your default editor with your configuration loaded. Save it and
you're good to go.

!!! Tip

    You can set your default editor using the `$EDITOR` environment variable.

## `serve`

The `serve` command should be run once to start Onzr web server:

```sh
onzr serve
```

Once ran, Onzr server main instance is active (by default at:
[localhost:9473](http://localhost:9473)).

!!! Tip "Pro Tip ™"

    You should launch a new terminal to run other commands communicating with
    the server.

    Alternatively, if you prefer to use the same terminal, you can run the
    server in the background and only print error (and higher) logger events:

    ```sh
    onzr serve --log-level error &
    ```

## `search`

Onzr works extensively using Deezer's identifiers (IDs) for artists, albums and
tracks. As you may not know them (yet?), you can start exploring Deezer using
the `search` command:

```sh
onzr search --help
```

You can search by artist, album or track using the corresponding flag, _e.g._ if
you are looking for Lady Gaga:

```sh
onzr search --artist "Lady Gaga"
```

The command output looks like:

```
                          Search results
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        ID ┃ Artist                                             ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│     75491 │ Lady Gaga                                          │
│   7735426 │ Bradley Cooper                                     │
│       145 │ Beyoncé                                            │
│     12815 │ Pitty                                              │
│     75798 │ Adele                                              │
│       290 │ Madonna                                            │
│   8425674 │ Lady Wray                                          │
│   8706544 │ Dua Lipa                                           │
│    144227 │ Katy Perry                                         │
│    429675 │ Bruno Mars                                         │
│      3469 │ Sia                                                │
│       483 │ Britney Spears                                     │
│  64927672 │ Teddy Swims                                        │
│     69925 │ P!nk                                               │
│  53187832 │ Lady Gaga & Bradley Cooper                         │
│  73789052 │ Chaax                                              │
│ 170247847 │ Turquoise M                                        │
│   4182755 │ Made famous by Lady Gaga                           │
│       933 │ Rednex                                             │
│   4195939 │ Lady Gaga's Karaoke Band, Made famous by Lady Gaga │
│  12245134 │ Lady Lava                                          │
│ 304731571 │ JJ                                                 │
│   7570760 │ Lady Parts                                         │
│   1201251 │ Lady Gaga's Karaoke Band                           │
│  64308902 │ Brö                                                │
└───────────┴────────────────────────────────────────────────────┘
```

Use the `--ids` flag to only print identifiers to the standard output if your
intent is to pipe your search result to another command (e.g. `artist` or
`play`).

```sh
onzr search --artist "Lady Gaga" --ids --first | \
    onzr artist - # (1)
```

1. 💡 the `-` argument of the `artist` command indicates to read artist ID from `stdin`

Your search result piped to the artist command display the artist top tracks:

```
                               Artist collection
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃         ID ┃ Track                    ┃ Album                    ┃ Artist    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 3537990861 │ The Dead Dance           │ The Dead Dance           │ Lady Gaga │
│ 2947516331 │ Die With A Smile         │ Die With A Smile         │ Lady Gaga │
│ 3214169391 │ Abracadabra              │ Abracadabra              │ Lady Gaga │
│  561856742 │ Shallow                  │ A Star Is Born           │ Lady Gaga │
│            │                          │ Soundtrack               │           │
│    2603558 │ Poker Face               │ The Fame                 │ Lady Gaga │
│  561856792 │ Always Remember Us This  │ A Star Is Born           │ Lady Gaga │
│            │ Way                      │ Soundtrack               │           │
│    4709947 │ Just Dance               │ The Fame Monster         │ Lady Gaga │
│            │                          │ (International Deluxe)   │           │
│    4709944 │ Telephone                │ The Fame Monster         │ Lady Gaga │
│            │                          │ (International Deluxe)   │           │
│   11747937 │ Bloody Mary              │ Born This Way            │ Lady Gaga │
│            │                          │ (International Special   │           │
│            │                          │ Edition Version)         │           │
│    4709938 │ Alejandro                │ The Fame Monster         │ Lady Gaga │
│            │                          │ (International Deluxe)   │           │
└────────────┴──────────────────────────┴──────────────────────────┴───────────┘
```

!!! Tip

    The `search` command `--strict` flag decreases fuzzyness in search results.

## `artist`

The `artist` command allows to explore artist top tracks and radios. So you want
to explore Eric Clapton's world (ID `192`)?

```sh
onzr artist --top 192
```

!!! Tip

    Remember: you can use the `search` command as a starting point to achieve
    the same task if you don't remember artists IDs (I don't 😅):

    ```sh
    onzr search --artist "Eric Clapton" --ids --first | \
        onzr artist --top -
    ```

And there it is! Eric Clapton's top tracks:

```
                               Artist collection
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃         ID ┃ Track                  ┃ Album                   ┃ Artist       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│    1140658 │ It's Probably Me       │ Fields Of Gold - The    │ Sting        │
│            │                        │ Best Of Sting 1984 -    │              │
│            │                        │ 1994                    │              │
│ 1933842237 │ Tears in Heaven        │ Unplugged (Live)        │ Eric Clapton │
│            │ (Acoustic Live)        │                         │              │
│    1175620 │ Cocaine                │ The Cream Of Clapton    │ Eric Clapton │
│    4654895 │ Tears in Heaven        │ Rush (Music from the    │ Eric Clapton │
│            │                        │ Motion Picture          │              │
│            │                        │ Soundtrack)             │              │
│ 1940201287 │ Layla (Acoustic; Live  │ Clapton Chronicles: The │ Eric Clapton │
│            │ at MTV Unplugged, Bray │ Best of Eric Clapton    │              │
│            │ Film Studios, Windsor, │                         │              │
│            │ England, UK,           │                         │              │
│            │ 1/16/1992; 1999        │                         │              │
│            │ Remaster)              │                         │              │
│    1175626 │ Wonderful Tonight      │ The Cream Of Clapton    │ Eric Clapton │
│ 1933842267 │ Layla (Acoustic Live)  │ Unplugged (Live)        │ Eric Clapton │
│     920186 │ I Shot The Sheriff     │ 461 Ocean Boulevard     │ Eric Clapton │
│ 1940201257 │ Change the World       │ Clapton Chronicles: The │ Eric Clapton │
│            │                        │ Best of Eric Clapton    │              │
│ 2253499407 │ Ten Long Years         │ Riding With The King    │ Eric Clapton │
│            │                        │ (20th Anniversary       │              │
│            │                        │ Deluxe Edition)         │              │
└────────────┴────────────────────────┴─────────────────────────┴──────────────┘
```

Do you prefer a radio inspired by Eric Clapton?

```sh
onzr artist --radio 192
```

Enjoy:

```
                               Artist collection
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃         ID ┃ Track               ┃ Album               ┃ Artist              ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 1927365327 │ Don't Cry Sister    │ The Road to         │ Eric Clapton        │
│            │                     │ Escondido           │                     │
│     927766 │ Can't Find My Way   │ Blind Faith         │ Blind Faith         │
│            │ Home                │                     │                     │
│ 1927349807 │ Circus              │ Pilgrim             │ Eric Clapton        │
│ 2472547801 │ Sweet Sounds Of     │ Sweet Sounds Of     │ The Rolling Stones  │
│            │ Heaven (Edit)       │ Heaven              │                     │
│ 1933843257 │ Nobody Knows You    │ Unplugged (Deluxe   │ Eric Clapton        │
│            │ When You're Down    │ Edition) (Live)     │                     │
│            │ and Out (Acoustic   │                     │                     │
│            │ Live)               │                     │                     │
│  542186022 │ Jealous Guy         │ Imagine (The        │ John Lennon         │
│            │ (Ultimate Mix)      │ Ultimate            │                     │
│            │                     │ Collection)         │                     │
│  410006472 │ Faces of Stone      │ Live At Pompeii     │ David Gilmour       │
│            │ (Live At Pompeii    │                     │                     │
│            │ 2016)               │                     │                     │
│    4124703 │ Fool To Cry         │ Black And Blue      │ The Rolling Stones  │
│            │ (Remastered 2009)   │ (Remastered 2009)   │                     │
│    4125588 │ I Got The Blues     │ Sticky Fingers      │ The Rolling Stones  │
│            │ (2009 Mix)          │ (Remastered)        │                     │
│ 1550811232 │ Peace Train         │ Teaser And The      │ Yusuf / Cat Stevens │
│            │ (Remastered 2021)   │ Firecat (Remastered │                     │
│            │                     │ 2021)               │                     │
└────────────┴─────────────────────┴─────────────────────┴─────────────────────┘
```

You can also explore artist's albums using the `--albums` option:

```sh
onzr search --artist Radiohead --ids --first | \
    onzr artist --albums --limit 20 -
```

There you go, here is Radiohead's discography:

```
                               Artist collection
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃        ID ┃ Album                                   ┃ Artist    ┃ Released   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 792320571 │ Hail to the Thief (Live Recordings      │ Radiohead │ 2025-08-13 │
│           │ 2003-2009)                              │           │            │
│ 265569082 │ KID A MNESIA                            │ Radiohead │ 2021-11-05 │
│  43197211 │ OK Computer OKNOTOK 1997 2017           │ Radiohead │ 2017-06-23 │
│  14880561 │ In Rainbows (Disk 2)                    │ Radiohead │ 2016-10-14 │
│  14879823 │ A Moon Shaped Pool                      │ Radiohead │ 2016-05-09 │
│  14880501 │ TKOL RMX 1234567                        │ Radiohead │ 2011-10-10 │
│  14880315 │ The King Of Limbs                       │ Radiohead │ 2011-02-18 │
│  14880659 │ In Rainbows                             │ Radiohead │ 2007-12-28 │
│  14879789 │ Com Lag: 2+2=5                          │ Radiohead │ 2004-03-24 │
│  14879739 │ Hail To the Thief                       │ Radiohead │ 2003-06-09 │
│  14879753 │ I Might Be Wrong                        │ Radiohead │ 2001-11-12 │
│  14879749 │ Amnesiac                                │ Radiohead │ 2001-03-12 │
│  14880741 │ Kid A                                   │ Radiohead │ 2000-10-02 │
│  14879797 │ Karma Police                            │ Radiohead │ 1997-08-25 │
│  14879699 │ OK Computer                             │ Radiohead │ 1997-06-17 │
│  14880317 │ The Bends                               │ Radiohead │ 1995-03-13 │
│  14880813 │ My Iron Lung                            │ Radiohead │ 1994-09-26 │
│  14880711 │ Pablo Honey                             │ Radiohead │ 1993-02-22 │
│ 423524437 │ Creep EP                                │ Radiohead │ 1992-09-21 │
│ 121893052 │ Drill EP                                │ Radiohead │ 1992-05-05 │
└───────────┴─────────────────────────────────────────┴───────────┴────────────┘
```

## `album`

The `album` command lists album tracks to check or play them:

```sh
onzr search --album "Friday night in San Francisco" --ids --first | \
    onzr album -
```

And there it is:

```
                                  Album tracks
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃      ID ┃ Track                     ┃ Album                    ┃ Artist      ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 1031231 │ Mediterranean Sundance /  │ Friday Night in San      │ Al Di Meola │
│         │ Rio Ancho (Live at        │ Francisco                │             │
│         │ Warfield Theatre, San     │                          │             │
│         │ Francisco, CA - December  │                          │             │
│         │ 5, 1980)                  │                          │             │
│ 1028083 │ Short Tales of the Black  │ Friday Night in San      │ Al Di Meola │
│         │ Forest (Live at Warfield  │ Francisco                │             │
│         │ Theatre, San Francisco,   │                          │             │
│         │ CA - December 5, 1980)    │                          │             │
│ 1030435 │ Frevo Rasgado (Live at    │ Friday Night in San      │ Al Di Meola │
│         │ Warfield Theatre, San     │ Francisco                │             │
│         │ Francisco, CA - December  │                          │             │
│         │ 5, 1980)                  │                          │             │
│ 1028903 │ Fantasia Suite (Live at   │ Friday Night in San      │ Al Di Meola │
│         │ Warfield Theatre, San     │ Francisco                │             │
│         │ Francisco, CA - December  │                          │             │
│         │ 5, 1980)                  │                          │             │
│ 1028399 │ Guardian Angel (Live at   │ Friday Night in San      │ Al Di Meola │
│         │ Warfield Theatre, San     │ Francisco                │             │
│         │ Francisco, CA - December  │                          │             │
│         │ 5, 1980)                  │                          │             │
└─────────┴───────────────────────────┴──────────────────────────┴─────────────┘
```

To play the entire album, don't forget to list only track ids and pass them to
the `add` command:

```sh
onzr search --album "Friday night in San Francisco" --ids --first | \
    onzr album --ids - | \
    onzr add -
```

## `mix`

The `mix` command generates playlists using various artists definition. You can
generate a "The Big Four" playlist on-the-fly as follow:

```sh
onzr mix --limit 4 Metallica Slayer Megadeth Anthrax
```

There it is 💫

```
                                Onzr Mix tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃         ID ┃ Track                    ┃ Album                    ┃ Artist    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│   65724647 │ South Of Heaven          │ South Of Heaven          │ Slayer    │
│ 1483825282 │ Nothing Else Matters     │ Metallica (Remastered    │ Metallica │
│            │ (Remastered 2021)        │ 2021)                    │           │
│ 3578462431 │ Tipping Point            │ Tipping Point            │ Megadeth  │
│ 1483825242 │ The Unforgiven           │ Metallica (Remastered    │ Metallica │
│            │ (Remastered 2021)        │ 2021)                    │           │
│    3089054 │ Tornado Of Souls (2004   │ Rust In Peace (2004      │ Megadeth  │
│            │ Remix)                   │ Remix / Expanded         │           │
│            │                          │ Edition)                 │           │
│  424562692 │ Master Of Puppets        │ Master Of Puppets        │ Metallica │
│            │ (Remastered)             │ (Deluxe Box Set /        │           │
│            │                          │ Remastered)              │           │
│   65690440 │ Angel Of Death           │ Reign In Blood           │ Slayer    │
│            │                          │ (Expanded)               │           │
│    3088984 │ A Tout Le Monde          │ Youthanasia (Expanded    │ Megadeth  │
│            │ (Remastered 2004)        │ Edition - Remastered)    │           │
│   61382107 │ Symphony Of Destruction  │ Countdown To Extinction  │ Megadeth  │
│            │ (Remastered 2012)        │ (Deluxe Edition -        │           │
│            │                          │ Remastered)              │           │
│ 1483825212 │ Enter Sandman            │ Metallica (Remastered    │ Metallica │
│            │ (Remastered 2021)        │ 2021)                    │           │
│   65690449 │ Raining Blood            │ Reign In Blood           │ Slayer    │
│            │                          │ (Expanded)               │           │
│    2428039 │ Got The Time             │ Madhouse: The Very Best  │ Anthrax   │
│            │                          │ Of Anthrax               │           │
│    2428036 │ Antisocial               │ Madhouse: The Very Best  │ Anthrax   │
│            │                          │ Of Anthrax               │           │
│ 3212862171 │ Caught In A Mosh         │ Among The Living -       │ Anthrax   │
│            │                          │ Deluxe Edition (eAlbum   │           │
│            │                          │ w/ PDF booklet audio     │           │
│            │                          │ only)                    │           │
│    1176687 │ Madhouse                 │ Spreading The Disease    │ Anthrax   │
│   65707337 │ Dead Skin Mask (Album    │ Seasons In The Abyss     │ Slayer    │
│            │ Version)                 │                          │           │
└────────────┴──────────────────────────┴──────────────────────────┴───────────┘
```

!!! Tip

    You may adapt the `--limit 10` option to have more or less tracks
    per-artist (defaults to `10`).

Guess what? You can have more magic by generating a "deep mix" 🪄

```sh
onzr mix --deep --limit 4 Metallica Slayer Megadeth Anthrax
```

Hello serendipity 🎉

```
                                Onzr Mix tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃         ID ┃ Track                 ┃ Album                 ┃ Artist          ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│    2851466 │ Amen                  │ Chaos A.D.            │ Sepultura       │
│    3089037 │ Sweating Bullets      │ Countdown To          │ Megadeth        │
│            │ (Remastered 2004)     │ Extinction (Expanded  │                 │
│            │                       │ Edition - Remastered) │                 │
│ 1084230652 │ Keep It In The Family │ Persistence Of Time   │ Anthrax         │
│            │                       │ (30th Anniversary     │                 │
│            │                       │ Remaster)             │                 │
│   65707334 │ Blood Red (Album      │ Seasons In The Abyss  │ Slayer          │
│            │ Version)              │                       │                 │
│   65690448 │ Postmortem            │ Reign In Blood        │ Slayer          │
│            │                       │ (Expanded)            │                 │
│    5194654 │ Practice What You     │ Practice What You     │ Testament       │
│            │ Preach                │ Preach                │                 │
│     549239 │ Cruelty Brought Thee  │ Cruelty & The Beast   │ Cradle of Filth │
│            │ Orchids               │                       │                 │
│ 3407660541 │ King Nothing          │ Load (Remastered      │ Metallica       │
│            │ (Remastered)          │ Deluxe Box Set)       │                 │
│    3088984 │ A Tout Le Monde       │ Youthanasia (Expanded │ Megadeth        │
│            │ (Remastered 2004)     │ Edition - Remastered) │                 │
│   87938845 │ The Beautiful People  │ Antichrist Superstar  │ Marilyn Manson  │
│  690926792 │ Catharsis             │ Volume 8: The Threat  │ Anthrax         │
│            │                       │ is Real               │                 │
│  575867572 │ One                   │ …And Justice for All  │ Metallica       │
│            │                       │ (Remastered)          │                 │
│    3088941 │ Into The Lungs Of     │ So Far, So Good...So  │ Megadeth        │
│            │ Hell (Remastered      │ What! (Expanded       │                 │
│            │ 2004)                 │ Edition - Remastered) │                 │
│    2851463 │ Refuse / Resist       │ Chaos A.D.            │ Sepultura       │
│     714426 │ Domination            │ Cowboys from Hell     │ Pantera         │
│  627302522 │ Freezing Moon         │ De Mysteriis Dom      │ Mayhem          │
│            │                       │ Sathanas              │                 │
└────────────┴───────────────────────┴───────────────────────┴─────────────────┘
```

As expected, you can pipe your mix with the `--ids` flag to the `add` command:

```sh
onzr mix --ids --deep --limit 4 Metallica Slayer Megadeth Anthrax | \
    onzr add -
```

## `add`

The `add` allows you to add tracks to the queue. Tracks identifiers should be
given as command arguments:

```sh
onzr add 4952889 4952964 15347301
```

This command adds 3 tracks to the queue.

As already seen, you can read track identifiers from the standard input by
using the `-` special identifier:

```sh
onzr search --track "all along the watchtower" --ids | \
    onzr add -
```

This command adds a track search result to the queue.

## `queue`

The `queue` command list tracks added to the queue:

```sh
onzr queue
```

## `clear`

The `clear` command stops the player and removes all tracks from the queue:

```sh
onzr clear
```

## `now`

The `onzr now` command gives you details about the track being currently played:

```sh
onzr now
```

You can follow tracks being played in live using the `-f` option:

```sh
onzr now -f
```

!!! Tip

    Hit ++ctrl+c++ to kill the command and restore your shell prompt.

## `play`

The `play` command does what it says: it (re-)starts playing queued tracks.

```sh
onzr search --artist "Go go penguin" --ids --first | \
    onzr artist --ids - | \
    onzr add - && \
    onzr play
```

This command plays "Go go penguin" top tracks; considering an empty queue
before starting the command.

Considering you have already queued tracks, you can start playing a track in
the queue given its rank (1-based numbering):

```sh
onzr play --rank 2
```

!!! Tip

    You can get the track rank by listing queued tracks using the `onzr queue`
    command.

## `pause`

The `pause` command toggles the player pause state:

```sh
onzr pause
```

## `stop`

The `stop` command stops the player:

```sh
onzr stop
```

## `next`

The `next` command plays the next track in queue:

```sh
onzr next
```

Note that it has no effect if you reach the end of the queue.

## `previous`

The `previous` command plays the previous track in queue:

```sh
onzr previous
```

Note that it has no effect if you reach the beginning of the queue.

## `state`

The `state` command gives you info about the server (player and queue) state:

```sh
onzr state
```

## `version`

The `version` command is useful to know which version of Onzr you are running:

```sh
onzr version
```

## `openapi`

The `openapi` command prints the OpenAPI schema of Onzr HTTP API in JSON format.

```sh
onzr openapi
```
