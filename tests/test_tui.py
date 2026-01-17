"""Onzr TUI tests."""

from unittest.mock import MagicMock

from textual.coordinate import Coordinate

from onzr.tui import PlayControl, PlayStatusWidget


def test_play_status_widget_render_with_track():
    """Test that PlayStatusWidget renders correctly with and without a track."""
    widget = PlayStatusWidget()

    # Test default render
    assert widget.render() == "Now playing: Nothing!"

    # Test with specific track name
    widget.now_playing_text = "Test Track"
    assert widget.render() == "Now playing: Test Track!"


def test_play_button_empty_playlist_no_client_call():
    """Test that play button does not call client.play when playlist is empty."""
    # Create a mock client with all methods mocked
    mock_client = MagicMock()
    mock_client.play = MagicMock()
    mock_client.pause = MagicMock()
    mock_client.stop = MagicMock()
    mock_client.previous = MagicMock()
    mock_client.next = MagicMock()

    # Create an empty playlist
    empty_playlist = MagicMock()
    empty_playlist.row_count = 0

    # Create PlayControl with mock client and empty playlist
    control = PlayControl(mock_client, empty_playlist)

    # Mock button press event for play button
    event = MagicMock()
    event.button.id = "play"

    # Call the button pressed handler
    control.on_button_pressed(event)

    # Verify that client.play was never called
    mock_client.play.assert_not_called()


def test_play_button_with_selection_calls_client():
    """Test that play button calls client.play when playlist has selection."""
    # Create a mock client with all methods mocked
    mock_client = MagicMock()
    mock_client.play = MagicMock()
    mock_client.pause = MagicMock()
    mock_client.stop = MagicMock()
    mock_client.previous = MagicMock()
    mock_client.next = MagicMock()

    # Create a playlist with data
    playlist = MagicMock()
    playlist.row_count = 2
    playlist.cursor_coordinate = Coordinate(0, 0)
    playlist.coordinate_to_cell_key = MagicMock(return_value=("row_key", None))

    # Create PlayControl with mock client and populated playlist
    control = PlayControl(mock_client, playlist)

    # Mock button press event for play button
    event = MagicMock()
    event.button.id = "play"

    # Call the button pressed handler
    control.on_button_pressed(event)

    # Verify that client.play was called with correct rank
    mock_client.play.assert_called_once_with(rank=0)
