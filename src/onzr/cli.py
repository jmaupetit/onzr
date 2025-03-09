"""Onzr: command line interface."""

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from .core import Onzr
from .deezer import StreamQuality

cli = typer.Typer(name="onzr", no_args_is_help=True, pretty_exceptions_short=True)
console = Console()


def start(fast: bool = False) -> Onzr:
    """Start onzr."""
    console.print("🚀 login in to Deezer…", style="cyan")
    return Onzr(fast=fast)


@cli.command()
def search(
    artist: str = "",
    album: str = "",
    track: str = "",
    strict: bool = False,
):
    """Search track, artist and/or album."""
    onzr = start(fast=True)
    console.print("🔍 start searching…")

    tracks = onzr.deezer.search(artist, album, track, strict)

    if not tracks:
        typer.Exit(code=1)

    table = Table(title="Search matches")
    table.add_column("Track (ID)", justify="right")
    table.add_column("Artist", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Album", style="green")
    table.add_column("Album (ID)", justify="right")

    for match in tracks:
        table.add_row(
            match.track_id,
            match.artist,
            match.title,
            match.album,
            match.album_id,
        )

    console.print(table)


@cli.command()
def play(track_id: str, quality: StreamQuality = StreamQuality.MP3_128):
    """Play one (or more) tracks."""
    onzr = start()
    console.print("▶️  starting the player…")
    onzr.play(track_id, quality)
    typer.Exit()
