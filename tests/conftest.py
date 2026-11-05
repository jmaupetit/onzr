"""Tests configuration."""

import importlib
import logging
import tempfile
import threading
from pathlib import Path
from time import sleep, time
from typing import Generator

import pytest
import requests
import uvicorn
import yaml
from fastapi.testclient import TestClient
from responses import matchers
from typer.testing import CliRunner

import onzr
from onzr import cli, config
from onzr.core import Onzr
from onzr.deezer import DeezerClient, Track
from onzr.models.deezer import DeezerUser
from tests.factories import DeezerSongFactory, DeezerSongResponseFactory

logger = logging.getLogger(__name__)


def wait_for_requests(mock, timeout: float = 5.0) -> None:
    """Wait until all requests registered in the mock have been executed.

    This is useful to wait for requests made in background threads (e.g. track
    informations fetched by the server) before giving the control back to the
    `responses` fixture, which asserts all registered mocks have been fired.
    """
    deadline = time() + timeout
    while any(response.call_count == 0 for response in mock.registered()):
        if time() > deadline:
            return
        sleep(0.01)


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
def deezer_user(responses) -> DeezerUser:
    """Logged in Deezer user.

    Mock the `deezer.getUserData` gateway call used both to login and to get the
    logged in user. As `responses` drops an already fired response when a later
    registered one also matches the request, other gateway calls mocked in tests
    should also match their gateway method.
    """
    user = DeezerUser(id=666, name="onzr")
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        json={
            "error": {},
            "results": {
                "checkForm": "secret_token",
                "USER": {
                    "USER_ID": user.id,
                    "MULTI_ACCOUNT": {"ENABLED": False},
                    "BLOG_NAME": user.name,
                    "OPTIONS": {
                        "license_token": "fake",
                        "web_hq": True,
                        "web_lossless": True,
                        "license_country": "FR",
                    },
                    "SETTING": {"global": {}},
                },
            },
        },
        status=200,
        match=[
            matchers.query_param_matcher(
                {"method": "deezer.getUserData"}, strict_match=False
            )
        ],
    )
    return user


@pytest.fixture
def deezer_client(deezer_user, settings):
    """Configured DeezerClient instance."""
    client = DeezerClient(
        arl=settings.ARL,
        blowfish=settings.DEEZER_BLOWFISH_SECRET,
        fast=False,
    )

    yield client


@pytest.fixture
def configured_onzr(deezer_user, app_configuration):
    """Onzr core instance with an initialized Deezer client."""
    instance = Onzr()

    yield instance

    instance.player.stop()


@pytest.fixture
def client(configured_onzr):
    """A test client configured for the server."""
    from onzr import server  # noqa: PLC0415

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
    from onzr import server as onzr_server  # noqa: PLC0415

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
            break
        except requests.RequestException:
            sleep(0.1)

    yield thread

    # Gracefully shutdown the server
    server.should_exit = True
    thread.join()


@pytest.fixture
def track(responses, configured_onzr, faker, monkeypatch):
    """Track factory fixture."""

    def stream_local_file(_) -> Generator[bytes, None, None]:
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
