"""Onzr: command line interface."""

import json
import logging
import logging.config
import os
import re
import select
import sys
import termios
import time
import tty
from contextlib import AbstractContextManager, contextmanager, nullcontext
from enum import IntEnum
from functools import cache, wraps
from importlib.metadata import version as import_lib_version
from itertools import chain
from operator import attrgetter
from pathlib import Path
from random import shuffle
from typing import Callable, Iterable, Iterator, List, NoReturn, Optional, Set, cast

import click
import pendulum
import typer
import uvicorn
import yaml
from rich.console import Console, Group
from rich.live import Live
from rich.progress_bar import ProgressBar
from rich.prompt import Prompt
from rich.segment import Segments
from rich.syntax import Syntax
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
from .deezer import AlbumSortBy, DeezerClient, TrackSortBy
from .models.core import (
    AlbumShort,
    ArtistShort,
    Collection,
    CollectionItem,
    PlayerControl,
    PlaylistShort,
    ServerState,
    TrackShort,
)

FORMAT = "%(message)s"
logging_console = Console(stderr=True)
logging_config = {
    "version": 1,
    "level": logging.INFO,
    "format": FORMAT,
    "datefmt": "[%X]",
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "console": logging_console,
        }
    },
}
logging.config.dictConfig(logging_config)

cli = typer.Typer(name="onzr", no_args_is_help=True, pretty_exceptions_short=True)
my = typer.Typer(name="my", no_args_is_help=True, pretty_exceptions_short=True)
cli.add_typer(my, name="my", help="Explore your 💜 library.")
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
    SERVER_DOWN = 40


def get_deezer_client(quiet: bool = False) -> DeezerClient:
    """Get Deezer client for simple API queries."""
    settings = get_settings()

    if not quiet:
        console.print("🚀 login in to Deezer…", style="cyan")

    return DeezerClient(
        arl=settings.ARL,
        blowfish=settings.DEEZER_BLOWFISH_SECRET,
        fast=True,
        connection_pool_maxsize=settings.CONNECTION_POOL_MAXSIZE,
        always_fetch_release_date=settings.ALWAYS_FETCH_RELEASE_DATE,
    )


