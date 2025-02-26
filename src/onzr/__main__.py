"""Onzr."""

import logging

from .core import Onzr
from .deezer import StreamQuality

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

track_id = "2107136627"
onzr = Onzr()
onzr.play(track_id, StreamQuality.MP3_128)
