"""Onzr: command line interface."""

import logging
from datetime import date
from enum import IntEnum
from pathlib import Path
from random import shuffle
from threading import Thread
from typing import List, cast

import click
import typer
from dynaconf import loaders
from pynput import keyboard
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt
from rich.table import Table

from .config import SECRETS_FILE, SETTINGS_FILE, get_onzr_dir, get_settings
from .core import Onzr
from .deezer import AlbumShort, ArtistShort, Collection, StreamQuality, TrackShort

FORMAT = "%(message)s"
logging_console = Console(stderr=True)
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(console=logging_console)],
)

cli = typer.Typer(name="onzr", no_args_is_help=True, pretty_exceptions_short=True)
console = Console()
logger = logging.getLogger(__name__)


class ExitCodes(IntEnum):
    """data7 exit codes."""

    OK = 0
    INCOMPLETE_CONFIGURATION = 10
    INVALID_CONFIGURATION = 11
    INVALID_ARGUMENTS = 20
    NOT_FOUND = 30


def start(fast: bool = False, quiet: bool = False) -> Onzr:
    """Start onzr."""
    if not quiet:
        console.print("🚀 login in to Deezer…", style="cyan")
    return Onzr(fast=fast)


def print_collection_ids(collection: Collection):
    """Print a collection as ids."""
    for item in collection:
        console.print(item.id)


def print_collection_table(collection: Collection, title="Collection"):
    """Print a collection as a table."""
    table = Table(title=title)

    sample = collection[0]
    show_artist = (
        True
        if isinstance(sample, TrackShort)
        or isinstance(sample, AlbumShort)
        or isinstance(sample, ArtistShort)
        else False
    )
    show_album = (
        True
        if isinstance(sample, TrackShort) or isinstance(sample, AlbumShort)
        else False
    )
    show_track = True if isinstance(sample, TrackShort) else False
    show_release = (
        True if isinstance(sample, AlbumShort) and sample.release_date else False
    )
    logger.debug(f"{show_artist=} - {show_album=} - {show_track=}")

    if show_track:
        table.add_column("ID", justify="right")
        table.add_column("Track", style="#9B6BDF")
    if show_album:
        table.add_column("ID", justify="right")
        table.add_column("Album", style="#E356A7")
    if show_release:
        table.add_column("Released")
    if show_artist:
        table.add_column("ID", justify="right")
        table.add_column("Artist", style="#75D7EC")

    # Sort albums by release date
    if isinstance(collection[0], AlbumShort):
        collection = cast(
            Collection,
            sorted(
                collection,
                key=lambda i: date.fromisoformat(i.release_date),
                reverse=True,
            ),
        )

    for item in collection:
        table.add_row(*item.to_list())

    console.print(table)


@cli.command()
def init(reset: bool = False):
    """Intialize onzr player."""
    console.print("⚙️ Initializing onzr…")

    app_dir = get_onzr_dir()
    module_dir = Path(__file__).parent

    # Create Onzr config directory if needed
    logger.debug(f"Creating application directory: {app_dir}")
    app_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    # Copy original dist
    logger.debug("Will copy distributed configurations…")
    for setting_file in [SECRETS_FILE, SETTINGS_FILE]:
        src = module_dir / setting_file.with_suffix(".toml.dist")
        dest = app_dir / setting_file
        logger.debug(f"{src=} -> {dest=}")

        if dest.exists():
            logger.info(f"Setting file '{setting_file}' already exists.")
            continue
        dest.write_text(src.read_text())
        logger.debug(f"Copied setting file: {setting_file}")

    # Set ARL value
    settings = get_settings()
    try:
        arl = settings.ARL
    except AttributeError:
        arl = None

    if arl is None or reset:
        logger.debug("ARL value will be (re)set.")
        arl = Prompt.ask("Paste your ARL 📋")
        secrets_file = app_dir / SECRETS_FILE

        logger.info(f"Writing secrets configuration: {secrets_file}")
        loaders.write(str(secrets_file), {"ARL": arl}, merge=True)

    console.print("🎉 Everything looks ok from here. You can start playing 💫")


