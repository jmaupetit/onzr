"""Onzr CLI tests."""

import copy
import datetime
import json
import logging
import re
from os import stat
from pathlib import Path
from time import sleep
from unittest.mock import MagicMock, patch

import click
import pytest
import uvicorn
import vlc
import yaml

import onzr
from onzr.cli import ExitCodes, cli
from onzr.deezer import DeezerClient
from onzr.exceptions import OnzrConfigurationError
from onzr.models import AlbumShort, ArtistShort, Collection, TrackShort
from tests.factories import DeezerSongFactory, DeezerSongResponseFactory

# Test fixtures
artist_1 = ArtistShort(id=1, name="foo")
artist_2 = ArtistShort(id=2, name="bar")
artists_collection: Collection = [artist_1, artist_2]
album_1 = AlbumShort(
    id=11,
    title="foo",
    artist="foo",
    release_date=datetime.date(2025, 1, 1).isoformat(),
)
album_2 = AlbumShort(
    id=12,
    title="bar",
    artist="bar",
    release_date=datetime.date(1925, 10, 1).isoformat(),
)
albums_collection: Collection = [album_1, album_2]
track_1 = TrackShort(id=21, title="foo", album="foo", artist="foo")
track_2 = TrackShort(id=22, title="bar", album="bar", artist="foo")
tracks_collection: Collection = [track_1, track_2]

# System exit codes
SYSTEM_EXIT_1 = 1
SYSTEM_EXIT_2 = 2


def test_require_server_command_wrapper(configured_cli_runner):
    """Test the `require_server` decorator."""
    result = configured_cli_runner.invoke(cli, ["state"])
    assert result.exit_code == ExitCodes.SERVER_DOWN
    assert "❌ Onzr server is down, run `onzr serve` first." in result.stdout


def test_command_help(cli_runner):
    """Test the `onzr --help` command."""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == ExitCodes.OK


def test_openapi_command(test_server, configured_cli_runner):
    """Test the `onzr openapi` command."""
    result = configured_cli_runner.invoke(cli, ["openapi"])
    assert result.exit_code == ExitCodes.OK

    # FIXME: a server log is captured as stdout (row 1)
    schema = json.loads(result.stdout.split("\n")[1])
    assert "openapi" in schema


def test_init_command_without_input(cli_runner, settings_file):
    """Test the `onzr init` command without ARL input."""
    assert settings_file.exists() is False

    # No ARL setting is provided
    result = cli_runner.invoke(cli, ["init"])
    assert result.exit_code == SYSTEM_EXIT_1

    # Base configuration exists but without ARL setting
    assert settings_file.exists() is True

    # Dist file and its initial copy hould be identical
    dist = Path(onzr.__file__).parent / Path(f"{settings_file.name}.dist")
    assert dist.exists()
    assert dist.read_text() == settings_file.read_text()


def test_init_command(cli_runner, settings_file):
    """Test the `onzr init` command."""
    assert settings_file.exists() is False

    result = cli_runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exit_code == ExitCodes.OK

    # Settings file should exist now
    assert settings_file.exists() is True

    # SETTINGS_FILE should be updated compared to the distributed template
    settings_dist = Path(onzr.__file__).parent / Path(f"{settings_file.name}.dist")
    assert settings_dist.exists()
    settings_file_content = settings_file.read_text()
    assert settings_dist.read_text() != settings_file_content
    assert re.search("^ARL: .*", settings_file_content)


def test_init_command_does_not_overwrite_settings(cli_runner, settings_file):
    """Test the `onzr init` command does not overwrite existing settings."""
    assert settings_file.exists() is False

    # Get most recent modification time
    result = cli_runner.invoke(cli, ["init"], input="fake-arl")
    original_stat = stat(settings_file)

    # Re-run the `init` command without reset mode shouldn't touch settings
    result = cli_runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exception is not None
    assert isinstance(result.exception, OnzrConfigurationError)
    assert (
        result.exception.args[0]
        == f"Configuration file '{settings_file}' already exists!"
    )
    assert original_stat == stat(settings_file)


