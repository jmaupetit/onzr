"""Dzr configuration."""

import logging
from functools import cache
from pathlib import Path

from pydantic import computed_field
from pydantic.networks import HttpUrl
from pydantic_extra_types.color import Color
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from typer import get_app_dir

from .deezer import StreamQuality
from .models import OnzrTheme

logger = logging.getLogger(__name__)

APP_NAME: str = "onzr"
SETTINGS_FILE: Path = Path("settings.yaml")


def get_onzr_dir() -> Path:
    """Get Onzr application directory."""
    return Path(get_app_dir(APP_NAME))


class Settings(BaseSettings):
    """Onzr application settings."""

    DEBUG: bool = False

    # Server
    SCHEMA: str = "http"
    HOST: str = "localhost"
    PORT: int = 9473
    API_ROOT_URL: str = "/api/v1"
    TRACK_STREAM_ENDPOINT: str = "/queue/{rank}/stream"
    PING_TIMEOUT: float = 0.1  # in seconds

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SERVER_BASE_URL(self) -> HttpUrl:
        """Onzr server base URL."""
        return HttpUrl(f"{self.SCHEMA}://{self.HOST}:{self.PORT}{self.API_ROOT_URL}")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def TRACK_STREAM_URL(self) -> str:
        """Onzr server track stream URL."""
        return f"{self.SERVER_BASE_URL}{self.TRACK_STREAM_ENDPOINT}"

    # Customization
    THEME: OnzrTheme = OnzrTheme(
        # Base palette
        primary_color=Color("#9B6BDF"),
        secondary_color=Color("#75D7EC"),
        tertiary_color=Color("#E356A7"),
        # Entities
        title_color=Color("#9B6BDF"),
        artist_color=Color("#75D7EC"),
        album_color=Color("#E356A7"),
        # Messages
        alert_color=Color("red"),
    )

    # Deezer
    QUALITY: StreamQuality = StreamQuality.MP3_128
    DEEZER_BLOWFISH_SECRET: str
    ARL: str

    # Player
    # How long should we wait before getting player status after player control action?
    STATE_DELAY: float = 0.005  # in seconds

    model_config = SettingsConfigDict(
        env_prefix=f"{APP_NAME.upper()}_",
        case_sensitive=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add Toml configuration support."""
        return env_settings, YamlConfigSettingsSource(
            settings_cls, yaml_file=get_onzr_dir() / SETTINGS_FILE
        )


@cache
def get_settings() -> Settings:
    """Get settings."""
    logger.debug(f"Loading settings from Onzr directory: {get_onzr_dir()}")
    # ARL and DEEZER_BLOWFISH_SECRET are missing in instantiation since
    # those should be loaded using the YAML configuration
    settings = Settings()  # type: ignore[call-arg]
    logger.debug(f"Settings: {settings=}")
    return settings
