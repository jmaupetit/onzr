"""Onzr server tests."""

from io import BytesIO
from time import sleep
from unittest.mock import patch

import pytest
import requests
from fastapi import status

from onzr.models.core import PlayingState

from .factories import DeezerSongFactory, DeezerSongResponseFactory


def test_queue_add_empty(client, responses, configured_onzr):
    """Test the POST /queue/ endpoint."""
    track_ids = []
    assert len(configured_onzr.queue.tracks) == 0

    response = client.post("/queue/", json=track_ids)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == f"Added {len(track_ids)} track(s) to queue"
    assert len(configured_onzr.queue.tracks) == 0
    for track, expected in zip(configured_onzr.queue.tracks, track_ids, strict=True):
        assert track.track_id == expected


def test_queue_add(client, configured_onzr, song_data, wait_for_requests):
    """Test the POST /queue/ endpoint."""
    track_ids = [1, 2, 3]

    assert len(configured_onzr.queue.tracks) == 0

    response = client.post("/queue/", json=track_ids)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == f"Added {len(track_ids)} track(s) to queue"

    # Track information are fetched in background threads: wait for the
    # mocked requests to be executed before leaving the test.
    wait_for_requests()

    assert len(configured_onzr.queue.tracks) == len(track_ids)
    for track, expected in zip(configured_onzr.queue.tracks, track_ids, strict=True):
        assert track.track_id == expected


def test_queue_clear(client, configured_onzr, track):
    """Test the DELETE /queue/ endpoint."""
    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Empty queue using the API
    response = client.delete("/queue/")
    state = response.json()
    assert state["player"] == "State.Stopped"
    assert state["queue"] == {"playing": None, "queued": 0}
    assert len(configured_onzr.queue) == 0
    assert configured_onzr.queue.is_empty


def test_queue_clear_empty(client, configured_onzr, track):
    """Test the DELETE /queue/ endpoint when the queue is empty."""
    assert configured_onzr.queue.is_empty

    # Empty queue using the API
    response = client.delete("/queue/")
    state = response.json()
    assert state["player"] == "State.Stopped"
    assert state["queue"] == {"playing": None, "queued": 0}
    assert len(configured_onzr.queue) == 0
    assert configured_onzr.queue.is_empty


def test_queue_list(client, configured_onzr, track):
    """Test the GET /queue/ endpoint."""
    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # List queue using the API
    response = client.get("/queue/")
    queue = response.json()
    assert queue["playing"] is None
    assert len(queue["tracks"]) == len(track_ids)
    for t, id_ in zip(queue["tracks"], track_ids, strict=True):
        assert t["track"]["id"] == id_


def test_queue_list_empty(client, configured_onzr, track):
    """Test the GET /queue/ endpoint when the queue is empty."""
    # List queue using the API
    response = client.get("/queue/")
    queue = response.json()
    assert queue["playing"] is None
    assert len(queue["tracks"]) == 0


def test_stream_track_empty_queue(client):
    """Test the GET /queue/{rank}/stream endpoint when queue is empty."""
    with client.stream("GET", "/queue/10/stream") as response:
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_stream_track_out_of_range(client, configured_onzr, track):
    """Test the GET /queue/{rank}/stream endpoint when rank is out of range."""
    # Fill queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    with client.stream("GET", "/queue/3/stream") as response:
        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_stream_track(client, responses, configured_onzr, track):
    """Test the GET /queue/{rank}/stream endpoint."""
    # Fill queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Track info refresh request
    responses.post(
        "http://www.deezer.com/ajax/gw-light.php",
        status=200,
        json=DeezerSongResponseFactory.build(
            error={}, results=DeezerSongFactory.build(SNG_ID=666)
        ).model_dump(),
    )
    rank = 1
    with client.stream("GET", f"/queue/{rank}/stream") as response:
        assert response.status_code == status.HTTP_200_OK
        song_file = BytesIO()
        for chunk in response.iter_raw():
            song_file.write(chunk)

    # Read the file magic number
    song_file.seek(0)
    magic = song_file.read(3)
    # It should match an mp3 file
    assert magic == b"ID3"

    # Now playing rank should be up to date
    assert configured_onzr.queue.playing == rank


def test_now_playing_empty(client, configured_onzr, track):
    """Test the GET /now endpoint when the queue is empty."""
    response = client.get("/now")
    state = PlayingState(**response.json())
    assert state.player.length == -1
    assert state.player.position == -1.0
    assert state.player.state == "State.NothingSpecial"
    assert state.player.time == -1
    assert state.track is None


def test_now_playing(client, configured_onzr, track):
    """Test the GET /now endpoint."""
    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Play
    #
    # Nota bene: the test client does not serve HTTP requests, VLC cannot fetch the
    # track stream, hence the player fails and is automatically stopped.
    configured_onzr.player.play()
    sleep(0.5)

    response = client.get("/now")
    state = PlayingState(**response.json())
    assert state.player.length == -1
    assert state.player.position == -1
    assert state.player.state == "State.Stopped"
    assert state.player.time == -1
    assert state.track is None