def test_config_command_no_config_file(cli_runner, settings_file):
    """Test the `onzr config` command when the configuration file does not exist."""
    assert settings_file.exists() is False

    result = cli_runner.invoke(cli, ["config"])
    assert result.exit_code == ExitCodes.INCOMPLETE_CONFIGURATION
    assert "Configuration file does not exist, use `onzr init` first." in result.stdout


def test_config_command(configured_cli_runner, settings_file):
    """Test the `onzr config` command."""
    assert settings_file.exists() is True

    # Mock click.edit function
    click.edit = MagicMock(return_value=0)

    # Get configuration file path
    result = configured_cli_runner.invoke(cli, ["config", "-p"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout.split("\n")[0] == str(settings_file)
    click.edit.assert_not_called()

    # Display configuration
    result = configured_cli_runner.invoke(cli, ["config"])
    assert result.exit_code == ExitCodes.OK
    with settings_file.open() as s:
        assert yaml.safe_load(result.stdout) == yaml.safe_load(s)
    click.edit.assert_not_called()

    # Edit configuration
    result = configured_cli_runner.invoke(cli, ["config", "-e"])
    assert result.exit_code == ExitCodes.OK
    click.edit.assert_called_once()


def test_search_command_with_no_argument(configured_cli_runner):
    """Test the `onzr search` without any argument."""
    result = configured_cli_runner.invoke(cli, ["search"])
    assert result.exit_code == ExitCodes.NOT_FOUND


@pytest.mark.parametrize("option", ("artist", "album", "track"))
def test_search_command_with_no_match(configured_cli_runner, monkeypatch, option):
    """Test the `onzr search` command with no match."""

    def search(*args, **kwargs):
        """Monkeypatch search."""
        return []

    monkeypatch.setattr(DeezerClient, "search", search)

    result = configured_cli_runner.invoke(cli, ["search", f"--{option}", "foo"])
    assert result.exit_code == ExitCodes.NOT_FOUND


@pytest.mark.parametrize(
    "option,results",
    (
        ("artist", artists_collection),
        ("album", albums_collection),
        ("track", tracks_collection),
    ),
)
def test_search_command(configured_cli_runner, monkeypatch, option, results):
    """Test the `onzr search` command."""

    def search(*args, **kwargs):
        """Monkeypatch search."""
        return results

    monkeypatch.setattr(DeezerClient, "search", search)

    result = configured_cli_runner.invoke(cli, ["search", f"--{option}", "foo"])
    assert result.exit_code == ExitCodes.OK

    # Test ids option
    result = configured_cli_runner.invoke(
        cli, ["search", f"--{option}", "foo", "--ids"]
    )
    assert result.exit_code == ExitCodes.OK
    expected = "".join([f"{r.id}\n" for r in results])
    assert result.stdout == expected

    # Test first option
    result = configured_cli_runner.invoke(
        cli, ["search", f"--{option}", "foo", "--ids", "--first"]
    )
    assert result.exit_code == ExitCodes.OK
    expected = f"{results[0].id}\n"
    assert result.stdout == expected


def test_artist_command_with_no_id(configured_cli_runner):
    """Test the `onzr artist` command with no ID."""
    result = configured_cli_runner.invoke(cli, ["artists"])
    assert result.exit_code == SYSTEM_EXIT_2


def test_artist_command(configured_cli_runner, monkeypatch):
    """Test the `onzr artist` command."""
    # One should choose one type of result
    result = configured_cli_runner.invoke(cli, ["artist", "1", "--no-top"])
    assert result.exit_code == ExitCodes.INVALID_ARGUMENTS

    top_collection = copy.copy(tracks_collection)
    top_collection.reverse()

    def artist(*args, **kwargs):
        """Monkeypatch artist."""
        if kwargs.get("radio"):
            return tracks_collection
        elif kwargs.get("top"):
            return top_collection
        elif kwargs.get("albums"):
            return albums_collection

    monkeypatch.setattr(DeezerClient, "artist", artist)

    # Default using an argument
    result = configured_cli_runner.invoke(cli, ["artist", "1"])
    assert result.exit_code == ExitCodes.OK
    result = configured_cli_runner.invoke(cli, ["artist", "--ids", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in top_collection])

    # Top using an argument
    result = configured_cli_runner.invoke(cli, ["artist", "--ids", "--top", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in top_collection])

    # Top using stdin
    for input in ["1", " 1", " 1 ", "1 "]:
        result = configured_cli_runner.invoke(
            cli, ["artist", "--ids", "--top", "-"], input=input
        )
        assert result.exit_code == ExitCodes.OK
        assert result.stdout == "".join([f"{t.id}\n" for t in top_collection])

    # Radio
    result = configured_cli_runner.invoke(cli, ["artist", "--ids", "--radio", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in tracks_collection])

    # Albums
    result = configured_cli_runner.invoke(cli, ["artist", "--ids", "--albums", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{a.id}\n" for a in albums_collection])


def test_album_command(configured_cli_runner, monkeypatch):
    """Test the `onzr album` command."""

    def album(*args, **kwargs):
        """Monkeypatch album."""
        return tracks_collection

    monkeypatch.setattr(DeezerClient, "album", album)

    # Standard run
    result = configured_cli_runner.invoke(cli, ["album", "1"])
    assert result.exit_code == ExitCodes.OK

    # Display only track ids
    result = configured_cli_runner.invoke(cli, ["album", "--ids", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in tracks_collection])

    # Use stdin
    for input in ["1", " 1", " 1 ", "1 "]:
        result = configured_cli_runner.invoke(cli, ["album", "--ids", "-"], input=input)
        assert result.exit_code == ExitCodes.OK
        assert result.stdout == "".join([f"{t.id}\n" for t in tracks_collection])


def test_mix_command(configured_cli_runner, monkeypatch):
    """Test the `onzr mix` command."""

    def search(*args, **kwargs):
        """Monkeypatch search."""
        return artists_collection

    monkeypatch.setattr(DeezerClient, "search", search)

    track_3 = TrackShort(id="31", title="lol", album="foo", artist="foo")
    track_4 = TrackShort(id="32", title="doe", album="bar", artist="bar")
    deep_collection: Collection = [track_3, track_4]

    def artist(*args, **kwargs):
        """Monkeypatch artist."""
        if kwargs.get("radio"):
            return deep_collection
        elif kwargs.get("top"):
            return tracks_collection

    monkeypatch.setattr(DeezerClient, "artist", artist)

    # Standard mix
    result = configured_cli_runner.invoke(cli, ["mix", "foo", "bar"])
    assert result.exit_code == ExitCodes.OK

    result = configured_cli_runner.invoke(cli, ["mix", "foo", "bar", "--ids"])
    assert result.exit_code == ExitCodes.OK
    # As tracks are shuffled, we need to sort them
    assert sorted(result.stdout.split()) == sorted(
        [f"{t.id}" for t in tracks_collection] * 2
    )

    # Deep mix
    result = configured_cli_runner.invoke(cli, ["mix", "foo", "bar", "--deep"])
    assert result.exit_code == ExitCodes.OK

    result = configured_cli_runner.invoke(cli, ["mix", "foo", "bar", "--ids", "--deep"])
    assert result.exit_code == ExitCodes.OK
    # As tracks are shuffled, we need to sort them
    assert sorted(result.stdout.split()) == sorted(
        [f"{t.id}" for t in deep_collection] * 2
    )


def test_add_command(test_server, responses, configured_cli_runner):
    """Test the `onzr add` command."""
    track_ids = [1, 2, 3]
    for track_id in track_ids:
        responses.post(
            "http://www.deezer.com/ajax/gw-light.php",
            status=200,
            json=DeezerSongResponseFactory.build(
                error={}, results=DeezerSongFactory.build(SNG_ID=track_id)
            ).model_dump(),
        )

    result = configured_cli_runner.invoke(cli, ["add", "1", "2", "3"])
    assert result.exit_code == ExitCodes.OK
    assert "Added 3 track(s) to queue" in result.stdout

    # Pass ids via stdin
    result = configured_cli_runner.invoke(
        cli, ["add", "-"], input="\n".join(map(str, track_ids))
    )
    assert result.exit_code == ExitCodes.OK
    assert "Added 3 track(s) to queue" in result.stdout


def test_queue_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr queue` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["queue"])
    assert result.exit_code == ExitCodes.OK
    assert "Queue is empty, use onzr add to start adding tracks." in result.stdout

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    result = configured_cli_runner.invoke(cli, ["queue"])
    assert result.exit_code == ExitCodes.OK
    assert all(x in result.stdout for x in [f"🧵   {i}" for i in range(1, 4)])


def test_clear_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr clear` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["clear"])
    assert result.exit_code == ExitCodes.OK
    assert "📢 Player: Stopped · Queue: None / 0" in result.stdout

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    result = configured_cli_runner.invoke(cli, ["clear"])
    assert result.exit_code == ExitCodes.OK
    assert "📢 Player: Stopped · Queue: None / 0" in result.stdout
    assert configured_onzr.queue.is_empty


def test_now_command(
    test_server, configured_cli_runner, configured_onzr, track, responses
):
    """Test the `onzr clear` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["now"])
    assert result.exit_code == ExitCodes.OK
    assert "Nothing more has been queued" in result.stdout

    # Fill the queue
    track_ids = [1, 2, 3]
    durations = [128, 245, 142]
    configured_onzr.queue.add(
        [
            track(track_id, DURATION=duration)
            for track_id, duration in zip(track_ids, durations, strict=True)
        ]
    )
    assert len(configured_onzr.queue) == len(track_ids)

    # Still nothing to display
    result = configured_cli_runner.invoke(cli, ["now"])
    assert result.exit_code == ExitCodes.OK
    assert "Nothing more has been queued" in result.stdout

    # Nota bene:
    #
    # Mock track info response as we will refresh this info before playing. If we do
    # not mock this here, we will use the latest available response for this track
    # which corresponds to the third track (and not the first).
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={}, results=DeezerSongFactory.build(SNG_ID=1, DURATION=128)
        ).model_dump(),
    )

    # Start playing
    configured_onzr.player.play()
    sleep(0.3)
    result = configured_cli_runner.invoke(cli, ["now"])
    assert result.exit_code == ExitCodes.OK
    assert "· (1/3)" in result.stdout
    assert "▶️" in result.stdout
    assert "Next:" in result.stdout
    assert " 00:02:08" in result.stdout


def test_play_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr play` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["play"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.NothingSpecial

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Play
    result = configured_cli_runner.invoke(cli, ["play"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.player.get_state() == vlc.State.Opening

    # Play an invalid track rank
    result = configured_cli_runner.invoke(cli, ["play", "--rank", "0"])
    assert result.exit_code == ExitCodes.INVALID_ARGUMENTS
    assert "Invalid rank" in result.stdout

    # Play the first track in queue
    result = configured_cli_runner.invoke(cli, ["play", "--rank", "1"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.player.get_state() == vlc.State.Opening

    # Play the second track in queue
    result = configured_cli_runner.invoke(cli, ["play", "--rank", "2"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.player.get_state() == vlc.State.Opening

    # Stop the player
    configured_onzr.player.stop()


def test_pause_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr pause` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["pause"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.NothingSpecial

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Pause without prior play event
    result = configured_cli_runner.invoke(cli, ["pause"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.NothingSpecial

    # Play
    configured_onzr.player.play()
    sleep(0.3)
    result = configured_cli_runner.invoke(cli, ["pause"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.Paused

    # Toggle
    result = configured_cli_runner.invoke(cli, ["pause"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.player.get_state() == vlc.State.Playing


def test_stop_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr stop` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["stop"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.Stopped

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Stop while playing
    configured_onzr.player.play()
    result = configured_cli_runner.invoke(cli, ["stop"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.Stopped


def test_next_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr next` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["next"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.NothingSpecial

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Play first in queue
    configured_onzr.player.play()
    sleep(0.3)
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.queue.playing == 0

    # Next
    for expected in (1, 2):
        result = configured_cli_runner.invoke(cli, ["next"])
        sleep(0.3)
        assert result.exit_code == ExitCodes.OK
        assert configured_onzr.player.is_playing() == 1
        assert configured_onzr.queue.playing == expected

    expected = 2
    result = configured_cli_runner.invoke(cli, ["next"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.queue.playing == expected


def test_previous_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr previous` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["previous"])
    assert result.exit_code == ExitCodes.OK
    assert configured_onzr.player.is_playing() == 0
    assert configured_onzr.player.get_state() == vlc.State.NothingSpecial

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Play first in queue
    current = 2
    configured_onzr.player.play_item_at_index(current)
    sleep(0.3)
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.queue.playing == current

    # Previous
    result = configured_cli_runner.invoke(cli, ["previous"])
    assert result.exit_code == ExitCodes.OK
    sleep(0.3)
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.queue.playing == 1

    result = configured_cli_runner.invoke(cli, ["previous"])
    assert result.exit_code == ExitCodes.OK
    sleep(0.3)
    assert configured_onzr.player.is_playing() == 1
    assert configured_onzr.queue.playing == 0


def test_serve_command(configured_cli_runner, configured_onzr):
    """Test the `onzr serve` command."""
    with (
        patch.object(uvicorn.Server, "run") as mock_run,
        patch("uvicorn.Config", spec=True) as MockConfig,
    ):
        result = configured_cli_runner.invoke(cli, ["serve"])
        assert result.exit_code == ExitCodes.OK
        MockConfig.assert_called_once_with(
            "onzr.server:app", host="localhost", port=9473, log_level=logging.INFO
        )
        assert mock_run.called

    # Test log level checking
    result = configured_cli_runner.invoke(
        cli,
        ["serve", "--log-level", "foo"],
    )
    assert result.exit_code == ExitCodes.INVALID_ARGUMENTS
    assert "Forbidden log-level" in result.stdout

    # Change defaults
    with (
        patch.object(uvicorn.Server, "run") as mock_run,
        patch("uvicorn.Config", spec=True) as MockConfig,
    ):
        result = configured_cli_runner.invoke(
            cli,
            ["serve", "--host", "127.0.0.1", "--port", 9999, "--log-level", "debug"],
        )
        assert result.exit_code == ExitCodes.OK
        MockConfig.assert_called_once_with(
            "onzr.server:app", host="127.0.0.1", port=9999, log_level=logging.DEBUG
        )
        assert mock_run.called


def test_state_command(test_server, configured_cli_runner, configured_onzr, track):
    """Test the `onzr state` command."""
    # Empty queue
    result = configured_cli_runner.invoke(cli, ["state"])
    assert result.exit_code == ExitCodes.OK
    assert "📢 Player: NothingSpecial · Queue: None / 0" in result.stdout

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    result = configured_cli_runner.invoke(cli, ["state"])
    assert result.exit_code == ExitCodes.OK
    assert "📢 Player: NothingSpecial · Queue: None / 3" in result.stdout

    # Start playing
    configured_onzr.player.play()
    sleep(0.3)
    result = configured_cli_runner.invoke(cli, ["state"])
    assert result.exit_code == ExitCodes.OK
    assert "📢 Player: Playing · Queue: 1 / 3" in result.stdout

    # Stop the player
    configured_onzr.player.stop()
    result = configured_cli_runner.invoke(cli, ["state"])
    assert result.exit_code == ExitCodes.OK
    assert "📢 Player: Stopped · Queue: 1 / 3" in result.stdout


def test_version_command(configured_cli_runner):
    """Test the `onzr version` command."""
    semver = (
        r"(?P<major>0|[1-9]\d*)"
        r"\.(?P<minor>0|[1-9]\d*)"
        r"\.(?P<patch>0|[1-9]\d*)"
        r"(?P<extras>.*)"
    )
    pattern = re.compile("🔖 Version: " + semver)
    result = configured_cli_runner.invoke(cli, ["version"])
    assert result.exit_code == ExitCodes.OK
    assert pattern.match(result.stdout)
