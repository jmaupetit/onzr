import logging
import vlc
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button

from .deezer import DeezerClient, StreamQuality, Track

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class OnzrPlayerApp(App):
    """The Onzr Player TUI."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Button(label="play", variant="primary", action="app.play")
        yield Footer()

    def _action_play(self):
        self.notify("Start playing...")
        track.play()

    def on_mount(self) -> None:
        """Set application properties."""
        self.title = "Onzr"
        self.sub_title = "Player"


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
