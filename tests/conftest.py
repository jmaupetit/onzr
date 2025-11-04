"""Tests configuration."""

import importlib
import json
import logging
import tempfile
import threading
from pathlib import Path

import pytest
import requests
import uvicorn
import yaml
from fastapi.testclient import TestClient
from requests.exceptions import ConnectionError
from typer.testing import CliRunner

import onzr
from onzr import cli, config
from onzr.core import Onzr
from onzr.deezer import Track
from tests.factories import DeezerSongFactory, DeezerSongResponseFactory

logger = logging.getLogger(__name__)


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
def app_configuration(settings_file):
    """Configured onzr app."""
    module_dir = Path(onzr.__file__).parent
    dist = module_dir / settings_file.with_suffix(".yaml.dist").name

    with dist.open() as f:
        test_config = yaml.safe_load(f)
    test_config["ARL"] = "fake-arl"
    test_config["PORT"] = 9474
    with settings_file.open(mode="w") as f:
        yaml.safe_dump(test_config, f, default_style='"')


@pytest.fixture
def settings(app_configuration):
    """Get configured settings."""
    return config.get_settings()


@pytest.fixture
def cli_runner():
    """CLI runner."""
    yield CliRunner()


@pytest.fixture
def configured_cli_runner(app_configuration):
    """Configured CLI runner."""
    yield CliRunner()


@pytest.fixture
def configured_onzr(responses, app_configuration, monkeypatch):
    """Onzr core instance with an initialized Deezer client."""
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        body=json.dumps(
            {
                "error": {},
                "results": {
                    "checkForm": "secret_token",
                    "USER": {
                        "USER_ID": 666,
                        "MULTI_ACCOUNT": {"ENABLED": False},
                        "BLOG_NAME": "onzr",
                        "OPTIONS": {
                            "license_token": "fake",
                            "web_hq": True,
                            "web_lossless": True,
                            "license_country": "FR",
                        },
                        "SETTING": {"global": {}},
                    },
                },
            }
        ),
        status=200,
        content_type="application/json",
    )
    instance = Onzr()

    yield instance

    instance.player.stop()


@pytest.fixture
def client(configured_onzr):
    """A test client configured for the server."""
    from onzr import server

    def get_configured_onzr():
        return configured_onzr

    # Override dependency to ensure we have got a deezer-mocked Onzr instance
    server.app.dependency_overrides[server.get_onzr] = get_configured_onzr
    yield TestClient(server.app)


@pytest.fixture
def test_server(responses, settings, configured_onzr):
    """A uvicorn test server instance.

    This fixture is costly and should only be run for integration testing such as an
    API client without mocking the server.
    """
    from onzr import server as onzr_server

    def get_configured_onzr():
        return configured_onzr

    # Override dependency to ensure we have got a deezer-mocked Onzr instance
    onzr_server.app.dependency_overrides[onzr_server.get_onzr] = get_configured_onzr

    responses.add_passthru(str(settings.SERVER_BASE_URL))

    config = uvicorn.Config(
        onzr_server.app, host=settings.HOST, port=settings.PORT, log_level="info"
    )
    server = uvicorn.Server(config)

    # Start a real test server in the background
    thread = threading.Thread(
        target=server.run,
        daemon=True,
    )
    thread.start()

    # Wait for the server to start
    max = 150
    attempt = 0
    while (attempt := attempt + 1) <= max:
        try:
            requests.get(settings.SERVER_BASE_URL, timeout=0.1)
        except ConnectionError:
            pass

    yield thread

    # Gracefully shutdown the server
    server.should_exit = True
    thread.join()


@pytest.fixture
def track(responses, configured_onzr, faker, monkeypatch):
    """Track factory fixture."""

    def stream_local_file(_):
        """Stream the same file for every track."""
        chunk_size: int = 2048 * 3
        with Path("./tests/intro-lvs.mp3").open("rb") as content:
            while chunk := content.read(chunk_size):
                yield chunk

    def _track(track_id: int | None = None, **kwargs):
        track_id = faker.pyint() if track_id is None else track_id
        responses.post(
            "http://www.deezer.com/ajax/gw-light.php",
            status=200,
            json=DeezerSongResponseFactory.build(
                error={}, results=DeezerSongFactory.build(SNG_ID=track_id, **kwargs)
            ).model_dump(),
        )
        track = Track(configured_onzr.deezer, track_id)
        monkeypatch.setattr(track, "stream", stream_local_file)
        return track

    return _track
