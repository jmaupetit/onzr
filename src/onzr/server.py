"""Onzr: http server."""

import logging
from enum import IntEnum

from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Mount, Route
from vlc import Instance

from .config import get_settings
from .core import Queue
from .deezer import DeezerClient, Track

logger = logging.getLogger(__name__)

settings = get_settings()

deezer: DeezerClient = DeezerClient(
    arl=settings.ARL, blowfish=settings.DEEZER_BLOWFISH_SECRET, fast=False
)


vlc_instance = Instance()
medialist = vlc_instance.media_list_new()
player = vlc_instance.media_list_player_new()
player.set_media_list(medialist)

queue: Queue = Queue(playlist=medialist)

logger.info("Starting Onzr server…")


async def queue_tracks(request):
    """Add tracks to queue given their identifiers."""
    track_ids = await request.json()
    tracks = [Track(deezer, id_, background=True) for id_ in track_ids]
    queue.add(tracks=tracks)
    return JSONResponse({"status": "added"})


async def queue_clear(request):
    """Clear tracks queue."""
    player.stop()
    queue.clear()
    return JSONResponse({"queue": "empty"})


async def queue_list(request):
    """List queue tracks."""
    return JSONResponse(
        [
            {"current": p == queue.playing, "position": p, "track": t.as_dict()}
            for p, t in enumerate(queue.tracks)
        ]
    )


async def stream_track(request):
    """Stream Deezer track given its identifer."""
    quality = settings.QUALITY
    track_id = request.path_params["track_id"]
    rank = queue.index_for_id(track_id)
    queue.playing = rank
    track = queue[rank]
    return StreamingResponse(track.stream(quality), media_type=quality.media_type)


async def now_playing(request):
    """Get info about current track."""
    track = queue.current
    if track is None:
        return JSONResponse({"playing": None})
    media_player = player.get_media_player()
    return JSONResponse(
        {
            "player": {
                "state": str(media_player.get_state()),
                "length": media_player.get_length(),
                "time": media_player.get_time(),
                "position": media_player.get_position(),
            },
            "track": track.as_dict(),
        }
    )


async def play(request):
    """Start playing current queue."""
    player.play()
    return JSONResponse({"player": "play"})


async def pause(request):
    """Pause/resume playing."""
    player.pause()
    return JSONResponse({"player": "paused"})


async def stop(request):
    """Stop playing."""
    player.stop()
    return JSONResponse({"player": "stop"})


async def next(request):
    """Play next track in queue."""
    player.next()
    return JSONResponse({"player": "next"})


async def previous(request):
    """Play previous track in queue."""
    player.previous()
    return JSONResponse({"player": "previous"})


async def state(request):
    """Player state."""
    return JSONResponse({"state": str(player.get_state())})


app = Starlette(
    debug=settings.DEBUG,
    routes=[
        Mount(
            settings.API_ROOT_URL,
            routes=[
                Route(settings.TRACK_STREAM_ENDPOINT, stream_track),
                Route("/queue/clear", queue_clear, methods=["POST"]),
                Route("/queue/", queue_tracks, methods=["POST"]),
                Route("/queue/", queue_list, methods=["GET"]),
                Route("/now", now_playing, methods=["GET"]),
                Route("/play", play, methods=["POST"]),
                Route("/pause", pause, methods=["POST"]),
                Route("/stop", stop, methods=["POST"]),
                Route("/next", next, methods=["POST"]),
                Route("/previous", previous, methods=["POST"]),
                Route("/state", state),
            ],
        )
    ],
)
