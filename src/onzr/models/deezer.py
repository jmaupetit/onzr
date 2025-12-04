"""Onzr: deezer models."""

import logging
from datetime import date
from typing import Annotated, Generator, Generic, List, Optional, TypeAlias, TypeVar

from annotated_types import Ge, Gt
from pydantic import BaseModel, PlainSerializer, PositiveInt

from .core import AlbumShort, ArtistShort, StreamQuality, TrackInfo, TrackShort

logger = logging.getLogger(__name__)

# Deezer type
DeezerT = TypeVar("DeezerT")


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


DeezerArtistTopResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerArtistRadioResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerArtistAlbumsResponse = DeezerAPIResponseCollection[DeezerAlbum]
DeezerArtistResponse: TypeAlias = (
    DeezerArtistTopResponse | DeezerArtistRadioResponse | DeezerArtistAlbumsResponse
)
DeezerAdvancedSearchResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerSearchAlbumResponse = DeezerAPIResponseCollection[DeezerAlbum]
DeezerSearchArtistResponse = DeezerAPIResponseCollection[DeezerArtist]
DeezerSearchTrackResponse = DeezerAPIResponseCollection[DeezerTrack]
DeezerSearchResponse: TypeAlias = (
    DeezerAdvancedSearchResponse
    | DeezerSearchAlbumResponse
    | DeezerSearchArtistResponse
    | DeezerSearchTrackResponse
)


# Helpers
def to_tracks(
    collection: (
        DeezerArtistTopResponse
        | DeezerArtistRadioResponse
        | DeezerAdvancedSearchResponse
        | DeezerSearchTrackResponse
    ),
) -> Generator[TrackShort, None, None]:
    """Convert deezer API response tracks collection to short tracks."""
    for track in collection.data:
        yield TrackShort(
            id=track.id,
            title=track.title,
            album=track.album.title,
            artist=track.artist.name,
        )


def to_albums(
    collection: DeezerArtistAlbumsResponse | DeezerSearchAlbumResponse,
    artist: Optional[ArtistShort] = None,
) -> Generator[AlbumShort, None, None]:
    """Get tracks collection iterator."""
    for album in collection.data:
        yield AlbumShort(
            id=album.id,
            title=album.title,
            release_date=album.release_date,
            artist=(
                artist.name if artist else album.artist.name if album.artist else None
            ),
        )


def to_artists(
    collection: DeezerSearchArtistResponse,
) -> Generator[ArtistShort, None, None]:
    """Get artists collection iterator."""
    for artist in collection.data:
        yield ArtistShort(
            id=artist.id,
            name=artist.name,
        )


# Deezer API Gateway models
class BaseDeezerGWResponse(BaseModel, Generic[DeezerT]):
    """Deezer API Gateway response base Model."""

    error: dict = {}
    results: DeezerT


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
    PHYSICAL_RELEASE_DATE: Annotated[date, PlainSerializer(str)]
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


DeezerSongResponse = BaseDeezerGWResponse[DeezerSong]
