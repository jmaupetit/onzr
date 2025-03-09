"""Onzr: command line interface."""

from typing_extensions import Annotated

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from .core import Onzr
from .deezer import StreamQuality

cli = typer.Typer(name="onzr", no_args_is_help=True, pretty_exceptions_short=True)
console = Console()

def start() -> Onzr:
    """Start onzr."""
    console.print("🚀 login in to Deezer…", style="cyan")
    return Onzr()

@cli.command()
def search(
    artist: str = "",
    album: str = "",
    track: str = "",
    strict: bool = False,
):
    """Search track, artist and/or album."""
    onzr = start()
    console.print("🔍 start searching…")
    response = onzr.deezer.api.advanced_search(
        artist=artist, album=album, track=track, strict=strict
    )

    table = Table(title="Search matches")
    table.add_column("Track (ID)", justify="right")
    table.add_column("Artist", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Album (ID)", justify="right")
    table.add_column("Album", style="green")

    for match in response["data"]:
        table.add_row(
            str(match.get("id")),
            match.get("artist").get("name"),
            match.get("title"),
            str(match.get("album").get("id")),
            match.get("album").get("title"),
        )

    console.print(table)


@cli.command()
def play(track_id: str, quality: StreamQuality = StreamQuality.MP3_128):
    """Play one (or more) tracks."""
    onzr = start()
    console.print("▶️  starting the player…")
    onzr.play(track_id, quality)
    typer.exit()
