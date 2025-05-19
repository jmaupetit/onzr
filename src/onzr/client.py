"""Onzr: http client."""

from typing import List
import requests

from .config import get_settings


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

    # Queue
    def queue_tracks(self, track_ids: List[str]) -> dict:
        """Add tracks to queue given their identifiers."""
        response = self.session.post(f"{self.base_url}/queue/", json=track_ids)
        return response.json()

    def queue_clear(self) -> dict:
        """Clear tracks queue."""
        response = self.session.post(f"{self.base_url}/queue/clear")
        return response.json()

    def queue_list(self) -> dict:
        """List queue tracks."""
        response = self.session.get(f"{self.base_url}/queue/")
        return response.json()

    # Status
    def now_playing(self) -> dict:
        """Get info about current track."""
        response = self.session.get(f"{self.base_url}/now")
        return response.json()

    # Controls
    def play(self) -> dict:
        """Start playing current queue."""
        response = self.session.post(f"{self.base_url}/play")
        return response.json()

    def pause(self) -> dict:
        """Pause/resume playing."""
        response = self.session.post(f"{self.base_url}/pause")
        return response.json()

    def stop(self) -> dict:
        """Stop playing."""
        response = self.session.post(f"{self.base_url}/stop")
        return response.json()

    def next(self) -> dict:
        """Play next track in queue."""
        response = self.session.post(f"{self.base_url}/next")
        return response.json()

    def previous(self) -> dict:
        """Play previous track in queue."""
        response = self.session.post(f"{self.base_url}/previous")
        return response.json()
