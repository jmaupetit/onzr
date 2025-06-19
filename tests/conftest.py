"""Tests configuration."""

import importlib
import tempfile
from pathlib import Path

import pytest
import yaml
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
def settings_file(onzr_dir):
    """Configured onzr settings file."""
    yield onzr_dir / config.SETTINGS_FILE


@pytest.fixture
def configured_app(onzr_dir, settings_file):
    """Configured onzr app."""
    module_dir = Path(onzr.__file__).parent
    src = module_dir / settings_file.with_suffix(".yaml.dist").name
    dest = onzr_dir / settings_file

    with src.open() as f:
        test_config = yaml.safe_load(f)
    test_config["ARL"] = "fake-arl"
    with dest.open(mode="w") as f:
        yaml.dump(test_config, f)


@pytest.fixture
def runner():
    """CLI runner."""
    yield CliRunner()
