"""Test factories."""

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import PositiveInt

from onzr.models.core import AlbumShort, ArtistShort, PlaylistShort, TrackShort
from onzr.models.deezer import (
    DeezerAdvancedSearchResponse,
    DeezerAlbum,
    DeezerAlbumResponse,
    DeezerArtist,
    DeezerArtistAlbumsResponse,
    DeezerArtistRadioResponse,
    DeezerArtistTopResponse,
    DeezerPlaylist,
    DeezerSearchAlbumResponse,
    DeezerSearchArtistResponse,
    DeezerSearchPlaylistResponse,
    DeezerSearchTrackResponse,
    DeezerSong,
    DeezerSongResponse,
    DeezerTrack,
)


class DeezerSongFactory(ModelFactory[DeezerSong]):
    """DeezerSong factory."""

    @classmethod
    def PHYSICAL_RELEASE_DATE(cls) -> str:
        """Always generate a release date."""
        return cls.__faker__.date()

    @classmethod
    def FILESIZE_MP3_128(cls) -> PositiveInt:
        """Force FILESIZE_MP3_128 to be at least 100."""
        return cls.__random__.randint(100, 10000)


class DeezerAlbumFactory(ModelFactory[DeezerAlbum]):
    """DeezerAlbum factory."""


class DeezerArtistFactory(ModelFactory[DeezerArtist]):
    """DeezerArtist factory."""


class DeezerPlaylistFactory(ModelFactory[DeezerPlaylist]):
    """DeezerPlaylist factory."""


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


class DeezerSearchPlaylistResponseFactory(ModelFactory[DeezerSearchPlaylistResponse]):
    """DeezerSearchPlaylistResponse factory."""


class DeezerSearchTrackResponseFactory(ModelFactory[DeezerSearchTrackResponse]):
    """DeezerSearchTrackResponse factory."""


class AlbumShortFactory(ModelFactory[AlbumShort]):
    """AlbumShort factory."""


class ArtistShortFactory(ModelFactory[ArtistShort]):
    """ArtistShort factory."""


class PlaylistShortFactory(ModelFactory[PlaylistShort]):
    """PlaylistShort factory."""


class TrackShortFactory(ModelFactory[TrackShort]):
    """TrackShort factory."""
