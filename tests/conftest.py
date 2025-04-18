"""Tests configuration."""

import importlib
import tempfile
from pathlib import Path

import pytest
from dynaconf import loaders
from typer.testing import CliRunner

import onzr
from onzr import cli, config


@pytest.fixture
def onzr_dir(monkeypatch):
    """Create test application directory."""
    with tempfile.TemporaryDirectory() as app_dir:
        monkeypatch.setattr(config, "get_onzr_dir", lambda: Path(app_dir))
        importlib.reload(cli)
        yield app_dir


@pytest.fixture
def settings_files(onzr_dir):
    """Configured onzr settings files."""
    yield [(onzr_dir / s) for s in [config.SETTINGS_FILE, config.SECRETS_FILE]]


@pytest.fixture
def configured_app(onzr_dir, settings_files):
    """Configured onzr app."""
    module_dir = Path(onzr.__file__).parent
    for setting_file in settings_files:
        src = module_dir / setting_file.with_suffix(".toml.dist").name
        dest = onzr_dir / setting_file
        dest.write_text(src.read_text())
    loaders.write(str(onzr_dir / config.SECRETS_FILE), {"ARL": "fake-arl"}, merge=True)


@pytest.fixture
def runner():
    """CLI runner."""
    yield CliRunner()
