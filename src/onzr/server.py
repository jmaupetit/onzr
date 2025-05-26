"""Onzr: http server."""

import logging
from typing import Annotated, List

from fastapi import FastAPI, Path
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from vlc import Instance

from .config import get_settings
from .core import Queue
from .deezer import DeezerClient, Track

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="Onzr", root_path=settings.API_ROOT_URL, debug=settings.DEBUG)

deezer: DeezerClient = DeezerClient(
    arl=settings.ARL, blowfish=settings.DEEZER_BLOWFISH_SECRET, fast=False
)


vlc_instance = Instance()
medialist = vlc_instance.media_list_new()
player = vlc_instance.media_list_player_new()
player.set_media_list(medialist)

queue: Queue = Queue(playlist=medialist)

logger.info("Starting Onzr server…")


@app.post("/queue/")
async def queue_tracks(track_ids: List[int]):
    """Add tracks to queue given their identifiers."""
    tracks = [Track(deezer, str(id_), background=True) for id_ in track_ids]
    queue.add(tracks=tracks)
    return JSONResponse({"status": "added"})


@app.delete("/queue/")
async def queue_clear():
    """Clear tracks queue."""
    player.stop()
    queue.clear()
    return JSONResponse({"queue": "empty"})


@app.get("/queue/")
async def queue_list():
    """List queue tracks."""
    return JSONResponse(
        [
            {"current": p == queue.playing, "position": p, "track": t.as_dict()}
            for p, t in enumerate(queue.tracks)
        ]
    )


@app.get(settings.TRACK_STREAM_ENDPOINT)
async def stream_track(
    track_id: Annotated[int, Path(title="Deezer track identifier")],
) -> StreamingResponse:
    """Stream Deezer track given its identifer."""
    quality = settings.QUALITY
    rank = queue.index_for_id(str(track_id))
    queue.playing = rank
    track = queue[rank]
    return StreamingResponse(track.stream(quality), media_type=quality.media_type)


@app.get("/now")
async def now_playing():
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


@app.post("/play")
async def play():
    """Start playing current queue."""
    player.play()
    # Get track that will be played info
    return JSONResponse({"player": "play"})


@app.post("/pause")
async def pause():
    """Pause/resume playing."""
    player.pause()
    # Get curent track info
    return JSONResponse({"player": "paused"})


@app.post("/stop")
async def stop():
    """Stop playing."""
    player.stop()
    return JSONResponse({"player": "stop"})


@app.post("/next")
async def next():
    """Play next track in queue."""
    player.next()
    # Get next track info
    return JSONResponse({"player": "next"})


@app.post("/previous")
async def previous():
    """Play previous track in queue."""
    player.previous()
    # Get previous track info
    return JSONResponse({"player": "previous"})


@app.get("/state")
async def state():
    """Player state."""
    return JSONResponse({"state": str(player.get_state())})


# app = Starlette(
#     debug=settings.DEBUG,
#     routes=[
#         Mount(
#             settings.API_ROOT_URL,
#             routes=[
#                 Route(settings.TRACK_STREAM_ENDPOINT, stream_track),
#                 Route("/queue/clear", queue_clear, methods=["POST"]),
#                 Route("/queue/", queue_tracks, methods=["POST"]),
#                 Route("/queue/", queue_list, methods=["GET"]),
#                 Route("/now", now_playing, methods=["GET"]),
#                 Route("/play", play, methods=["POST"]),
#                 Route("/pause", pause, methods=["POST"]),
#                 Route("/stop", stop, methods=["POST"]),
#                 Route("/next", next, methods=["POST"]),
#                 Route("/previous", previous, methods=["POST"]),
#                 Route("/state", state),
#             ],
#         )
#     ],
# )
