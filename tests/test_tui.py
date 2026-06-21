"""Onzr TUI tests."""

from unittest.mock import MagicMock

import pytest
from textual.coordinate import Coordinate

from onzr.tui import PlayControl, PlayStatusWidget

# Button ID constants
BUTTON_PLAY = "play"
BUTTON_PAUSE = "pause"
BUTTON_STOP = "stop"
BUTTON_PREVIOUS = "previous"
BUTTON_NEXT = "next"


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock OnzrClient with all control methods."""
    client = MagicMock()
    client.play = MagicMock()
    client.pause = MagicMock()
    client.stop = MagicMock()
    client.previous = MagicMock()
    client.next = MagicMock()
    return client


@pytest.fixture
def empty_playlist() -> MagicMock:
    """Create an empty playlist mock."""
    playlist = MagicMock()
    playlist.row_count = 0
    return playlist


@pytest.fixture
def populated_playlist() -> MagicMock:
    """Create a playlist with data mock."""
    playlist = MagicMock()
    playlist.row_count = 2
    playlist.cursor_coordinate = Coordinate(0, 0)
    playlist.coordinate_to_cell_key = MagicMock(return_value=("row_key", None))
    return playlist


@pytest.fixture
def playlist_with_none_row_key() -> MagicMock:
    """Create a playlist where coordinate_to_cell_key returns None row_key."""
    playlist = MagicMock()
    playlist.row_count = 1
    playlist.cursor_coordinate = Coordinate(0, 0)
    playlist.coordinate_to_cell_key = MagicMock(return_value=(None, None))
    return playlist


class TestPlayStatusWidget:
    """Tests for PlayStatusWidget."""

    def test_render_default(self) -> None:
        """Test default render shows 'Nothing'."""
        widget = PlayStatusWidget()
        assert widget.render() == "Now playing: Nothing!"

    def test_render_with_track(self) -> None:
        """Test render with specific track name."""
        widget = PlayStatusWidget()
        widget.now_playing_text = "Test Track"
        assert widget.render() == "Now playing: Test Track!"


class TestPlayControlPlayButton:
    """Tests for PlayControl play button behavior."""

    def test_empty_playlist_no_client_call(
        self, mock_client: MagicMock, empty_playlist: MagicMock
    ) -> None:
        """Test play button does not call client when playlist is empty."""
        control = PlayControl(mock_client, empty_playlist)
        event = MagicMock()
        event.button.id = BUTTON_PLAY

        control.on_button_pressed(event)

        mock_client.play.assert_not_called()

    def test_with_selection_calls_client(
        self, mock_client: MagicMock, populated_playlist: MagicMock
    ) -> None:
        """Test play button calls client.play with correct rank."""
        control = PlayControl(mock_client, populated_playlist)
        event = MagicMock()
        event.button.id = BUTTON_PLAY

        control.on_button_pressed(event)

        mock_client.play.assert_called_once_with(rank=0)

    def test_with_none_row_key_no_client_call(
        self, mock_client: MagicMock, playlist_with_none_row_key: MagicMock
    ) -> None:
        """Test play button does not call client when row_key is None."""
        control = PlayControl(mock_client, playlist_with_none_row_key)
        event = MagicMock()
        event.button.id = BUTTON_PLAY

        control.on_button_pressed(event)

        mock_client.play.assert_not_called()


class TestPlayControlOtherButtons:
    """Tests for pause, stop, previous, next buttons."""

    @pytest.mark.parametrize(
        "button_id,client_method",
        [
            (BUTTON_PAUSE, "pause"),
            (BUTTON_STOP, "stop"),
            (BUTTON_PREVIOUS, "previous"),
            (BUTTON_NEXT, "next"),
        ],
    )
    def test_buttons_call_client_methods(
        self,
        mock_client: MagicMock,
        empty_playlist: MagicMock,
        button_id: str,
        client_method: str,
    ) -> None:
        """Test control buttons call their respective client methods."""
        control = PlayControl(mock_client, empty_playlist)
        event = MagicMock()
        event.button.id = button_id

        control.on_button_pressed(event)

        getattr(mock_client, client_method).assert_called_once()
