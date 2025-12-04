"""Test factories."""

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import PositiveInt

from onzr.models.core import AlbumShort, ArtistShort, TrackShort
from onzr.models.deezer import (
    DeezerAdvancedSearchResponse,
    DeezerAlbum,
    DeezerAlbumResponse,
    DeezerArtist,
    DeezerArtistAlbumsResponse,
    DeezerArtistRadioResponse,
    DeezerArtistTopResponse,
    DeezerSearchAlbumResponse,
    DeezerSearchArtistResponse,
    DeezerSearchTrackResponse,
    DeezerSong,
    DeezerSongResponse,
    DeezerTrack,
)


class DeezerSongFactory(ModelFactory[DeezerSong]):
    """DeezerSong factory."""

    @classmethod
    def FILESIZE_MP3_128(cls) -> PositiveInt:
        """Force FILESIZE_MP3_128 to be at least 100."""
        return cls.__random__.randint(100, 10000)


class DeezerAlbumFactory(ModelFactory[DeezerAlbum]):
    """DeezerAlbum factory."""


class DeezerArtistFactory(ModelFactory[DeezerArtist]):
    """DeezerArtist factory."""


class DeezerTrackFactory(ModelFactory[DeezerTrack]):
    """DeezerTrack factory."""


class DeezerAlbumResponseFactory(ModelFactory[DeezerAlbumResponse]):
    """DeezerAlbumResponse factory."""


class DeezerSongResponseFactory(ModelFactory[DeezerSongResponse]):
    """DeezerSongResponse factory."""


class DeezerArtistAlbumsResponseFactory(ModelFactory[DeezerArtistAlbumsResponse]):
    """DeezerArtistAlbumsResponse factory."""


class DeezerArtistRadioResponseFactory(ModelFactory[DeezerArtistRadioResponse]):
    """DeezerArtistRadioResponse factory."""


class DeezerArtistTopResponseFactory(ModelFactory[DeezerArtistTopResponse]):
    """DeezerArtistTopResponse factory."""


class DeezerAdvancedSearchResponseFactory(ModelFactory[DeezerAdvancedSearchResponse]):
    """DeezerAdvancedSearchResponse factory."""


class DeezerSearchArtistResponseFactory(ModelFactory[DeezerSearchArtistResponse]):
    """DeezerSearchArtistResponse factory."""


class DeezerSearchAlbumResponseFactory(ModelFactory[DeezerSearchAlbumResponse]):
    """DeezerSearchAlbumResponse factory."""


class DeezerSearchTrackResponseFactory(ModelFactory[DeezerSearchTrackResponse]):
    """DeezerSearchTrackResponse factory."""


class TrackShortFactory(ModelFactory[TrackShort]):
    """TrackShort factory."""


class AlbumShortFactory(ModelFactory[AlbumShort]):
    """AlbumShort factory."""


class ArtistShortFactory(ModelFactory[ArtistShort]):
    """ArtistShort factory."""
