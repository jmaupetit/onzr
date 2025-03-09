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
def search(
    artist: str = "",
    album: str = "",
    track: str = "",
    strict: bool = False,
    quiet: bool = False,
    ids: bool = False,
):
    """Search track, artist and/or album."""
    onzr = start(fast=True, quiet=quiet)
    if not quiet:
        console.print("🔍 start searching…")

    tracks = onzr.deezer.search(artist, album, track, strict)

    if not tracks:
        typer.Exit(code=1)

    if ids:
        # We want to print raw output
        for match in tracks:
            console.print(match.track_id)
        return

    table = Table(title="Search matches")
    table.add_column("Track (ID)", justify="right")
    table.add_column("Album (ID)", justify="right")
    table.add_column("Artist", style="cyan")
    table.add_column("Album", style="green")
    table.add_column("Title", style="magenta")

    for match in tracks:
        table.add_row(
            match.track_id,
            match.album_id,
            match.artist,
            match.album,
            match.title,
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
