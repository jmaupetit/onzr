"""Onzr: deezer models."""

import logging
from datetime import date
from enum import IntEnum
from typing import Annotated, Generator, Generic, List, Optional, TypeAlias, TypeVar

from annotated_types import Ge, Gt
from pydantic import BaseModel, PlainSerializer, PositiveInt

from .core import (
    AlbumShort,
    ArtistShort,
    PlaylistShort,
    StreamQuality,
    TrackInfo,
    TrackShort,
)

logger = logging.getLogger(__name__)

# Deezer type
DeezerT = TypeVar("DeezerT")
DeezerTab = TypeVar("DeezerTab")


class BaseDeezerModel(BaseModel):
    """Base Deezer Model."""


# Deezer API models
class BaseDeezerAPIResponse(BaseModel):
    """Deezer API response base Model."""


class DeezerAPIResponseCollection(BaseModel, Generic[DeezerT]):
    """An intermediate model for collections in data fields."""

    data: List[DeezerT]


class DeezerArtist(BaseDeezerModel):
    """Deezer API artist."""

    id: int
    name: str

    def to_short(self) -> ArtistShort:
        """Get ArtistShort."""
        return ArtistShort(id=self.id, name=self.name)


class DeezerAlbum(BaseDeezerModel):
    """Deezer API album."""

    id: int
    title: str
    release_date: Optional[date] = None
    artist: Optional[DeezerArtist] = None

    def to_short(self) -> AlbumShort:
        """Get AlbumShort."""
        return AlbumShort(
            id=self.id,
            title=self.title,
            release_date=self.release_date,
            artist=self.artist.name if self.artist else None,
        )


class DeezerTrack(BaseDeezerModel):
    """Deezer API track."""

    id: PositiveInt
    title: str
    album: DeezerAlbum
    artist: DeezerArtist
    release_date: Optional[date] = None

    def to_short(self) -> TrackShort:
        """Get TrackShort."""
        return TrackShort(
            id=self.id,
            title=self.title,
            album=self.album.title,
            artist=self.artist.name,
            release_date=self.release_date,
        )


class DeezerUser(BaseDeezerModel):
    """Deezer API user."""

    id: PositiveInt
    name: str


class DeezerPlaylist(BaseDeezerModel):
    """Deezer API playlist."""

    id: PositiveInt
    title: str
    public: bool
    nb_tracks: Annotated[int, Ge(0)]
    # Creator is usually filled when requesting playlist details
    creator: Optional[DeezerUser] = None
    # User is filled when searching for playlists 🤷
    user: Optional[DeezerUser] = None
    tracks: Optional[DeezerAPIResponseCollection[DeezerTrack]] = None

    def to_short(self) -> PlaylistShort:
        """Get PlaylistShort."""
        return PlaylistShort(
            id=self.id,
            title=self.title,
            public=self.public,
            nb_tracks=self.nb_tracks,
            user=(
                self.creator.name
                if self.creator
                else self.user.name if self.user else None
            ),
            tracks=(
                [track.to_short() for track in self.tracks.data]
                if self.tracks
                else None
            ),
        )


class DeezerAlbumResponse(BaseDeezerAPIResponse):
    """Deezer album response."""

    id: int
    title: str
    release_date: date
    artist: DeezerArtist
    tracks: DeezerAPIResponseCollection[DeezerTrack]

    def get_tracks(self) -> Generator[TrackShort, None, None]:
        """Get album TrackShort iterator."""
        if not len(self.tracks.data):
            logger.error(f"Empty album {self.id}")
            return

        for track in self.tracks.data:
            yield TrackShort(
                id=track.id,
                title=track.title,
                album=track.album.title,
                artist=track.artist.name,
                release_date=self.release_date,
            )

    def to_short(self, artist: Optional[ArtistShort] = None) -> AlbumShort:
        """Get AlbumShort."""
        return AlbumShort(
            id=self.id,
            title=self.title,
            release_date=self.release_date,
            artist=(
                artist.name if artist else self.artist.name if self.artist else None
            ),
        )


DeezerArtistTopResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerArtistRadioResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerArtistAlbumsResponse = DeezerAPIResponseCollection[DeezerAlbum]
DeezerArtistResponse: TypeAlias = (
    DeezerArtistTopResponse | DeezerArtistRadioResponse | DeezerArtistAlbumsResponse
)
DeezerAdvancedSearchResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerSearchAlbumResponse = DeezerAPIResponseCollection[DeezerAlbum]
DeezerSearchArtistResponse = DeezerAPIResponseCollection[DeezerArtist]
DeezerSearchPlaylistResponse = DeezerAPIResponseCollection[DeezerPlaylist]
DeezerSearchTrackResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerSearchResponse: TypeAlias = (
    DeezerAdvancedSearchResponse
    | DeezerSearchAlbumResponse
    | DeezerSearchArtistResponse
    | DeezerSearchPlaylistResponse
    | DeezerSearchTrackResponse
)


