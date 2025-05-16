"""Onzr: http server."""

import logging

from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from vlc import Instance

from .config import get_settings
from .core import Queue
from .deezer import DeezerClient, StreamQuality, Track

logger = logging.getLogger(__name__)

settings = get_settings()

deezer: DeezerClient = DeezerClient(
    arl=settings.arl,
    blowfish=settings.DEEZER_BLOWFISH_SECRET,
    multicast_group=settings.MULTICAST_GROUP,
)

queue: Queue = Queue()

vlc_instance = Instance()
medialist = vlc_instance.media_list_new()
player = vlc_instance.media_list_player_new()
player.set_media_list(medialist)

# FIXME: should be configurable
# quality = StreamQuality.FLAC
# media_type = "audio/flac"
quality = StreamQuality.MP3_128
media_type = "audio/mpeg"

logger.info("Starting Onzr server…")


async def queue_tracks(request):
    """Add tracks to queue given its identifier."""
    track_ids = await request.json()
    start = len(queue)
    tracks = [Track(deezer, id_, quality) for id_ in track_ids]
    queue.add(tracks=tracks)
    rank = start
    for rank in range(start, len(queue), 1):
        media = vlc_instance.media_new(f"http://localhost:9473/queue/{rank}/stream")
        medialist.add_media(media)
    return JSONResponse({"status": "added"})


async def stream_track(request):
    """Stream Deezer track given its identifer."""
    rank = int(request.path_params["rank"])
    track = queue[rank]
    print(f"Now playing: {track.full_title}")
    return StreamingResponse(track.stream(), media_type=media_type)


async def play(request):
    """Start playing current queue."""
    player.play()
    return JSONResponse({"player": "play"})


async def pause(request):
    """Pause/resume playing."""
    player.pause()
    return JSONResponse({"player": "paused"})


async def next(request):
    """Play next track in queue."""
    player.next()
    return JSONResponse({"player": "next"})


async def previous(request):
    """Play previous track in queue."""
    player.previous()
    return JSONResponse({"player": "previous"})


async def stop(request):
    """Stop playing."""
    player.stop()
    return JSONResponse({"player": "stop"})


async def state(request):
    """Stop playing."""
    return JSONResponse({"state": str(player.get_state())})


app = Starlette(
    debug=True,
    routes=[
        Route("/queue/{rank}/stream", stream_track),
        Route("/queue/", queue_tracks, methods=["POST"]),
        Route("/play", play, methods=["POST"]),
        Route("/pause", pause, methods=["POST"]),
        Route("/next", next, methods=["POST"]),
        Route("/previous", previous, methods=["POST"]),
        Route("/stop", stop, methods=["POST"]),
        Route("/state", state),
    ],
)
