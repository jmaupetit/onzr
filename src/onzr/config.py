"""Dzr configuration."""

import logging
from pathlib import Path

from pydantic import computed_field
from pydantic.networks import HttpUrl
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)
from typer import get_app_dir

from .deezer import StreamQuality

logger = logging.getLogger(__name__)

APP_NAME: str = "onzr"
SETTINGS_FILE: Path = Path("settings.yaml")


def get_onzr_dir() -> Path:
    """Get Onzr application directory."""
    return Path(get_app_dir(APP_NAME))


# def get_settings() -> Dynaconf:
#     """Get Dynaconf settiings."""
#     logger.debug("Getting settings…")
#     settings = Dynaconf(
#         envvar_prefix=APP_NAME.upper(),
#         root_path=get_onzr_dir(),
#         settings_files=[SECRETS_FILE.name, SETTINGS_FILE.name],
#         validators=[
#             Validator("ARL", must_exist=True),
#             Validator("DEEZER_BLOWFISH_SECRET", must_exist=True),
#             Validator("QUALITY", must_exist=True, cast=StreamQuality),
#         ],
#     )
#
#     # Check settings
#     try:
#         settings.validators.validate_all()
#     except ValidationError as err:
#         mess = "Onzr is not properly configured:\n"
#         mess += "\n".join([f"- {e[1]}" for e in err.details])
#         raise OnzrConfigurationError(mess) from err
#     return settings


class Settings(BaseSettings):
    """Onzr application settings."""

    DEBUG: bool = False

    # Server
    SCHEMA: str = "http"
    HOST: str = "localhost"
    PORT: int = 9473
    API_ROOT_URL: str = "/api/v1"
    TRACK_STREAM_ENDPOINT: str = "/queue/{track_id}/stream"

    @property
    @computed_field
    def SERVER_BASE_URL(self) -> HttpUrl:
        """Onzr server base URL."""
        return HttpUrl(f"{self.SCHEMA}://{self.HOST}:{self.PORT}{self.API_ROOT_URL}")

    @property
    @computed_field
    def TRACK_STREAM_URL(self) -> str:
        """Onzr server track stream URL."""
        return f"{self.SERVER_BASE_URL}{self.TRACK_STREAM_ENDPOINT}"

    # Deezer
    QUALITY: StreamQuality = StreamQuality.MP3_128
    DEEZER_BLOWFISH_SECRET: str
    ARL: str

    model_config = SettingsConfigDict(
        env_prefix=APP_NAME.upper(),
        yaml_file=get_onzr_dir() / SETTINGS_FILE,
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
        return (YamlConfigSettingsSource(settings_cls),)


def get_settings() -> Settings:
    """Get settings."""
    # ARL and DEEZER_BLOWFISH_SECRET are missing in instantiation since
    # those should be loaded using the YAML configuration
    return Settings()  # type: ignore[call-arg]
