"""Onzr: Pydantic models."""

from pydantic import BaseModel


class QueueState(BaseModel):
    """Queue state."""

    playing: int | None
    queued: int


class ServerState(BaseModel):
    """Onzr server state."""

    # Does not support VLC Enums
    player: str
    queue: QueueState


class PlayerControl(BaseModel):
    """Player controls."""

    action: str
    state: ServerState
