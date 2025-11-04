"""Onzr: http server."""

import logging
from functools import lru_cache
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, Path, status
from fastapi.responses import StreamingResponse

from .config import get_settings
from .core import Onzr
from .deezer import Track
from .models import (
    PlayerControl,
    PlayerState,
    PlayingState,
    PlayQueryParams,
    QueuedTracks,
    ServerMessage,
    ServerState,
)

logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title="Onzr", root_path=settings.API_ROOT_URL, debug=settings.DEBUG)


@lru_cache
def get_onzr() -> Onzr:
    """Get Onzr core instance."""
    return Onzr()


# --- Routes


@app.post("/queue/")
async def queue_add(
    onzr: Annotated[Onzr, Depends(get_onzr)],
    track_ids: List[int],
) -> ServerMessage:
    """Add tracks to queue given their identifiers."""
    tracks = [Track(onzr.deezer, id_, background=True) for id_ in track_ids]
    onzr.queue.add(tracks=tracks)
    return ServerMessage(message=f"Added {len(tracks)} track(s) to queue")


@app.delete("/queue/")
async def queue_clear(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> ServerState:
    """Clear tracks queue."""
    onzr.player.stop()
    onzr.queue.clear()
    return onzr.state()


@app.get("/queue/")
async def queue_list(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> QueuedTracks:
    """List queue tracks."""
    return onzr.queue.serialize()


@app.get(settings.TRACK_STREAM_ENDPOINT)
async def stream_track(
    onzr: Annotated[Onzr, Depends(get_onzr)],
    rank: Annotated[int, Path(title="Track queue rank")],
) -> StreamingResponse:
    """Stream Deezer track given its identifer."""
    if onzr.queue.is_empty:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT, detail="Queue is empty."
        )
    if rank >= len(onzr.queue):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Track rank out of range."
        )
    onzr.queue.playing = rank
    track = onzr.queue[rank]
    # Refresh track token in case it expired
    track.refresh()
    quality = track.query_quality(settings.QUALITY)
    return StreamingResponse(track.stream(quality), media_type=quality.media_type)


@app.get("/now")
async def now_playing(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> PlayingState:
    """Get info about current track."""
    track = onzr.queue.current
    media_player = onzr.player.get_media_player()
    length: int = media_player.get_length()
    if track and length == 0:
        logger.debug("Player cannot guess track length. Falling back to track info.")
        length = track.duration * 1000 if isinstance(track.duration, int) else 0
    return PlayingState(
        player=PlayerState(
            state=str(media_player.get_state()),
            length=length,
            time=media_player.get_time(),
            position=media_player.get_position(),
        ),
        track=track.serialize() if track else None,
    )


@app.post("/play")
async def play(
    onzr: Annotated[Onzr, Depends(get_onzr)], params: PlayQueryParams
) -> PlayerControl:
    """Start playing current queue."""
    if params.rank is not None:
        # TODO: rank should be < len(queue)
        onzr.player.play_item_at_index(params.rank)
    else:
        onzr.player.play()
    return PlayerControl(action="play", state=onzr.state())


@app.post("/pause")
async def pause(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> PlayerControl:
    """Pause/resume playing."""
    onzr.player.pause()
    return PlayerControl(action="pause", state=onzr.state())


@app.post("/stop")
async def stop(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> PlayerControl:
    """Stop playing."""
    onzr.player.stop()
    return PlayerControl(action="stop", state=onzr.state())


@app.post("/next")
async def next(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> PlayerControl:
    """Play next track in queue."""
    onzr.player.next()
    return PlayerControl(action="next", state=onzr.state())


@app.post("/previous")
async def previous(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> PlayerControl:
    """Play previous track in queue."""
    onzr.player.previous()
    return PlayerControl(action="previous", state=onzr.state())


@app.get("/state")
async def state(
    onzr: Annotated[Onzr, Depends(get_onzr)],
) -> ServerState:
    """Server state."""
    return onzr.state()


@app.get("/ping")
async def ping() -> None:
    """Server ping."""
    return