def test_play(client, configured_onzr, track):
    """Test the POST /play endpoint."""
    with patch.object(configured_onzr.player, "play", return_value=None) as mocked_play:
        response = client.post("/play", json={})
        status = response.json()
        # Queue is empty
        assert status == {
            "action": "play",
            "state": {
                "player": "State.NothingSpecial",
                "queue": {"playing": None, "queued": 0},
            },
        }
        assert mocked_play.called

    # Add tracks to queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])

    # Start playing
    #
    # Nota bene: the test client does not serve HTTP requests, VLC cannot fetch the
    # track stream, hence the player ends (we disable automatic failure handling to
    # avoid race conditions).
    with patch.object(configured_onzr, "_skip_failed"):
        response = client.post("/play", json={})
    status = response.json()
    assert status == {
        "action": "play",
        "state": {
            "player": "State.Ended",
            "queue": {"playing": None, "queued": 3},
        },
    }


def test_pause(client, configured_onzr):
    """Test the POST /pause endpoint."""
    with patch.object(
        configured_onzr.player, "pause", return_value=None
    ) as mocked_pause:
        response = client.post("/pause")
        status = response.json()
        # Queue is empty
        assert status == {
            "action": "pause",
            "state": {
                "player": "State.NothingSpecial",
                "queue": {"playing": None, "queued": 0},
            },
        }
        assert mocked_pause.called

    # FIXME
    # Should play something first and then pause


def test_stop(client, configured_onzr):
    """Test the POST /stop endpoint."""
    with patch.object(configured_onzr.player, "stop", return_value=None) as mocked_stop:
        response = client.post("/stop")
        status = response.json()
        # Queue is empty
        assert status == {
            "action": "stop",
            "state": {
                "player": "State.NothingSpecial",
                "queue": {"playing": None, "queued": 0},
            },
        }
        assert mocked_stop.called

    # FIXME
    # Should play something first and then stop


def test_next(client, configured_onzr):
    """Test the POST /next endpoint."""
    with patch.object(configured_onzr.player, "next", return_value=None) as mocked_next:
        response = client.post("/next")
        status = response.json()
        # Queue is empty
        assert status == {
            "action": "next",
            "state": {
                "player": "State.NothingSpecial",
                "queue": {"playing": None, "queued": 0},
            },
        }
        assert mocked_next.called

    # FIXME
    # Should play something first and then next


def test_previous(client, configured_onzr, track):
    """Test the POST /previous endpoint."""
    with patch.object(
        configured_onzr.player, "previous", return_value=None
    ) as mocked_previous:
        response = client.post("/previous")
        status = response.json()
        # Queue is empty
        assert status == {
            "action": "previous",
            "state": {
                "player": "State.NothingSpecial",
                "queue": {"playing": None, "queued": 0},
            },
        }
        assert mocked_previous.called

    # FIXME
    # Should play something first and then previous


def test_state(client, configured_onzr, track):
    """Test the GET /state endpoint."""
    response = client.get("/state")
    state = response.json()
    # Queue is empty
    assert state == {
        "player": "State.NothingSpecial",
        "queue": {"playing": None, "queued": 0},
    }

    # Start playing
    configured_onzr.player.play()
    response = client.get("/state")
    state = response.json()
    # Queue is still empty
    assert state == {
        "player": "State.NothingSpecial",
        "queue": {"playing": None, "queued": 0},
    }

    # Add tracks to queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])

    # Start playing for real
    configured_onzr.player.play()
    response = client.get("/state")
    state = response.json()
    assert state == {
        "player": "State.Opening",
        # FIXME
        # Should mock queue.playing
        "queue": {"playing": None, "queued": 3},
    }


def test_ping(client):
    """Test the GET /ping endpoint."""
    response = client.get("/ping")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is None


def test_stream_track_refresh_failure(client, configured_onzr, track):
    """Test the GET /queue/{rank}/stream endpoint when track refresh fails."""
    configured_onzr.queue.add([track(1)])

    with patch.object(
        configured_onzr.queue[0], "refresh", side_effect=ValueError("ARL expired")
    ):
        with client.stream("GET", "/queue/0/stream") as response:
            assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert configured_onzr.queue.playing == 0


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.ConnectionError("Connection refused"),
        requests.exceptions.ReadTimeout("Read timed out"),
        requests.exceptions.HTTPError("403 Forbidden"),
        StopIteration(),
    ],
)
def test_stream_track_stream_failure(client, configured_onzr, track, error):
    """Test the GET /queue/{rank}/stream endpoint when track stream fails."""
    configured_onzr.queue.add([track(1)])

    def failing_stream(*args, **kwargs):
        raise error
        yield b""  # pragma: no cover

    with (
        patch.object(configured_onzr.queue[0], "refresh"),
        patch.object(configured_onzr.queue[0], "stream", failing_stream),
    ):
        with client.stream("GET", "/queue/0/stream") as response:
            assert response.status_code == status.HTTP_502_BAD_GATEWAY


def test_stream_track_timeout(client, configured_onzr, track, settings):
    """Test the GET /queue/{rank}/stream endpoint passes the stream timeout."""
    configured_onzr.queue.add([track(1)])

    with (
        patch.object(configured_onzr.queue[0], "refresh"),
        patch.object(
            configured_onzr.queue[0], "stream", return_value=iter([b"ID3"])
        ) as mocked_stream,
    ):
        with client.stream("GET", "/queue/0/stream") as response:
            assert response.status_code == status.HTTP_200_OK
            assert response.read() == b"ID3"
    assert mocked_stream.call_args.kwargs["timeout"] == settings.STREAM_TIMEOUT
