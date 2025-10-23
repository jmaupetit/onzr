"""Onzr client tests."""

from time import sleep

from onzr.client import OnzrClient
from onzr.models import (
    PlayerControl,
    PlayerState,
    PlayingState,
    QueuedTracks,
    QueueState,
    ServerMessage,
    ServerState,
)

from .factories import DeezerSongFactory, DeezerSongResponseFactory


def test_queue_add(test_server, responses):
    """Test the `queue_add` method."""
    client = OnzrClient()

    track_ids = [1, 2, 3]
    for track_id in track_ids:
        responses.post(
            "http://www.deezer.com/ajax/gw-light.php",
            status=200,
            json=DeezerSongResponseFactory.build(
                error={}, results=DeezerSongFactory.build(SNG_ID=track_id)
            ).model_dump(),
        )

    assert client.queue_add([str(t) for t in track_ids]) == ServerMessage(
        message="Added 3 track(s) to queue"
    )


def test_queue_clear(test_server, configured_onzr, track):
    """Test the `queue_add` method."""
    # Empty queue
    client = OnzrClient()
    assert client.queue_clear() == ServerState(
        player="State.Stopped", queue=QueueState(playing=None, queued=0)
    )
    assert len(configured_onzr.queue) == 0
    assert configured_onzr.queue.is_empty

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    assert client.queue_clear() == ServerState(
        player="State.Stopped", queue=QueueState(playing=None, queued=0)
    )
    assert len(configured_onzr.queue) == 0
    assert configured_onzr.queue.is_empty


def test_queue_list(test_server, configured_onzr, track):
    """Test the `queue_list` method."""
    # Empty queue
    client = OnzrClient()
    assert client.queue_list() == QueuedTracks(playing=None, tracks=[])

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    queued_tracks = client.queue_list()
    assert isinstance(queued_tracks, QueuedTracks)
    assert queued_tracks.playing is None
    assert len(queued_tracks.tracks) == len(track_ids)


def test_now_playing(test_server, configured_onzr, track):
    """Test the `now_playing` method."""
    client = OnzrClient()

    # Empty queue
    assert client.now_playing() == PlayingState(
        player=PlayerState(
            state="State.NothingSpecial", length=-1, time=-1, position=-1.0
        ),
        track=None,
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    configured_onzr.player.play()

    assert client.now_playing() == PlayingState(
        player=PlayerState(state="State.Opening", length=0, time=0, position=0.0),
        track=None,
    )

    # Stop the player
    configured_onzr.player.stop()


def test_state(test_server, configured_onzr, track):
    """Test the `state` method."""
    client = OnzrClient()

    # Empty queue
    assert client.state() == ServerState(
        player="State.NothingSpecial", queue=QueueState(playing=None, queued=0)
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Start playing
    configured_onzr.player.play()

    assert client.state() == ServerState(
        player="State.Opening", queue=QueueState(playing=None, queued=3)
    )

    # Stop the player
    configured_onzr.player.stop()


def test_ping_server_down(configured_onzr):
    """Test the `ping` method when the server is down."""
    client = OnzrClient()
    assert client.ping() is False


def test_ping_server(test_server, configured_onzr):
    """Test the `ping` method when the server is down."""
    client = OnzrClient()
    assert client.ping()


def test_play(test_server, configured_onzr, track):
    """Test the `play` method."""
    client = OnzrClient()

    # Empty queue
    assert client.play() == PlayerControl(
        action="play",
        state=ServerState(
            player="State.NothingSpecial", queue=QueueState(playing=None, queued=0)
        ),
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Start playing: should be opening the file
    assert client.play() == PlayerControl(
        action="play",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=None, queued=3)
        ),
    )

    # Wait a bit and we should really be playing something
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )

    # Start playing from a queue index (aka rank)
    assert client.play(rank=1) == PlayerControl(
        action="play",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=0, queued=3)
        ),
    )

    # Wait a bit and we should have switched to rank 1 track
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=1, queued=3)
    )


def test_pause(test_server, configured_onzr, track):
    """Test the `pause` method."""
    client = OnzrClient()

    # Empty queue
    assert client.pause() == PlayerControl(
        action="pause",
        state=ServerState(
            player="State.NothingSpecial", queue=QueueState(playing=None, queued=0)
        ),
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Start playing: should be opening the file
    configured_onzr.player.play()

    # Wait a bit and we should really be playing something
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )

    # Start playing from a queue index (aka rank)
    assert client.pause() == PlayerControl(
        action="pause",
        state=ServerState(player="State.Paused", queue=QueueState(playing=0, queued=3)),
    )

    # Toggle pause
    assert client.pause() == PlayerControl(
        action="pause",
        state=ServerState(
            player="State.Playing", queue=QueueState(playing=0, queued=3)
        ),
    )


def test_stop(test_server, configured_onzr, track):
    """Test the `stop` method."""
    client = OnzrClient()

    # Empty queue
    assert client.stop() == PlayerControl(
        action="stop",
        state=ServerState(
            player="State.Stopped", queue=QueueState(playing=None, queued=0)
        ),
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Start playing: should be opening the file
    configured_onzr.player.play()

    # Wait a bit and we should really be playing something
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )

    # Stop playing
    assert client.stop() == PlayerControl(
        action="stop",
        state=ServerState(
            player="State.Stopped", queue=QueueState(playing=0, queued=3)
        ),
    )


def test_next(test_server, configured_onzr, track):
    """Test the `next` method."""
    client = OnzrClient()

    # Empty queue
    assert client.next() == PlayerControl(
        action="next",
        state=ServerState(
            player="State.NothingSpecial", queue=QueueState(playing=None, queued=0)
        ),
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Should start playing first track in queue
    assert client.next() == PlayerControl(
        action="next",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=None, queued=3)
        ),
    )

    # Wait a bit and we should really be playing something
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )

    # Next track
    assert client.next() == PlayerControl(
        action="next",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=0, queued=3)
        ),
    )

    # Wait a bit and we should be playing the next track
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=1, queued=3)
    )


def test_previous(test_server, configured_onzr, track):
    """Test the `previous` method."""
    client = OnzrClient()

    # Empty queue
    assert client.previous() == PlayerControl(
        action="previous",
        state=ServerState(
            player="State.NothingSpecial", queue=QueueState(playing=None, queued=0)
        ),
    )

    # Fill the queue
    track_ids = [1, 2, 3]
    configured_onzr.queue.add([track(track_id) for track_id in track_ids])
    assert len(configured_onzr.queue) == len(track_ids)

    # Should start playing first track in queue
    assert client.previous() == PlayerControl(
        action="previous",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=None, queued=3)
        ),
    )
    # Wait a bit and we should really be playing something
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )

    # Previous should restart current track from the beginning
    assert client.previous() == PlayerControl(
        action="previous",
        state=ServerState(
            player="State.Playing", queue=QueueState(playing=0, queued=3)
        ),
    )
    # Wait a bit and we should be playing the previous track
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )

    # Play track 2
    configured_onzr.player.play_item_at_index(2)
    assert client.previous() == PlayerControl(
        action="previous",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=0, queued=3)
        ),
    )
    # Wait a bit and we should be playing the previous track
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=1, queued=3)
    )

    # Again?
    assert client.previous() == PlayerControl(
        action="previous",
        state=ServerState(
            player="State.Opening", queue=QueueState(playing=1, queued=3)
        ),
    )
    # Wait a bit and we should be playing the previous track
    sleep(0.1)
    assert client.state() == ServerState(
        player="State.Playing", queue=QueueState(playing=0, queued=3)
    )
