import logging
import vlc
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button

from .deezer import DeezerClient, StreamQuality, Track

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OnzrPlayerApp(App):
    """The Onzr Player TUI."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Button(label="play", variant="primary", action="app.play")
        yield Button(label="pause", variant="default", action="app.pause")
        yield Footer()

    def _action_play(self):
        if track.is_playable:
            track.player.play()
        else:
            self.notify("Still fetching current track...")

    def _action_pause(self):
        self.notify("Toggling pause...")
        track.player.pause()

    def on_mount(self) -> None:
        """Set application properties."""
        self.title = "Onzr"
        self.sub_title = "Player"
        track.fetch()


# Deezer API client
dzr = DeezerClient()

# VLC player
vlc_instance = vlc.Instance()
vlc_player = vlc_instance.media_player_new()

# Track
track_id = "2107136627"
track = Track(dzr, track_id, vlc_player, StreamQuality.FLAC)
# track.play()

app = OnzrPlayerApp()
# app.run()
