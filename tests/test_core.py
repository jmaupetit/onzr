"""Onzr core tests."""

from unittest.mock import patch


def test_onzr_skip_failed_next(configured_onzr, track):
    """Test failed track is skipped when it's not the last queued track."""
    configured_onzr.queue.add([track(1), track(2), track(3)])
    configured_onzr.queue.playing = 1

    with (
        patch.object(configured_onzr.player, "next") as mocked_next,
        patch.object(configured_onzr.player, "stop") as mocked_stop,
    ):
        configured_onzr._skip_failed()
    mocked_next.assert_called_once()
    mocked_stop.assert_not_called()
    assert configured_onzr._consecutive_failures == 1


def test_onzr_skip_failed_last_track(configured_onzr, track):
    """Test player stops when the last queued track fails."""
    configured_onzr.queue.add([track(1), track(2)])
    configured_onzr.queue.playing = 1

    with (
        patch.object(configured_onzr.player, "next") as mocked_next,
        patch.object(configured_onzr.player, "stop") as mocked_stop,
    ):
        configured_onzr._skip_failed()
    mocked_next.assert_not_called()
    mocked_stop.assert_called_once()


def test_onzr_skip_failed_no_playing_track(configured_onzr, track):
    """Test player stops when failing before any track has been streamed."""
    configured_onzr.queue.add([track(1), track(2)])
    assert configured_onzr.queue.playing is None

    with (
        patch.object(configured_onzr.player, "next") as mocked_next,
        patch.object(configured_onzr.player, "stop") as mocked_stop,
    ):
        configured_onzr._skip_failed()
    mocked_next.assert_not_called()
    mocked_stop.assert_called_once()


def test_onzr_skip_failed_max_consecutive_failures(configured_onzr, track, settings):
    """Test player stops after too many consecutive failures."""
    configured_onzr.queue.add([track(i) for i in range(10)])
    configured_onzr.queue.playing = 0

    with (
        patch.object(configured_onzr.player, "next") as mocked_next,
        patch.object(configured_onzr.player, "stop") as mocked_stop,
    ):
        for _ in range(settings.MAX_CONSECUTIVE_FAILURES):
            configured_onzr._skip_failed()
    assert mocked_next.call_count == settings.MAX_CONSECUTIVE_FAILURES - 1
    mocked_stop.assert_called_once()


def test_onzr_on_playing_resets_failures(configured_onzr):
    """Test the playing event resets the consecutive failures counter."""
    configured_onzr._consecutive_failures = 3
    configured_onzr._on_playing(None)
    assert configured_onzr._consecutive_failures == 0


def test_onzr_on_error_skips_in_thread(configured_onzr):
    """Test the error event handler skips the failed track from a new thread."""
    with patch("onzr.core.threading.Thread") as mocked_thread:
        configured_onzr._on_error(None)
    mocked_thread.assert_called_once_with(
        target=configured_onzr._skip_failed, daemon=True
    )
    mocked_thread.return_value.start.assert_called_once()
