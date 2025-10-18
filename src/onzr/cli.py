"""Onzr: command line interface."""

import json
import logging
import sys
import time
from datetime import date
from enum import IntEnum
from functools import cache
from importlib.metadata import version as import_lib_version
from pathlib import Path
from random import shuffle
from typing import List, cast

import click
import pendulum
import typer
import uvicorn
import yaml
from pydantic import PositiveInt
from rich.console import Console, Group
from rich.live import Live
from rich.logging import RichHandler
from rich.progress_bar import ProgressBar
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from typing_extensions import Annotated
from uvicorn.config import LOG_LEVELS

from onzr.exceptions import OnzrConfigurationError

from .client import OnzrClient
from .config import (
    SETTINGS_FILE,
    get_onzr_dir,
    get_settings,
)
from .deezer import DeezerClient
from .models import (
    AlbumShort,
    ArtistShort,
    Collection,
    PlayerControl,
    ServerState,
    TrackShort,
)

FORMAT = "%(message)s"
logging_console = Console(stderr=True)
logging_config = {
    "level": logging.INFO,
    "format": FORMAT,
    "datefmt": "[%X]",
    "handlers": [RichHandler(console=logging_console)],
}
logging.basicConfig(**logging_config)  # type: ignore[arg-type]

cli = typer.Typer(name="onzr", no_args_is_help=True, pretty_exceptions_short=True)
console = Console()
logger = logging.getLogger(__name__)


@cache
def get_theme():
    """Get Onzr theme."""
    return get_settings().THEME


class ExitCodes(IntEnum):
    """Onzr exit codes."""

    OK = 0
    INCOMPLETE_CONFIGURATION = 10
    INVALID_CONFIGURATION = 11
    INVALID_ARGUMENTS = 20
    NOT_FOUND = 30


def get_deezer_client(quiet: bool = False) -> DeezerClient:
    """Get Deezer client for simple API queries."""
    settings = get_settings()

    if not quiet:
        console.print("🚀 login in to Deezer…", style="cyan")

    return DeezerClient(
        arl=settings.ARL,
        blowfish=settings.DEEZER_BLOWFISH_SECRET,
        fast=True,
    )


def print_collection_ids(collection: Collection):
    """Print a collection as ids."""
    for item in collection:
        console.print(item.id)


def print_collection_table(collection: Collection, title="Collection"):
    """Print a collection as a table."""
    theme = get_theme()
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
    show_release = True if isinstance(sample, AlbumShort) else False
    logger.debug(f"{show_artist=} - {show_album=} - {show_track=}")

    table.add_column("ID", justify="right")
    if show_track:
        table.add_column("Track", style=theme.title_color.as_hex())
    if show_album:
        table.add_column("Album", style=theme.album_color.as_hex())
    if show_artist:
        table.add_column("Artist", style=theme.artist_color.as_hex())
    if show_release:
        table.add_column("Released")

    # Sort albums by release date
    # FIXME: mypy does not get that we are dealing with a List[AlbumShort] collection
    if isinstance(sample, AlbumShort):
        albums_with_release_date = set(
            filter(lambda x: x.release_date is not None, collection)  # type: ignore[attr-defined]
        )
        albums_without_release_date = list(set(collection) - albums_with_release_date)
        collection = sorted(
            albums_with_release_date,
            key=lambda i: date.fromisoformat(i.release_date),  # type: ignore[attr-defined]
            reverse=True,
        )  # type: ignore[assignment]
        collection.extend(albums_without_release_date)  # type: ignore[arg-type]

    for item in collection:
        table.add_row(*map(str, item.model_dump().values()))

    console.print(table)