def require_server(func):
    """A command decorator that tests if Onzr server is running."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        client = OnzrClient()
        theme = get_theme()
        if not client.ping():
            console.print(
                f"[{theme.alert_color}]❌ "
                "Onzr server is down, run `onzr serve` first."
                f"[/{theme.alert_color}]"
            )
            raise typer.Exit(ExitCodes.SERVER_DOWN)
        func(*args, **kwargs)

    return wrapper


def print_collection_ids(collection: Iterable[CollectionItem]):
    """Print a collection as ids."""
    for item in collection:
        console.print(item.id)


@contextmanager
def pager() -> Iterator[None]:
    """Page console output, keeping colors.

    The default pager (`less`) displays color codes as-is unless the `-R` flag is
    set: use it when the user did not configure their pager (`PAGER` or `LESS`).
    """
    configured = "PAGER" in os.environ or "LESS" in os.environ
    if not configured:
        os.environ["LESS"] = "-R"
    try:
        with console.pager(styles=True):
            yield
    finally:
        if not configured:
            del os.environ["LESS"]


def progress(message: str, quiet: bool = False) -> AbstractContextManager:
    """Display a progress status on stderr (unless quiet).

    The status is displayed on stderr so that stdout stays clean (pager, ids).
    """
    return nullcontext() if quiet else logging_console.status(message)


def exit_not_found(message: str, quiet: bool = False) -> NoReturn:
    """Print a "not found" message (unless quiet) and exit."""
    if not quiet:
        theme = get_theme()
        console.print(f"❌ [{theme.alert_color}]{message}[/{theme.alert_color}]")
    raise typer.Exit(code=ExitCodes.NOT_FOUND)


def print_collection_table(
    collection: Collection, title="Collection", sort: bool = True, quiet: bool = False
):
    """Print a collection as a table."""
    theme = get_theme()
    table = Table(title=title)

    # Copy the collection, as it may be sorted below
    items: List[CollectionItem] = list(collection)
    if not items:
        return
    sample = items[0]
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
        True
        if (isinstance(sample, TrackShort) and sample.release_date is not None)
        or (isinstance(sample, AlbumShort) and sample.release_date is not None)
        else False
    )
    logger.debug(f"{show_artist=} - {show_album=} - {show_track=}")

    table.add_column("#", justify="left")
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
    if isinstance(sample, AlbumShort) and sort:
        albums_with_release_date: Set[AlbumShort] = set(
            filter(attrgetter("release_date"), items)  # type: ignore[arg-type]
        )
        albums_without_release_date: List[AlbumShort] = list(
            cast(Set[AlbumShort], set(items)) - albums_with_release_date
        )
        sorted_collection: List[AlbumShort] = sorted(
            albums_with_release_date,
            key=attrgetter("release_date"),
            reverse=True,
        )
        sorted_collection.extend(albums_without_release_date)
        items = list(sorted_collection)

    if isinstance(sample, PlaylistShort):
        table.add_column("Title", style=theme.title_color.as_hex())
        table.add_column("Public", style="italic")
        table.add_column("# tracks", style="bold")
        table.add_column("User", style=theme.secondary_color.as_hex())

    for rk, item in enumerate(items, start=1):
        table.add_row(
            str(rk),
            *map(str, item.model_dump(exclude_none=True, exclude={"tracks"}).values()),
        )

    # Rendering large tables takes a while (column widths depend on all rows): render
    # while displaying a status, then print the rendered table, so that stdout is not
    # written while the status is displayed.
    min_rows = get_settings().CLI_TABLE_RENDERING_STATUS_MIN_ROWS
    with progress("Rendering table…", quiet or len(items) < min_rows):
        rendered = Segments(list(console.render(table)))
    console.print(rendered)


@cli.command()
def init():
    """Initialize Onzr configuration."""
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
    base_settings = src.read_text()
    dest.write_text(base_settings)
    logger.debug(f"Copied base setting file to: {dest}")

    logger.debug("ARL value will be (re)set.")
    arl = yaml.safe_dump({"ARL": Prompt.ask("Paste your ARL 📋")}).strip()

    # Only set the ARL line to keep commented default settings
    logger.info(f"Writing settings configuration to: {dest}")
    dest.write_text(
        re.sub(r"^# ARL:.*$", lambda _: arl, base_settings, count=1, flags=re.M)
    )

    console.print("🎉 Everything looks ok from here. You can start playing 💫")


@cli.command()
def config(
    path: Annotated[
        bool, typer.Option("--path", "-p", help="Show configuration path and exit.")
    ] = False,
    edit: Annotated[
        bool, typer.Option("--edit", "-e", help="Edit configuration in $EDITOR.")
    ] = False,
):
    """Display or edit Onzr's configuration."""
    user_config_path = get_onzr_dir() / SETTINGS_FILE

    if not user_config_path.exists():
        console.print(
            "[red]Configuration file does not exist, use `onzr init` first.[/red]"
        )
        raise typer.Exit(ExitCodes.INCOMPLETE_CONFIGURATION)

    if path:
        console.print(user_config_path)
        raise typer.Exit(0)

    if edit:
        click.edit(filename=str(user_config_path))
        raise typer.Exit(0)

    with user_config_path.open() as f:
        user_config = f.read()
    console.print(Syntax(user_config, "yaml"))


