# Onzr

The one-hour-late Deezer 💜 CLI.

> ⚠️ This project is a work in progress. It works in its core parts, but will
> not meet standard requirements for a decent player.

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

> In this case, the server is ran as a background job; see the `serve` command
> documentation for details about running Onzr server.

Play your first album:

```sh
onzr search --artist "Billie Eilish" --ids | \
    head -n 1 | \
    onzr artist --albums --ids - | \
    head -n 1 | \
    onzr album --ids - | \
    onzr add - && \
    onzr play
```

> 🎉 In this command, we look for the latest Billie Eilish album, add it to the
> queue and play it instantly!

## Commands

Remember that Onzr is a CLI (Command Line Interface) and that we love UNIX. That
being said, you won't be surprised to pipe Onzr commands to achieve what you
want.

```sh
onzr search --artist "Lady Gaga" --ids | \
    head -n 1 | \
    onzr artist --top --limit 20 --ids - | \
    onzr add -
```

> In this example, we will be adding Lady Gaga's top 20 most listened tracks to
> the player queue.

### `serve`

The `serve` command should be run once to start Onzr web server:

```sh
onzr serve
```

Once ran, Onzr server main instance is active (by default at:
[localhost:9473](http://localhost:9473)).

> 👉 You should launch a new terminal to run other commands communicating with
> the server.

Alternatively, if you prefer to use the same terminal, you can run the server in
the background and only print error (and higher) logger events:

```sh
onzr serve --log-level error &
```

### `search`

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
onzr search --artist "Lady Gaga" --ids | \
    head -n 1 | \
    onzr artist -
```

> 💡 The `-` argument of the `artist` command indicates to read artist ID from
> `stdin`.

Your search result piped to the artist command display the artist top tracks:

```
                                               Artist collection
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃         ID ┃ Track                       ┃ Album                                                 ┃ Artist    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 3537990861 │ The Dead Dance              │ The Dead Dance                                        │ Lady Gaga │
│ 2947516331 │ Die With A Smile            │ Die With A Smile                                      │ Lady Gaga │
│ 3214169391 │ Abracadabra                 │ Abracadabra                                           │ Lady Gaga │
│  561856742 │ Shallow                     │ A Star Is Born Soundtrack                             │ Lady Gaga │
│    2603558 │ Poker Face                  │ The Fame                                              │ Lady Gaga │
│  561856792 │ Always Remember Us This Way │ A Star Is Born Soundtrack                             │ Lady Gaga │
│    4709947 │ Just Dance                  │ The Fame Monster (International Deluxe)               │ Lady Gaga │
│    4709944 │ Telephone                   │ The Fame Monster (International Deluxe)               │ Lady Gaga │
│   11747937 │ Bloody Mary                 │ Born This Way (International Special Edition Version) │ Lady Gaga │
│    4709938 │ Alejandro                   │ The Fame Monster (International Deluxe)               │ Lady Gaga │
└────────────┴─────────────────────────────┴───────────────────────────────────────────────────────┴───────────┘
```

> 💡 The `--strict` flag decrease fuzzyness in search results.

### `artist`

The `artist` command allows to explore artist top tracks and radios. So you want
to explore Eric Clapton's world (ID `192`)?

```sh
onzr artist --top 192
```

> 💡 Remember: you can use the `search` command as a starting point to achieve
> the same task if you don't remember artists IDs (I don't 😅):

```sh
onzr search --artist "Eric Clapton" --ids | \
    head -n 1 | \
    onzr artist --top -
```

And there it is! Eric Clapton's top tracks:

```
                                                 Artist collection
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓
┃         ID ┃ Track                                    ┃ Album                                    ┃ Artist       ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━┩
│    1140658 │ It's Probably Me                         │ Fields Of Gold - The Best Of Sting 1984  │ Sting        │
│            │                                          │ - 1994                                   │              │
│ 1933842237 │ Tears in Heaven (Acoustic Live)          │ Unplugged (Live)                         │ Eric Clapton │
│    1175620 │ Cocaine                                  │ The Cream Of Clapton                     │ Eric Clapton │
│    4654895 │ Tears in Heaven                          │ Rush (Music from the Motion Picture      │ Eric Clapton │
│            │                                          │ Soundtrack)                              │              │
│ 1940201287 │ Layla (Acoustic; Live at MTV Unplugged,  │ Clapton Chronicles: The Best of Eric     │ Eric Clapton │
│            │ Bray Film Studios, Windsor, England, UK, │ Clapton                                  │              │
│            │ 1/16/1992; 1999 Remaster)                │                                          │              │
│    1175626 │ Wonderful Tonight                        │ The Cream Of Clapton                     │ Eric Clapton │
│ 1933842267 │ Layla (Acoustic Live)                    │ Unplugged (Live)                         │ Eric Clapton │
│     920186 │ I Shot The Sheriff                       │ 461 Ocean Boulevard                      │ Eric Clapton │
│ 1940201257 │ Change the World                         │ Clapton Chronicles: The Best of Eric     │ Eric Clapton │
│            │                                          │ Clapton                                  │              │
│ 2253499407 │ Ten Long Years                           │ Riding With The King (20th Anniversary   │ Eric Clapton │
│            │                                          │ Deluxe Edition)                          │              │
└────────────┴──────────────────────────────────────────┴──────────────────────────────────────────┴──────────────┘
```

Do you prefer a radio inspired by Eric Clapton?

```sh
onzr artist --radio 192
```

Enjoy:

```
                                                 Artist collection
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃         ID ┃ Track                           ┃ Album                           ┃ Artist                         ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 2986824131 │ Always On My Mind               │ Meanwhile                       │ Eric Clapton                   │
│  584213822 │ Floating Away                   │ Down The Road Wherever (Deluxe) │ Mark Knopfler                  │
│ 1933843337 │ Rollin' & Tumblin' (Acoustic    │ Unplugged (Deluxe Edition)      │ Eric Clapton                   │
│            │ Live)                           │ (Live)                          │                                │
│    1571367 │ Teardrops In My Tequila         │ #8                              │ J.J. Cale                      │
│ 1927349767 │ River of Tears                  │ Pilgrim                         │ Eric Clapton                   │
│     848664 │ Mary Had a Little Lamb          │ The Essential Stevie Ray        │ Stevie Ray Vaughan & Double    │
│            │                                 │ Vaughan And Double Trouble      │ Trouble                        │
│    2288683 │ Darling Pretty                  │ Golden Heart                    │ Mark Knopfler                  │
│   14640574 │ If I Were a Carpenter (2006     │ Fate of Nations                 │ Robert Plant                   │
│            │ Remaster)                       │                                 │                                │
│    2236733 │ News                            │ Communiqué                      │ Dire Straits                   │
│  389044621 │ Blood Of Eden (Live)            │ Live Blood                      │ Peter Gabriel                  │
└────────────┴─────────────────────────────────┴─────────────────────────────────┴────────────────────────────────┘
```

You can also explore artist's albums using the `--albums` option:

```sh
onzr search --artist Radiohead --ids | \
    head -n 1 | \
    onzr artist --albums --limit 20 -
```

There you go, here is Radiohead's discography:

```
                                  Artist collection
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃        ID ┃ Album                                         ┃ Artist    ┃ Released   ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 792320571 │ Hail to the Thief (Live Recordings 2003-2009) │ Radiohead │ 2025-08-13 │
│ 265569082 │ KID A MNESIA                                  │ Radiohead │ 2021-11-05 │
│  43197211 │ OK Computer OKNOTOK 1997 2017                 │ Radiohead │ 2017-06-23 │
│  14880561 │ In Rainbows (Disk 2)                          │ Radiohead │ 2016-10-14 │
│  14879823 │ A Moon Shaped Pool                            │ Radiohead │ 2016-05-09 │
│  14880501 │ TKOL RMX 1234567                              │ Radiohead │ 2011-10-10 │
│  14880315 │ The King Of Limbs                             │ Radiohead │ 2011-02-18 │
│  14880659 │ In Rainbows                                   │ Radiohead │ 2007-12-28 │
│  14879789 │ Com Lag: 2+2=5                                │ Radiohead │ 2004-03-24 │
│  14879739 │ Hail To the Thief                             │ Radiohead │ 2003-06-09 │
│  14879753 │ I Might Be Wrong                              │ Radiohead │ 2001-11-12 │
│  14879749 │ Amnesiac                                      │ Radiohead │ 2001-03-12 │
│  14880741 │ Kid A                                         │ Radiohead │ 2000-10-02 │
│  14879797 │ Karma Police                                  │ Radiohead │ 1997-08-25 │
│  14879699 │ OK Computer                                   │ Radiohead │ 1997-06-17 │
│  14880317 │ The Bends                                     │ Radiohead │ 1995-03-13 │
│  14880813 │ My Iron Lung                                  │ Radiohead │ 1994-09-26 │
│  14880711 │ Pablo Honey                                   │ Radiohead │ 1993-02-22 │
│ 423524437 │ Creep EP                                      │ Radiohead │ 1992-09-21 │
│ 121893052 │ Drill EP                                      │ Radiohead │ 1992-05-05 │
└───────────┴───────────────────────────────────────────────┴───────────┴────────────┘
```

### `album`

The `album` command list album tracks to check or play them:

```sh
# Display track list
onzr search --album "Friday night in San Francisco" --ids | \
    head -n 1 | \
    onzr album -
```

And there it is:

```
                                                   Album tracks
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃      ID ┃ Track                                                   ┃ Album                         ┃ Artist      ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 1031231 │ Mediterranean Sundance / Rio Ancho (Live at Warfield    │ Friday Night in San Francisco │ Al Di Meola │
│         │ Theatre, San Francisco, CA - December 5, 1980)          │                               │             │
│ 1028083 │ Short Tales of the Black Forest (Live at Warfield       │ Friday Night in San Francisco │ Al Di Meola │
│         │ Theatre, San Francisco, CA - December 5, 1980)          │                               │             │
│ 1030435 │ Frevo Rasgado (Live at Warfield Theatre, San Francisco, │ Friday Night in San Francisco │ Al Di Meola │
│         │ CA - December 5, 1980)                                  │                               │             │
│ 1028903 │ Fantasia Suite (Live at Warfield Theatre, San           │ Friday Night in San Francisco │ Al Di Meola │
│         │ Francisco, CA - December 5, 1980)                       │                               │             │
│ 1028399 │ Guardian Angel (Live at Warfield Theatre, San           │ Friday Night in San Francisco │ Al Di Meola │
│         │ Francisco, CA - December 5, 1980)                       │                               │             │
└─────────┴─────────────────────────────────────────────────────────┴───────────────────────────────┴─────────────┘
```

To play the entire album, don't forget to list only track ids and pass them to
the `add` command:

```sh
# Get track ids and add them to the queue
onzr search --album "Friday night in San Francisco" --ids | \
    head -n 1 | \
    onzr album --ids - | \
    onzr add -
```

### `mix`

The `mix` command generates playlists using various artists definition. You can
generate a "The Big Four" playlist on-the-fly as follow:

```sh
onzr mix --limit 4 Metallica Slayer Megadeth Anthrax
```

There it is 💫

```
                                                  Onzr Mix tracks
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃         ID ┃ Track                                     ┃ Album                                      ┃ Artist    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│    3089054 │ Tornado Of Souls (2004 Remix)             │ Rust In Peace (2004 Remix / Expanded       │ Megadeth  │
│            │                                           │ Edition)                                   │           │
│  424562692 │ Master Of Puppets (Remastered)            │ Master Of Puppets (Deluxe Box Set /        │ Metallica │
│            │                                           │ Remastered)                                │           │
│   65690449 │ Raining Blood                             │ Reign In Blood (Expanded)                  │ Slayer    │
│   65707342 │ Seasons In The Abyss (Album Version)      │ Seasons In The Abyss                       │ Slayer    │
│ 3212862171 │ Caught In A Mosh                          │ Among The Living - Deluxe Edition (eAlbum  │ Anthrax   │
│            │                                           │ w/ PDF booklet audio only)                 │           │
│    3089034 │ Symphony Of Destruction                   │ Countdown To Extinction (Expanded Edition  │ Megadeth  │
│            │                                           │ - Remastered)                              │           │
│   65724647 │ South Of Heaven                           │ South Of Heaven                            │ Slayer    │
│    1176687 │ Madhouse                                  │ Spreading The Disease                      │ Anthrax   │
│    2428036 │ Antisocial                                │ Madhouse: The Very Best Of Anthrax         │ Anthrax   │
│    1104106 │ Bring The Noise                           │ Attack Of The Killer B's                   │ Anthrax   │
│ 1483825242 │ The Unforgiven (Remastered 2021)          │ Metallica (Remastered 2021)                │ Metallica │
│   65690440 │ Angel Of Death                            │ Reign In Blood (Expanded)                  │ Slayer    │
│    3088984 │ A Tout Le Monde (Remastered 2004)         │ Youthanasia (Expanded Edition -            │ Megadeth  │
│            │                                           │ Remastered)                                │           │
│ 1483825212 │ Enter Sandman (Remastered 2021)           │ Metallica (Remastered 2021)                │ Metallica │
│ 1483825282 │ Nothing Else Matters (Remastered 2021)    │ Metallica (Remastered 2021)                │ Metallica │
│   61382107 │ Symphony Of Destruction (Remastered 2012) │ Countdown To Extinction (Deluxe Edition -  │ Megadeth  │
│            │                                           │ Remastered)                                │           │
└────────────┴───────────────────────────────────────────┴────────────────────────────────────────────┴───────────┘
```

> 💡 You may adapt the `--limit 10` option to have more or less tracks
> per-artist (defaults to `10`).

Guess what? You can have more magic by generating a "deep mix" 🪄

```sh
onzr mix --deep --limit 4 Metallica Slayer Megadeth Anthrax
```

Hello serendipity 🎉

```
                                                  Onzr Mix tracks
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃        ID ┃ Track                                 ┃ Album                                 ┃ Artist              ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 131294228 │ Dread and the Fugitive Mind           │ The World Needs a Hero                │ Megadeth            │
│   2114258 │ Cyanide                               │ Death Magnetic                        │ Metallica           │
│ 651517892 │ Native Blood                          │ Dark Roots of Earth                   │ Testament           │
│  70877852 │ TNT                                   │ Graveyard Classics                    │ Six Feet Under      │
│    662875 │ Mouth for War                         │ Vulgar Display of Power               │ Pantera             │
│  65724648 │ Silent Scream (Album Version)         │ South Of Heaven                       │ Slayer              │
│   2114578 │ Am I Evil?                            │ Garage Inc.                           │ Metallica           │
│   1055986 │ How Will I Laugh Tomorrow (Album      │ How Will I Laugh Tomorrow When I      │ Suicidal Tendencies │
│           │ Version)                              │ Can't Even Smile Today                │                     │
│   2814112 │ Pull Me Under                         │ Images and Words                      │ Dream Theater       │
│  65690439 │ Payback                               │ God Hates Us All                      │ Slayer              │
│ 668788462 │ Evil Twin                             │ For All Kings                         │ Anthrax             │
│ 668785432 │ Down for Life                         │ The Gathering                         │ Testament           │
│   7754497 │ Brotherhood Of Man                    │ The World Is Yours                    │ Motörhead           │
│   3089037 │ Sweating Bullets (Remastered 2004)    │ Countdown To Extinction (Expanded     │ Megadeth            │
│           │                                       │ Edition - Remastered)                 │                     │
│ 651518372 │ The Devil You Know                    │ Worship Music                         │ Anthrax             │
│ 136332688 │ The Four Horsemen (Remastered)        │ Kill 'Em All (Remastered)             │ Metallica           │
└───────────┴───────────────────────────────────────┴───────────────────────────────────────┴─────────────────────┘
```

As expected, you can pipe your mix with the `--ids` flag to the `add` command:

```sh
onzr mix --ids --deep --limit 4 Metallica Slayer Megadeth Anthrax | \
    onzr add -
```

### `add`

The `add` allows you to add tracks to the queue. Tracks identifiers should be
given as command arguments:

```sh
onzr add 4952889 4952964 15347301
```

> This command adds 3 tracks to the queue.

As already seen, you can read track identifiers from the standard input by
using the `-` special identifier:

```sh
onzr search --track "all along the watchtower" --ids | \
    onzr add -
```

> This command adds a track search result to the queue.

### `queue`

The `queue` command list tracks added to the queue:

```sh
onzr queue
```

### `clear`

The `clear` command stops the player and removes all tracks from the queue:

```sh
onzr clear
```

### `now`

The `onzr now` command gives you details about the track being currently played:

```sh
onzr now
```

You can follow tracks being played in live using the `-f` option:

```sh
onzr now -f
```

> 💡 Hit `CTRL+C` to kill the command and restore your shell prompt.

### `play`

The `play` command does what it says: it (re-)starts playing queued tracks.

```sh
# Clear the queue, add tracks to the queue and starts playing
onzr search --artist "Go go penguin" --ids | \
    head -n 1 | \
    onzr artist --ids - | \
    onzr add - && \
    onzr play
```

> This command plays "Go go penguin" top tracks; considering an empty queue
> before starting the command.

Considering you have already queued tracks, you can start playing a track in
the queue given its rank (1-based numbering):

```sh
onzr play --rank 2
```

> 💡 You can get the track rank by listing queued tracks using the `onzr queue`
> command.

### `pause`

The `pause` command toggles the player pause state:

```sh
onzr pause
```

### `stop`

The `stop` command stops the player:

```sh
onzr stop
```

### `next`

The `next` command plays the next track in queue:

```sh
onzr next
```

> 💡 It has no effect if you reach the end of the queue.

### `previous`

The `previous` command plays the previous track in queue:

```sh
onzr previous
```

> 💡 It has no effect if you reach the beginning of the queue.

### `state`

The `state` command gives you info about the server (player and queue) state:

```sh
onzr state
```

### `version`

The `version` command is useful to know which version of Onzr you are running:

```sh
onzr version
```

## Quick hacking guide (for developers)

Install dependencies in a working environment:

```sh
make bootstrap
```

Run linters:

```sh
make lint
```

Run tests:

```sh
make test
```

> 💡 Don't be surprised to ear strange noises during tests execution 😅

## License

This work is released under the MIT License.
