"""Onzr: command line interface."""

import logging
from typing import List

import click
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from .core import Onzr
from .deezer import StreamQuality

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


def start(fast: bool = False, quiet: bool = False) -> Onzr:
    """Start onzr."""
    if not quiet:
        console.print("🚀 login in to Deezer…", style="cyan")
    return Onzr(fast=fast)


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
        typer.Exit(code=1)

    sample = results[0]
    show_artist = True if sample.artist else False
    show_album = True if sample.album else False
    show_track = True if sample.title else False

    search_ids = [r.track_id for r in results]
    if not show_track:
        if show_artist:
            search_ids = [r.artist_id for r in results]
        elif show_album:
            search_ids = [r.album_id for r in results]

    if ids:
        # We want to print raw output
        for search_id in search_ids:
            console.print(search_id)
        return

    table = Table(title="Search matches")
    if show_artist:
        table.add_column("ID", justify="right")
        table.add_column("Artist", style="cyan")
    if show_album:
        table.add_column("ID", justify="right")
        table.add_column("Album", style="green")
    if show_track:
        table.add_column("ID", justify="right")
        table.add_column("Title", style="magenta")


    for match in results:
        table.add_row(
            *list(
                filter(
                    None,
                    [
                        match.artist_id,
                        match.artist,
                        match.album_id,
                        match.album,
                        match.track_id,
                        match.title,
                    ],
                )
            )
        )

    console.print(table)


@cli.command()
def play(track_ids: List[str], quality: StreamQuality = StreamQuality.MP3_128):
    """Play one (or more) tracks."""
    onzr = start()
    console.print("▶️ starting the player…")
    if track_ids == ["-"]:
        logger.debug("Reading track ids from stdin…")
        track_ids = click.get_text_stream("stdin").read().split()
        logger.debug(f"{track_ids=}")
    onzr.add(track_ids, quality)
    onzr.play()
    typer.Exit()