@cli.command()
def search(
    artist: Annotated[
        str, typer.Option("--artist", "-A", help="Search by artist name.")
    ] = "",
    album: Annotated[
        str, typer.Option("--album", "-a", help="Search by album name.")
    ] = "",
    track: Annotated[
        str, typer.Option("--track", "-t", help="Search by track title.")
    ] = "",
    playlist: Annotated[
        str, typer.Option("--playlist", "-p", help="Search by playlist name.")
    ] = "",
    strict: Annotated[
        bool, typer.Option("--strict", "-s", help="Only consider strict matches.")
    ] = False,
    release: Annotated[
        bool,
        typer.Option("--release", "-R", help="Fetch albums or tracks release date."),
    ] = False,
    first: Annotated[
        bool, typer.Option("--first", "-f", help="Limit to the first match.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Search tracks, artists and/or albums.

    Note that search criteria can be combined (e.g. artist and album).
    """
    if ids:
        quiet = True
    deezer = get_deezer_client(quiet=quiet)

    if not quiet:
        console.print("🔍 start searching…")
    try:
        results = deezer.search(artist, album, track, playlist, strict, release)
    except ValueError as err:
        raise typer.Exit(code=ExitCodes.INVALID_ARGUMENTS) from err

    if not results:
        exit_not_found("No match found", quiet)

    if first:
        results = cast(List[TrackShort], results)[:1]

    if ids:
        print_collection_ids(results)
        return

    print_collection_table(results, title="Search results", quiet=quiet)


@cli.command()
def artist(
    artist_id: str,
    top: Annotated[
        bool, typer.Option("--top/--no-top", "-t/-T", help="Show artist top tracks.")
    ] = True,
    radio: Annotated[
        bool,
        typer.Option("--radio", "-r", help="Show artist-inspired tracks."),
    ] = False,
    albums: Annotated[
        bool, typer.Option("--albums", "-a", help="Show artist albums.")
    ] = False,
    release: Annotated[
        bool,
        typer.Option("--release", "-R", help="Fetch albums or tracks release date."),
    ] = False,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Limit to the first l hits.")
    ] = 10,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get artist top tracks, radio or albums.

    Increase the default limit to list more than 10 albums.
    """
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
        int(artist_id),
        radio=radio,
        top=top,
        albums=albums,
        limit=limit,
        fetch_release_date=release,
    )

    if ids:
        print_collection_ids(collection)
        return

    print_collection_table(collection, title="Artist collection", quiet=quiet)


@cli.command()
def album(
    album_id: str,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get album tracks."""
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

    print_collection_table(collection, title="Album tracks", quiet=quiet)


@cli.command()
def playlist(
    playlist_id: str,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get playlist tracks."""
    if ids:
        quiet = True

    if playlist_id == "-":
        logger.debug("Reading playlist id from stdin…")
        playlist_id = click.get_text_stream("stdin").read().strip()
        logger.debug(f"{playlist_id=}")

    deezer = get_deezer_client(quiet=quiet)
    playlist = deezer.playlist(int(playlist_id))

    if playlist.tracks is None:
        console.print("This playlist contains no tracks")
        raise typer.Exit(code=ExitCodes.INVALID_ARGUMENTS)

    if ids:
        print_collection_ids(playlist.tracks)
        return

    print_collection_table(
        playlist.tracks,
        title=f"« {playlist.title} » by {playlist.user or '?'}",
        quiet=quiet,
    )


@cli.command()
def mix(
    artist: list[str],
    deep: Annotated[
        bool,
        typer.Option(
            "--deep", "-d", help="Create a mix with related artists (like a radio)."
        ),
    ] = False,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Limit to the first l hits per artist.")
    ] = 10,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
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
        artist_id = cast(List[ArtistShort], result)[0].id
        tracks += cast(
            List[TrackShort],
            deezer.artist(artist_id, radio=deep, top=True, limit=limit),
        )
    shuffle(tracks)

    if ids:
        print_collection_ids(tracks)
        return

    print_collection_table(tracks, title="Onzr Mix tracks", quiet=quiet)


@my.command("playlists")
def my_playlists(
    private: Annotated[
        bool, typer.Option("--private", "-p", help="Restrict to private playlists.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get your playlists."""
    if ids:
        quiet = True

    deezer = get_deezer_client(quiet=quiet)

    playlists = deezer.user_playlists(private)
    if not playlists:
        exit_not_found(
            "No private playlists found" if private else "No playlists found", quiet
        )

    if ids:
        print_collection_ids(playlists)
        return

    with pager():
        print_collection_table(
            playlists, title=f"{deezer.user.name}'s playlists", quiet=quiet
        )


@my.command("artists")
def my_artists(
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get your favorite artists."""
    if ids:
        quiet = True

    deezer = get_deezer_client(quiet=quiet)

    artists = deezer.user_artists()
    if not artists:
        exit_not_found("No favorite artists found", quiet)

    if ids:
        print_collection_ids(artists)
        return

    with pager():
        print_collection_table(
            artists, title=f"{deezer.user.name}'s artists", quiet=quiet
        )


@my.command("albums")
def my_albums(
    by: Annotated[
        AlbumSortBy, typer.Option("--by", "-b", help="Sort by title or artist.")
    ] = AlbumSortBy.TITLE,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get your favorite albums."""
    if ids:
        quiet = True

    deezer = get_deezer_client(quiet=quiet)

    albums = deezer.user_albums(sort_by=by)
    if not albums:
        exit_not_found("No favorite albums found", quiet)

    if ids:
        print_collection_ids(albums)
        return

    with pager():
        print_collection_table(
            albums, title=f"{deezer.user.name}'s albums", sort=False, quiet=quiet
        )


@my.command("tracks")
def my_tracks(
    by: Annotated[
        Optional[TrackSortBy],
        typer.Option(
            "--by",
            "-b",
            help="Sort by album, artist or title (default: most recent first).",
        ),
    ] = None,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Quiet output.")] = False,
    ids: Annotated[
        bool, typer.Option("--ids", "-i", help="Show only result IDs.")
    ] = False,
):
    """Get your favorite tracks."""
    if ids:
        quiet = True

    settings = get_settings()
    deezer = get_deezer_client(quiet=quiet)

    def fetch() -> Iterator[TrackShort]:
        # Sorting fetches all tracks during the call, else tracks are fetched lazily
        return deezer.user_tracks(
            page_size=settings.FAVORITE_SONGS_PAGINATE_BY, sort_by=by
        )

    # Stream ids as soon as they are fetched (unless sorted)
    if ids:
        tracks = fetch()
        # `tracks` is an iterator, always truthy: peek the first track to detect
        # empty collections, and restore it for later consumption.
        if (first := next(tracks, None)) is None:
            exit_not_found("No favorite tracks found", quiet)
        print_collection_ids(chain([first], tracks))
        return

    with progress("Fetching your favorite tracks…", quiet):
        fetched = list(fetch())
    if not fetched:
        exit_not_found("No favorite tracks found", quiet)

    with pager():
        print_collection_table(
            fetched, title=f"{deezer.user.name}'s tracks", sort=False, quiet=quiet
        )


@cli.command()
@require_server
def add(track_ids: List[str]):
    """Add one (or more) tracks to the queue."""
    if track_ids == ["-"]:
        logger.debug("Reading track ids from stdin…")
        track_ids = []
        with progress("Reading track ids…") as status:
            for line in click.get_text_stream("stdin"):
                track_ids.extend(line.split())
                status.update(f"Reading track ids… ({len(track_ids)})")
        logger.debug(f"{track_ids=}")

    client = OnzrClient()
    with progress(f"Adding {len(track_ids)} track(s) to queue…"):
        response = client.queue_add(track_ids)

    console.print(f"✅ {response.message}")


def _client_request(name: str, **kwargs):
    """A generic wrapper that executes a client method."""
    client = OnzrClient()
    method = getattr(client, name)
    response = method(**kwargs)
    return response


@cli.command()
@require_server
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

    with pager():
        for qt in queue.tracks:
            track_infos = (
                f"[white][bold]{qt.position + 1:-3d}[/] "
                f"[{theme.title_color}]{qt.track.title}[white] - "
                f"[{theme.artist_color}]{qt.track.artist} "
                f"[{theme.album_color}]({qt.track.album} - "
                f"{qt.track.release_date.year})[/]"
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
@require_server
def clear():
    """Empty queue."""
    state = _client_request("queue_clear")
    _print_server_state(state)


@contextmanager
def follow_keys() -> Iterator[Callable[[float], str | None]]:
    """Yield a non-blocking single key reader (stdin in cbreak mode).

    If stdin is not a TTY, the reader only waits for the given timeout.
    """
    if not sys.stdin.isatty():

        def wait(timeout: float) -> str | None:
            time.sleep(timeout)
            return None

        yield wait
        return

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def read_key(timeout: float) -> str | None:
        ready, _, _ = select.select([fd], [], [], timeout)
        return os.read(fd, 1).decode(errors="ignore") if ready else None

    try:
        tty.setcbreak(fd)
        yield read_key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


@cli.command()
@require_server
def now(
    follow: Annotated[
        bool, typer.Option("--follow", "-f", help="Follow what's happening.")
    ] = False,
):
    """Show details about the track that is being played and the player status.

    In follow mode, type `q` (or CTRL+C) to exit.
    """
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

    with follow_keys() as read_key, Live(display(), refresh_per_second=4) as live:
        try:
            while read_key(0.1) != "q":
                live.update(display())
        except KeyboardInterrupt:
            pass


@cli.command()
@require_server
def play(
    rank: Annotated[
        int | None,
        typer.Option("--rank", "-r", help="Start playing the queue at rank r."),
    ] = None,
):
    """Play queued tracks.

    If the player is paused, this command will resume the track.
    """
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
@require_server
def pause():
    """Pause/resume playing."""
    control = _client_request("pause")
    _print_player_control(control)


@cli.command()
@require_server
def stop():
    """Stop playing queue."""
    control = _client_request("stop")
    _print_player_control(control)


@cli.command("next")
@require_server
def next_():
    """Play next track in queue."""
    control = _client_request("next")
    _print_player_control(control)


@cli.command()
@require_server
def previous():
    """Play previous track in queue."""
    control = _client_request("previous")
    _print_player_control(control)


@cli.command()
def serve(
    host: Annotated[
        str, typer.Option("--host", "-H", help="Server host name.")
    ] = "localhost",
    port: Annotated[int, typer.Option("--port", "-P", help="Server port.")] = 9473,
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level",
            "-L",
            help="Server log level (debug, info, warning, error, critical).",
        ),
    ] = "info",
):
    """Run Onzr HTTP server."""
    theme = get_theme()
    # Typer does not support complex types such as Literal, so let's check log_level
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
    logging.config.dictConfig(logging_config)

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
@require_server
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
@require_server
def openapi():
    """Get Onzr HTTP API OpenAPI schema."""
    from onzr.server import app  # noqa: PLC0415

    sys.stdout.write(f"{json.dumps(app.openapi())}\n")