@cli.command()
def init():
    """Intialize onzr player."""
    console.print("⚙️ Initializing onzr…")

    app_dir = get_onzr_dir()
    module_dir = Path(__file__).parent

    # Create Onzr config directory if needed
    logger.debug(f"Creating application directory: {app_dir}")
    app_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    # Copy original dist
    logger.debug("Will copy distributed configurations…")
    src = module_dir / SETTINGS_FILE.with_suffix(".yaml.dist")
    dest = app_dir / SETTINGS_FILE
    logger.debug(f"{src=} -> {dest=}")

    if dest.exists():
        raise OnzrConfigurationError(f"Configuration file '{dest}' already exists!")

    logger.info(f"Will create base setting file '{dest}'")
    dest.write_text(src.read_text())
    logger.debug(f"Copied base setting file to: {dest}")

    # Open base configuration
    with src.open() as f:
        user_settings = yaml.safe_load(f)

    logger.debug("ARL value will be (re)set.")
    user_settings["ARL"] = Prompt.ask("Paste your ARL 📋")

    logger.info(f"Writing settings configuration to: {dest}")
    with dest.open(mode="w") as f:
        yaml.dump(user_settings, f)

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
    deezer = get_deezer_client(quiet=quiet)

    if not quiet:
        console.print("🔍 start searching…")
    results = deezer.search(artist, album, track, strict)

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

    deezer = get_deezer_client(quiet=quiet)
    collection = deezer.artist(
        int(artist_id), radio=radio, top=top, albums=albums, limit=limit
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

    deezer = get_deezer_client(quiet=quiet)
    collection = deezer.album(int(album_id))

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

    deezer = get_deezer_client(quiet=quiet)
    tracks: List[TrackShort] = []

    if not quiet:
        console.print("🍪 cooking the mix…")

    for artist_ in artist:
        result = deezer.search(artist_, strict=True)
        # We expect the search engine to be relevant 🤞
        artist_id = result[0].id
        tracks += cast(
            List[TrackShort],
            deezer.artist(artist_id, radio=deep, top=True, limit=limit),
        )
    shuffle(tracks)

    if ids:
        print_collection_ids(tracks)
        return

    print_collection_table(tracks, title="Onzr Mix tracks")


@cli.command()
def add(track_ids: List[str]):
    """Add one (or more) tracks to the queue."""
    if track_ids == ["-"]:
        logger.debug("Reading track ids from stdin…")
        track_ids = click.get_text_stream("stdin").read().split()
        logger.debug(f"{track_ids=}")

    console.print("➕ Adding tracks to queue…")

    client = OnzrClient()
    response = client.queue_add(track_ids)

    console.print(f"✅ {response.message}")


def _client_request(name: str, **kwargs):
    """A generic wrapper that executes a client method."""
    client = OnzrClient()
    method = getattr(client, name)
    response = method(**kwargs)
    return response


@cli.command()
def queue():
    """List queue tracks."""
    theme = get_theme()
    queue = _client_request("queue_list")
    if not len(queue):
        console.print(
            "⚠ [yellow]Queue is empty, use [magenta]onzr add[/magenta] "
            "to start adding tracks.[/yellow]"
        )
        raise typer.Exit(0)

    with console.pager(styles=True):
        for qt in queue.tracks:
            track_infos = (
                f"[white][bold]{qt.position + 1:-3d}[/] "
                f"[{theme.title_color}]{qt.track.title}[white] - "
                f"[{theme.artist_color}]{qt.track.artist} "
                f"[{theme.album_color}]({qt.track.album})"
            )
            if queue.playing is not None and qt.position < queue.playing:
                s = f"🏁 [italic]{track_infos}[/italic]"
            elif qt.current:
                s = f"▶  [bold]{track_infos}[/bold]"
            else:
                s = f"🧵 {track_infos}"
            s += "[white]"
            console.print(s)


def _print_server_state(state: ServerState):
    """Print server state."""
    theme = get_theme()
    playing = state.queue.playing + 1 if state.queue.playing is not None else None
    s = (
        "📢 "
        f"Player: [{theme.secondary_color}]{state.player.split('.')[1]}[white]"
        " · "
        f"Queue: [{theme.tertiary_color}]{playing}[white]"
        " / "
        f"[{theme.primary_color}]{state.queue.queued}[white]"
    )
    console.print(s)


def _print_player_control(control: PlayerControl):
    """Print player control action."""
    theme = get_theme()
    match control.action:
        case "play":
            icon = "▶️"
        case "pause":
            icon = "⏯️"
        case "stop":
            icon = "⏹️"
        case "next":
            icon = "⏭"
        case "previous":
            icon = "⏮"
        case _:
            icon = "⁉️"
    console.print(f"{icon}  Action: [{theme.secondary_color}]{control.action}[white] ")
    _print_server_state(control.state)


@cli.command()
def clear():
    """Empty queue."""
    state = _client_request("queue_clear")
    _print_server_state(state)


@cli.command()
def now(follow: Annotated[bool, typer.Option("--follow", "-f")] = False):
    """Get info about now playing track."""
    client = OnzrClient()
    theme = get_theme()

    def timecode(duration: pendulum.Duration) -> str:
        """Convert a duration (in ms) to a time code."""
        return (
            f"{duration.hours:02d}:"
            f"{duration.minutes:02d}:"
            f"{duration.remaining_seconds:02d}"
        )

    def get_track_infos(track: TrackShort) -> str:
        """Generate a fully qualified track string."""
        return (
            f"[{theme.title_color}]{track.title} - "
            f"[{theme.artist_color}]{track.artist} - "
            f"[{theme.album_color}]{track.album}"
        )

    def display() -> Group:
        """Now playing."""
        now_playing = client.now_playing()
        queue = client.queue_list()
        track = now_playing.track
        player = now_playing.player
        next_track = (
            queue.tracks[queue.playing + 1].track
            if queue.playing is not None and queue.playing < len(queue) - 1
            else None
        )

        match player.state:
            case "State.Playing":
                icon = "▶️"
            case "State.Paused":
                icon = "⏯️"
            case "State.Stopped":
                icon = "⏹️"
            case "State.Ended":
                icon = "🏁"
            case "State.NothingSpecial":
                icon = "🤷"
            case "State.Opening":
                icon = "📂"
            case "State.Buffering":
                icon = "🌐"
            case _:
                icon = "⁉️"

        track_infos = f"{icon} "
        if track is not None:
            track_infos += get_track_infos(track)
        track_infos += (
            "[white] · "
            f"({queue.playing + 1 if queue.playing is not None else '-'}/{len(queue)})"
        )
        track_duration = pendulum.duration(seconds=player.length / 1000.0)
        track_played = pendulum.duration(seconds=player.time / 1000.0)
        track_played_timecode = Text(
            f"{timecode(track_played)} ", style=theme.secondary_color.as_hex(), end=""
        )
        track_total_timecode = f" [{theme.primary_color}]{timecode(track_duration)}"
        progress_bar = ProgressBar(
            total=player.length,
            completed=player.time,
            complete_style=theme.tertiary_color.as_hex(),
            finished_style=theme.secondary_color.as_hex(),
            width=62,
        )
        coming_next = "Next: "
        if next_track is not None:
            coming_next += get_track_infos(next_track)
        else:
            coming_next += "❎ [italic]Nothing more has been queued[/italic]"

        return Group(
            track_infos,
            track_played_timecode,
            progress_bar,
            track_total_timecode,
            coming_next,
        )

    if not follow:
        console.print(display())
        return

    with Live(display(), refresh_per_second=4) as live:
        while True:
            time.sleep(0.1)
            live.update(display())


@cli.command()
def play(rank: PositiveInt | None = None):
    """Play queue."""
    theme = get_theme()
    if rank is not None and rank < 1:
        console.print(
            (
                "🙈 "
                f"[{theme.alert_color} bold]Invalid rank![/{theme.alert_color} bold] "
                "It should be greater than 0."
            )
        )
        raise typer.Exit(ExitCodes.INVALID_ARGUMENTS)
    control = _client_request("play", rank=rank - 1 if rank else None)
    _print_player_control(control)


@cli.command()
def pause():
    """Pause/resume playing."""
    control = _client_request("pause")
    _print_player_control(control)


@cli.command()
def stop():
    """Stop playing queue."""
    control = _client_request("stop")
    _print_player_control(control)


@cli.command()
def next():
    """Play next track in queue."""
    control = _client_request("next")
    _print_player_control(control)


@cli.command()
def previous():
    """Play previous track in queue."""
    control = _client_request("previous")
    _print_player_control(control)


@cli.command()
def serve(
    host: str = "localhost",
    port: int = 9473,
    log_level: str = "info",
):
    """Run onzr http server."""
    theme = get_theme()
    # Typer does not support complex types such as Litteral, so let's check log_level
    # validity by ourselves.
    allowed_levels: list[str] = ["debug", "info", "warning", "error", "critical"]
    if log_level not in allowed_levels:
        console.print(
            (
                "🙈 "
                f"[{theme.alert_color} bold]"
                "Forbidden log-level!"
                f"[/{theme.alert_color} bold] "
                f"Should be in: {allowed_levels}"
            )
        )
        raise typer.Exit(ExitCodes.INVALID_ARGUMENTS)

    level = LOG_LEVELS[log_level]
    logging_config.update({"level": level})
    logging.basicConfig(**logging_config, force=True)  # type: ignore[arg-type]

    settings = get_settings()
    config = uvicorn.Config(
        "onzr.server:app",
        host=host or settings.HOST,
        port=port or settings.PORT,
        log_level=level,
    )
    server = uvicorn.Server(config)
    server.run()


@cli.command()
def state():
    """Get server state."""
    client = OnzrClient()
    state = client.state()
    _print_server_state(state)


@cli.command()
def version():
    """Get program version."""
    theme = get_theme()
    console.print(
        f"🔖 Version: [{theme.secondary_color}]{import_lib_version('onzr')}[white]"
    )


@cli.command()
def openapi():
    """Get Onzr HTTP API OpenAPI schema."""
    from onzr.server import app

    sys.stdout.write(f"{json.dumps(app.openapi())}\n")
