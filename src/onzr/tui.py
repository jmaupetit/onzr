"""Onzr: TUI elements."""

from textual.app import App, ComposeResult
from textual.containers import Container, HorizontalGroup, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
    TabbedContent,
    TabPane,
)

from onzr import cli
from onzr.client import OnzrClient
from onzr.models import PlayingState, QueuedTracks


def get_now_playing():
    """Get the current playing status."""
    client = OnzrClient()
    playing_state: PlayingState = client.now_playing()
    if playing_state.track is not None:
        return playing_state.track.title
    else:
        return "Nothing"


class PlayStatusWidget(Static):
    """Show the current playing status."""

    now_playing_text = reactive("Nothing", layout=True)

    def render(self) -> str:
        """Render the current playing status."""
        return f"Now playing: {self.now_playing_text}!"


class PlayControl(HorizontalGroup):
    """A group of buttons to control play/pause/stop music."""

    now_playing_text = reactive("Nothing", layout=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        button_id = event.button.id

        match button_id:
            case "play":
                cli.play()
            case "pause":
                cli.pause()
            case "stop":
                cli.stop()
            case "previous":
                cli.previous()
            case "next":
                cli.next()

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Button("Play", id="play", variant="primary", classes="play-button")
        yield Button("Pause", id="pause", variant="primary", classes="play-button")
        yield Button("Stop", id="stop", variant="primary", classes="play-button")
        yield Button(
            "Previous", id="previous", variant="primary", classes="play-button"
        )
        yield Button("Next", id="next", variant="primary", classes="play-button")


class OnzrTuiApp(App):
    """OnzrTui app.

    This is the class that will:
    - define the TUI, compose the interface with the widgets
    - gather the information about the playlist
    - allow features such as search...
    """

    CSS_PATH = "tui.tcss"

    BINDINGS = [
        ("p", "show_tab('playlist-tab')", "Play list"),
        ("s", "show_tab('search-tab')", "Search"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initialize the app."""
        self.title = "ONZR: play your music from the terminal"
        self.set_interval(1, self.update_status)

    def update_status(self):
        """Update the text displayed in the status widget."""
        self.query_one(PlayStatusWidget).now_playing_text = get_now_playing()

    def compose(self) -> ComposeResult:
        """Compose the tui app with tabbed content."""
        yield Header()
        with TabbedContent(initial="playlist-tab"):
            with TabPane("Play list", id="playlist-tab"):
                with Vertical():
                    yield self.get_playlist_items()
                    with Container(classes="play-control"):
                        yield PlayStatusWidget(classes="play-status")
                        yield PlayControl()
            with TabPane("Search", id="search-tab"):
                yield Static("Search")
        # Footer to show keys
        yield Footer()

    def get_playlist_items(self) -> DataTable:
        """Create the playlist items table."""
        client = OnzrClient()
        queue: QueuedTracks = client.queue_list()
        table: DataTable = DataTable()

        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Artist")
        table.add_column("Album")

        for qtrack in queue.tracks:
            table.add_row(
                qtrack.track.id,
                qtrack.track.title,
                qtrack.track.artist,
                qtrack.track.album,
            )

        return table
