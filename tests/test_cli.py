"""Data7 CLI tests."""

import copy
import datetime
import re
from os import stat
from pathlib import Path

import pytest

import onzr
from onzr.cli import ExitCodes, cli
from onzr.deezer import DeezerClient
from onzr.exceptions import OnzrConfigurationError
from onzr.models import AlbumShort, ArtistShort, Collection, TrackShort

# Test fixtures
artist_1 = ArtistShort(id="1", name="foo")
artist_2 = ArtistShort(id="2", name="bar")
artists_collection: Collection = [artist_1, artist_2]
album_1 = AlbumShort(
    id="11",
    title="foo",
    artist="foo",
    release_date=datetime.date(2025, 1, 1).isoformat(),
)
album_2 = AlbumShort(
    id="12",
    title="bar",
    artist="bar",
    release_date=datetime.date(1925, 10, 1).isoformat(),
)
albums_collection: Collection = [album_1, album_2]
track_1 = TrackShort(id="21", title="foo", album="foo", artist="foo")
track_2 = TrackShort(id="22", title="bar", album="bar", artist="foo")
tracks_collection: Collection = [track_1, track_2]

# System exit codes
SYSTEM_EXIT_1 = 1
SYSTEM_EXIT_2 = 2


def test_command_help(runner):
    """Test the `onzr --help` command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == ExitCodes.OK


def test_init_command_without_input(runner, settings_file):
    """Test the `onzr init` command without ARL input."""
    assert settings_file.exists() is False

    # No ARL setting is provided
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == SYSTEM_EXIT_1

    # Base configuration exists but without ARL setting
    assert settings_file.exists() is True

    # Dist file and its initial copy hould be identical
    dist = Path(onzr.__file__).parent / Path(f"{settings_file.name}.dist")
    assert dist.exists()
    assert dist.read_text() == settings_file.read_text()


def test_init_command(runner, settings_file):
    """Test the `onzr init` command."""
    assert settings_file.exists() is False

    result = runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exit_code == ExitCodes.OK

    # Settings file should exist now
    assert settings_file.exists() is True

    # SETTINGS_FILE should be updated compared to the distributed template
    settings_dist = Path(onzr.__file__).parent / Path(f"{settings_file.name}.dist")
    assert settings_dist.exists()
    settings_file_content = settings_file.read_text()
    assert settings_dist.read_text() != settings_file_content
    assert re.search("^ARL: .*", settings_file_content)


def test_init_command_does_not_overwrite_settings(runner, settings_file):
    """Test the `onzr init` command does not overwrite existing settings."""
    assert settings_file.exists() is False

    # Get most recent modification time
    result = runner.invoke(cli, ["init"], input="fake-arl")
    original_stat = stat(settings_file)

    # Re-run the `init` command without reset mode shouldn't touch settings
    result = runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exception is not None
    assert isinstance(result.exception, OnzrConfigurationError)
    assert (
        result.exception.args[0]
        == f"Configuration file '{settings_file}' already exists!"
    )
    assert original_stat == stat(settings_file)


def test_search_command_with_no_argument(runner, configured_app):
    """Test the `onzr search` without any argument."""
    result = runner.invoke(cli, ["search"])
    assert result.exit_code == ExitCodes.NOT_FOUND


@pytest.mark.parametrize("option", ("artist", "album", "track"))
def test_search_command_with_no_match(runner, configured_app, monkeypatch, option):
    """Test the `onzr search` command with no match."""

    def search(*args, **kwargs):
        """Monkeypatch search."""
        return []

    monkeypatch.setattr(DeezerClient, "search", search)

    result = runner.invoke(cli, ["search", f"--{option}", "foo"])
    assert result.exit_code == ExitCodes.NOT_FOUND


@pytest.mark.parametrize(
    "option,results",
    (
        ("artist", artists_collection),
        ("album", albums_collection),
        ("track", tracks_collection),
    ),
)
def test_search_command(runner, configured_app, monkeypatch, option, results):
    """Test the `onzr search` command."""

    def search(*args, **kwargs):
        """Monkeypatch search."""
        return results

    monkeypatch.setattr(DeezerClient, "search", search)

    result = runner.invoke(cli, ["search", f"--{option}", "foo"])
    assert result.exit_code == ExitCodes.OK

    # Test ids option
    result = runner.invoke(cli, ["search", f"--{option}", "foo", "--ids"])
    assert result.exit_code == ExitCodes.OK
    expected = "".join([f"{r.id}\n" for r in results])
    assert result.stdout == expected


def test_artist_command_with_no_id(runner, configured_app):
    """Test the `onzr artist` command with no ID."""
    result = runner.invoke(cli, ["artists"])
    assert result.exit_code == SYSTEM_EXIT_2


def test_artist_command(runner, configured_app, monkeypatch):
    """Test the `onzr artist` command."""
    # One should choose one type of result
    result = runner.invoke(
        cli, ["artist", "--no-top", "--no-radio", "--no-albums", "1"]
    )
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
    result = runner.invoke(cli, ["artist", "1"])
    assert result.exit_code == ExitCodes.OK
    result = runner.invoke(cli, ["artist", "--ids", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in top_collection])

    # Top using an argument
    result = runner.invoke(cli, ["artist", "--ids", "--top", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in top_collection])

    # Top using stdin
    for input in ["1", " 1", " 1 ", "1 "]:
        result = runner.invoke(cli, ["artist", "--ids", "--top", "-"], input=input)
        assert result.exit_code == ExitCodes.OK
        assert result.stdout == "".join([f"{t.id}\n" for t in top_collection])

    # Radio
    result = runner.invoke(cli, ["artist", "--ids", "--radio", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in tracks_collection])

    # Albums
    result = runner.invoke(cli, ["artist", "--ids", "--albums", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{a.id}\n" for a in albums_collection])


def test_album_command(runner, configured_app, monkeypatch):
    """Test the `onzr album` command."""

    def album(*args, **kwargs):
        """Monkeypatch album."""
        return tracks_collection

    monkeypatch.setattr(DeezerClient, "album", album)

    # Standard run
    result = runner.invoke(cli, ["album", "1"])
    assert result.exit_code == ExitCodes.OK

    # Display only track ids
    result = runner.invoke(cli, ["album", "--ids", "1"])
    assert result.exit_code == ExitCodes.OK
    assert result.stdout == "".join([f"{t.id}\n" for t in tracks_collection])

    # Use stdin
    for input in ["1", " 1", " 1 ", "1 "]:
        result = runner.invoke(cli, ["album", "--ids", "-"], input=input)
        assert result.exit_code == ExitCodes.OK
        assert result.stdout == "".join([f"{t.id}\n" for t in tracks_collection])


def test_mix_command(runner, configured_app, monkeypatch):
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
    result = runner.invoke(cli, ["mix", "foo", "bar"])
    assert result.exit_code == ExitCodes.OK

    result = runner.invoke(cli, ["mix", "foo", "bar", "--ids"])
    assert result.exit_code == ExitCodes.OK
    # As tracks are shuffled, we need to sort them
    assert sorted(result.stdout.split()) == sorted(
        [f"{t.id}" for t in tracks_collection] * 2
    )

    # Deep mix
    result = runner.invoke(cli, ["mix", "foo", "bar", "--deep"])
    assert result.exit_code == ExitCodes.OK

    result = runner.invoke(cli, ["mix", "foo", "bar", "--ids", "--deep"])
    assert result.exit_code == ExitCodes.OK
    # As tracks are shuffled, we need to sort them
    assert sorted(result.stdout.split()) == sorted(
        [f"{t.id}" for t in deep_collection] * 2
    )