@cli.command()
def search(  # noqa: PLR0913
    artist: str = "",
    album: str = "",
    track: str = "",
    strict: bool = False,
    quiet: bool = False,
    ids: bool = False,
):
    """Search track, artist and/or album."""
    if ids:
        quiet = True
    onzr = start(fast=True, quiet=quiet)
    if not quiet:
        console.print("🔍 start searching…")

    results = onzr.deezer.search(artist, album, track, strict)

    if not results:
        console.print("No match found.")
        raise typer.Exit(code=ExitCodes.NOT_FOUND)

    if ids:
        print_collection_ids(results)
        return

    print_collection_table(results, title="Search results")


@cli.command()
def artist(  # noqa: PLR0913
    artist_id: str,
    top: bool = True,
    radio: bool = False,
    albums: bool = False,
    limit: int = 10,
    quiet: bool = False,
    ids: bool = False,
):
    """Get artist popular track ids."""
    if all([not top, not radio, not albums]):
        console.print("You should choose either top titles, artist radio or albums.")
        raise typer.Exit(code=ExitCodes.INVALID_ARGUMENTS)
    elif albums:
        top = False
        radio = False

    if ids:
        quiet = True

    if artist_id == "-":
        logger.debug("Reading artist id from stdin…")
        artist_id = click.get_text_stream("stdin").read().strip()
        logger.debug(f"{artist_id=}")

    onzr = start(fast=True, quiet=quiet)
    collection = onzr.deezer.artist(
        artist_id, radio=radio, top=top, albums=albums, limit=limit
    )

    if ids:
        print_collection_ids(collection)
        return

    print_collection_table(collection, title="Artist collection")


@cli.command()
def album(
    album_id: str,
    quiet: bool = False,
    ids: bool = False,
):
    """Get album track ids."""
    if ids:
        quiet = True

    if album_id == "-":
        logger.debug("Reading artist id from stdin…")
        album_id = click.get_text_stream("stdin").read().strip()
        logger.debug(f"{album_id=}")

    onzr = start(fast=True, quiet=quiet)
    collection = onzr.deezer.album(album_id)

    if ids:
        print_collection_ids(collection)
        return

    print_collection_table(collection, title="Album tracks")


@cli.command()
def mix(
    artist: list[str],
    deep: bool = False,
    limit: int = 10,
    quiet: bool = False,
    ids: bool = False,
):
    """Create a playlist from multiple artists."""
    if ids:
        quiet = True

    onzr = start(fast=True, quiet=quiet)
    tracks: List[TrackShort] = []

    if not quiet:
        console.print("🍪 cooking the mix…")

    for artist_ in artist:
        result = onzr.deezer.search(artist_, strict=True)
        # We expect the search engine to be relevant 🤞
        artist_id = result[0].id
        tracks += cast(
            List[TrackShort],
            onzr.deezer.artist(artist_id, radio=deep, top=True, limit=limit),
        )
    shuffle(tracks)

    if ids:
        print_collection_ids(tracks)
        return

    print_collection_table(tracks, title="Onzr Mix tracks")


@cli.command()
def play(
    track_ids: List[str],
    quality: StreamQuality = StreamQuality.MP3_128,
    shuffle: bool = False,
):
    """Play one (or more) tracks."""
    onzr = start()
    console.print("🚀 starting the player…")
    if track_ids == ["-"]:
        logger.debug("Reading track ids from stdin…")
        track_ids = click.get_text_stream("stdin").read().split()
        logger.debug(f"{track_ids=}")
    onzr.add(track_ids, quality)
    if shuffle:
        onzr.shuffle()

    # Start playing in a new thread
    thread = Thread(target=onzr.play)
    thread.start()

    # Controls
    def on_press(key: keyboard.Key):
        """Player control actions."""
        match key:
            case keyboard.Key.media_play_pause:
                onzr.pause()

    with keyboard.Listener(on_press=on_press) as listener:  # type: ignore[arg-type]
        listener.join()

    raise typer.Exit()
