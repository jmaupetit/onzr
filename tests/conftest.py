"""Tests configuration."""

import importlib
import tempfile

import click
import pytest
from typer.testing import CliRunner

from onzr import cli, config


@pytest.fixture(autouse=True)
def onzr_dir(monkeypatch):
    """Create test application directory."""
    with tempfile.TemporaryDirectory() as app_dir:
        monkeypatch.setattr(click, "get_app_dir", lambda _: app_dir)
        importlib.reload(config)
        yield


@pytest.fixture
def onzr_cli(onzr_dir):
    """Configured onzr CLI instance."""
    importlib.reload(cli)
    yield cli.cli


@pytest.fixture
def settings_files(onzr_dir):
    """Configured onzr settings files."""
    yield [
        config.SETTINGS_FILE,
        config.SECRETS_FILE,
    ]


@pytest.fixture
def settings(onzr_dir):
    """Configured onzr settings files."""
    yield config.settings


@pytest.fixture
def runner():
    """CLI runner."""
    yield CliRunner()
