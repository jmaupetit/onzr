"""Onzr: http client."""

from typing import Annotated, List, Optional

import requests
from annotated_types import Ge

from .config import get_settings
from .models import (
    PlayerControl,
    PlayingState,
    PlayQueryParams,
    QueuedTracks,
    ServerMessage,
    ServerState,
)


class OnzrClient:
    """Onzr API client."""

    def __init__(self):
        """Initialize Onzr API client."""
        self.http_headers = {
            "User-Agent": "Onzr Client",
        }
        self.session = requests.session()
        self.session.headers = self.http_headers

        settings = get_settings()
        self.base_url = settings.SERVER_BASE_URL
        self.ping_timeout = settings.PING_TIMEOUT

    # Queue
    def queue_add(self, track_ids: List[str]) -> ServerMessage:
        """Add tracks to queue given their identifiers."""
        response = self.session.post(f"{self.base_url}/queue/", json=track_ids)
        return ServerMessage.model_validate_json(response.text)

    def queue_clear(self) -> ServerState:
        """Clear tracks queue."""
        response = self.session.delete(f"{self.base_url}/queue/")
        return ServerState.model_validate_json(response.text)

    def queue_list(self) -> QueuedTracks:
        """List queue tracks."""
        response = self.session.get(f"{self.base_url}/queue/")
        return QueuedTracks.model_validate_json(response.text)

    # Status
    def now_playing(self) -> PlayingState:
        """Get info about current track."""
        response = self.session.get(f"{self.base_url}/now")
        return PlayingState.model_validate_json(response.text)

    def state(self) -> ServerState:
        """Get server status."""
        response = self.session.get(f"{self.base_url}/state")
        return ServerState.model_validate_json(response.text)

    def ping(self) -> bool:
        """Get server status."""
        try:
            response = self.session.get(
                f"{self.base_url}/ping", timeout=self.ping_timeout
            )
        except requests.exceptions.ConnectionError:
            return False
        return response.status_code == requests.codes.ok

    # Controls
    def play(self, rank: Optional[Annotated[int, Ge(0)]] = None) -> PlayerControl:
        """Start playing current queue."""
        params = PlayQueryParams(rank=rank)
        response = self.session.post(
            f"{self.base_url}/play",
            json=params.model_dump() if rank is not None else {},
        )
        return PlayerControl.model_validate_json(response.text)

    def pause(self) -> PlayerControl:
        """Pause/resume playing."""
        response = self.session.post(f"{self.base_url}/pause")
        return PlayerControl.model_validate_json(response.text)

    def stop(self) -> PlayerControl:
        """Stop playing."""
        response = self.session.post(f"{self.base_url}/stop")
        return PlayerControl.model_validate_json(response.text)

    def next(self) -> PlayerControl:
        """Play next track in queue."""
        response = self.session.post(f"{self.base_url}/next")
        return PlayerControl.model_validate_json(response.text)

    def previous(self) -> PlayerControl:
        """Play previous track in queue."""
        response = self.session.post(f"{self.base_url}/previous")
        return PlayerControl.model_validate_json(response.text)