# Deezer API Gateway models
class BaseDeezerGWResponse(BaseModel, Generic[DeezerT]):
    """Deezer API Gateway response base Model."""

    error: dict = {}
    results: DeezerT


class DeezerGWUser(BaseDeezerModel):
    """Deezer Gateway user."""

    USER_ID: int
    BLOG_NAME: str

    def to_user(self):
        """Convert to DeezerUser."""
        return DeezerUser(id=self.USER_ID, name=self.BLOG_NAME)


class PlaylistStatus(IntEnum):
    """Playlist statuses."""

    PUBLIC = 0
    PRIVATE = 1
    COLLABORATIVE = 2


class DeezerGWPlaylist(BaseDeezerModel):
    """Deezer Gateway playlist."""

    PLAYLIST_ID: int
    TITLE: str
    STATUS: PlaylistStatus
    NB_SONG: int
    PARENT_USERNAME: Optional[str] = None
    PARENT_USER_ID: Optional[int] = None
    USER_ID: Optional[int] = None

    def to_short(self, user: Optional[str] = None) -> PlaylistShort:
        """Convert DeezerGWPlaylist to PlaylistShort."""
        return PlaylistShort(
            id=self.PLAYLIST_ID,
            title=self.TITLE,
            public=True if self.STATUS == PlaylistStatus.PUBLIC else False,
            nb_tracks=self.NB_SONG,
            user=(
                self.PARENT_USERNAME if self.PARENT_USERNAME else user if user else None
            ),
        )


class DeezerGWPlaylistResponse(BaseDeezerModel):
    """Deezer Gateway playlist response."""

    DATA: DeezerGWPlaylist
    SONGS: DeezerAPIResponseCollection["DeezerSong"]

    def to_short(self) -> PlaylistShort:
        """Convert DeezerGWPlaylistResponse to PlaylistShort."""
        playlist = self.DATA.to_short()
        playlist.tracks = [s.to_short() for s in self.SONGS.data]
        return playlist


class DeezerUserData(BaseDeezerModel):
    """Deezer User Data."""

    USER: DeezerGWUser


class DeezerUserProfilePageTab(BaseDeezerModel, Generic[DeezerTab]):
    """Deezer user profile page tab."""

    TAB: DeezerTab


class DeezerUserProfilePagePlaylists(BaseDeezerModel):
    """Deezer user profile page playlists."""

    playlists: DeezerAPIResponseCollection[DeezerGWPlaylist]


DeezerUserProfilePageTabPlaylists = DeezerUserProfilePageTab[
    DeezerUserProfilePagePlaylists
]


class DeezerSong(BaseDeezerModel):
    """Deezer API Song."""

    SNG_ID: Annotated[int, Gt(0), PlainSerializer(str)]
    TRACK_TOKEN: str
    DURATION: Annotated[int, Gt(0), PlainSerializer(str)]
    ART_NAME: str
    SNG_TITLE: str
    VERSION: Optional[str] = None
    ALB_TITLE: str
    ALB_PICTURE: str
    PHYSICAL_RELEASE_DATE: Annotated[Optional[date], PlainSerializer(str)] = None
    FILESIZE_MP3_128: Annotated[int, Ge(0), PlainSerializer(str)]
    FILESIZE_MP3_320: Annotated[int, Ge(0), PlainSerializer(str)]
    FILESIZE_FLAC: Annotated[int, Ge(0), PlainSerializer(str)]
    FALLBACK: "Optional[DeezerSong]" = None

    def to_track_info(self) -> TrackInfo:
        """Get TrackInfo from this song."""
        song: DeezerSong = self
        if self.FALLBACK:
            logger.warning(
                f"Using fallback track with id {self.FALLBACK.SNG_ID} "
                f"(original was {song.SNG_ID})"
            )
            song = self.FALLBACK

        filesizes = {
            "FILESIZE_MP3_128": StreamQuality.MP3_128,
            "FILESIZE_MP3_320": StreamQuality.MP3_320,
            "FILESIZE_FLAC": StreamQuality.FLAC,
        }
        return TrackInfo(
            id=song.SNG_ID,
            title=(
                f"{self.SNG_TITLE} {self.VERSION}" if self.VERSION else song.SNG_TITLE
            ),
            album=song.ALB_TITLE,
            artist=song.ART_NAME,
            release_date=song.PHYSICAL_RELEASE_DATE,
            picture=song.ALB_PICTURE,
            token=song.TRACK_TOKEN,
            duration=song.DURATION,
            formats=[filesizes[size] for size in filesizes if getattr(song, size) > 0],
        )

    def to_short(self):
        """Convert DeezerSong to ShortTrack."""
        return TrackShort(
            id=self.SNG_ID,
            title=(
                f"{self.SNG_TITLE} {self.VERSION}" if self.VERSION else self.SNG_TITLE
            ),
            album=self.ALB_TITLE,
            artist=self.ART_NAME,
            release_date=self.PHYSICAL_RELEASE_DATE,
        )


DeezerSongResponse = BaseDeezerGWResponse[DeezerSong]
