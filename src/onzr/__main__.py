"""Onzr."""

import logging
import time

import vlc

from .deezer import DeezerClient, StreamQuality, Track

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Deezer API client
dzr = DeezerClient()

# VLC player
vlc_instance = vlc.Instance()
vlc_player = vlc_instance.media_player_new()

# Track
track_id = "2107136627"
track = Track(dzr, track_id, vlc_player, StreamQuality.FLAC)
track.play()

# Infinite loop while running the CLI
while True:
    time.sleep(10)
