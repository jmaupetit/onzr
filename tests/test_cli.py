"""Data7 CLI tests."""

import copy
import datetime
import re
from os import stat
from pathlib import Path

import pytest

import onzr
from onzr.cli import ExitCodes, cli
from onzr.deezer import AlbumShort, ArtistShort, Collection, DeezerClient, TrackShort

# Test fixtures
artist_1 = ArtistShort(id="1", name="foo")
artist_2 = ArtistShort(id="2", name="bar")
artists_collection: Collection = [artist_1, artist_2]
album_1 = AlbumShort(
    id="11",
    name="foo",
    release_date=datetime.date(2025, 1, 1).isoformat(),
    artist=artist_1,
)
album_2 = AlbumShort(
    id="12",
    name="bar",
    release_date=datetime.date(1925, 10, 1).isoformat(),
    artist=artist_2,
)
albums_collection: Collection = [album_1, album_2]
track_1 = TrackShort(id="21", title="foo", album=album_1)
track_2 = TrackShort(id="22", title="bar", album=album_2)
tracks_collection: Collection = [track_1, track_2]

# System exit codes
SYSTEM_EXIT_1 = 1
SYSTEM_EXIT_2 = 2


def test_command_help(runner):
    """Test the `onzr --help` command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == ExitCodes.OK


def test_init_command_without_input(runner, settings_files):
    """Test the `onzr init` command without ARL input."""
    for setting_file in settings_files:
        assert setting_file.exists() is False

    # No ARL setting is provided
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == SYSTEM_EXIT_1

    # Base configuration exists but without ARL setting
    for setting_file in settings_files:
        assert setting_file.exists() is True

    # Dist file and its initial copy hould be identical
    for dest in settings_files:
        dist = Path(onzr.__file__).parent / Path(f"{dest.name}.dist")
        assert dist.exists()
        assert dist.read_text() == dest.read_text()


def test_init_command(runner, settings_files):
    """Test the `onzr init` command."""
    for setting_file in settings_files:
        assert setting_file.exists() is False

    result = runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exit_code == ExitCodes.OK

    # All settings files should exist now
    for setting_file in settings_files:
        assert setting_file.exists() is True

    # SETTINGS_FILE should be identical
    SETTINGS_FILE = settings_files[0]
    settings_dist = Path(onzr.__file__).parent / Path(f"{SETTINGS_FILE.name}.dist")
    assert settings_dist.exists()
    assert settings_dist.read_text() == SETTINGS_FILE.read_text()

    # SECRETS_FILE should be different
    SECRETS_FILE = settings_files[1]
    secrets_dist = Path(onzr.__file__).parent / Path(f"{SECRETS_FILE.name}.dist")
    assert secrets_dist.exists()
    secrets = SECRETS_FILE.read_text()
    assert secrets_dist.read_text() != secrets
    assert re.search("^ARL = .*", secrets)


def test_init_command_does_not_overwrite_settings(runner, settings_files):
    """Test the `onzr init` command does not overwrite existing settings."""
    for setting_file in settings_files:
        assert setting_file.exists() is False

    # Get most recent modification time
    result = runner.invoke(cli, ["init"], input="fake-arl")
    original_stats = [stat(sf) for sf in settings_files]

    # Re-run the `init` command without reset mode shouldn't touch settings
    result = runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exit_code == ExitCodes.OK
    new_stats = [stat(sf) for sf in settings_files]

    assert all(o == n for o, n in zip(original_stats, new_stats, strict=True))


def test_init_command_reset(runner, settings_files):
    """Test the `onzr init` command using the --reset flag."""
    for setting_file in settings_files:
        assert setting_file.exists() is False

    result = runner.invoke(cli, ["init"], input="fake-arl")
    assert result.exit_code == ExitCodes.OK

    # All settings files should exist now
    for setting_file in settings_files:
        assert setting_file.exists() is True

    # Get most recent modification time
    SETTINGS_FILE = settings_files[0]
    SECRETS_FILE = settings_files[1]
    original_settings_stats = SETTINGS_FILE.stat()
    original_secrets_stats = SECRETS_FILE.stat()

    # Re-run the `init` command with the reset mode should update secrets
    result = runner.invoke(cli, ["init", "--reset"], input="new-fake-arl")
    assert result.exit_code == ExitCodes.OK

    # SETTINGS_FILE should be identical
    settings_dist = Path(onzr.__file__).parent / Path(f"{SETTINGS_FILE.name}.dist")
    assert settings_dist.exists()
    assert settings_dist.read_text() == SETTINGS_FILE.read_text()
    assert original_settings_stats == SETTINGS_FILE.stat()

    # SECRETS_FILE should be different
    secrets_dist = Path(onzr.__file__).parent / Path(f"{SECRETS_FILE.name}.dist")
    assert secrets_dist.exists()
    secrets = SECRETS_FILE.read_text()
    assert secrets_dist.read_text() != secrets
    assert original_secrets_stats != SECRETS_FILE.stat()
    assert re.search(r'^ARL = "new-fake-arl"', secrets)


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

    track_3 = TrackShort(id="31", title="lol", album=album_1)
    track_4 = TrackShort(id="32", title="doe", album=album_2)
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
