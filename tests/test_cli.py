"""Data7 CLI tests."""

import tempfile

import click

import onzr
from onzr.cli import ExitCodes, cli


def test_command_help(runner):
    """Test the `onzr --help` command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == ExitCodes.OK


def test_init_command(runner, monkeypatch):
    """Test the `onzr init` command."""
    with tempfile.TemporaryDirectory() as app_dir:
        monkeypatch.setattr(click, 'get_app_dir', lambda: app_dir)
        print(f"{onzr.config.settings.__dict__}")
        settings_files = [
            onzr.config.SETTINGS_FILE,
            onzr.config.SECRETS_FILE,
        ]
        for setting_file in settings_files:
            assert setting_file.exists() is False

        # result = runner.invoke(cli, ["init"], input="fake-arl")
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == ExitCodes.OK

        # All settings files should exist now
        for setting_file in settings_files:
            assert setting_file.exists() is True
