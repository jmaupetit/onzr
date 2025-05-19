"""Dzr configuration."""

import logging
from pathlib import Path

from dynaconf import Dynaconf, ValidationError, Validator
from typer import get_app_dir

from .deezer import StreamQuality
from .exceptions import OnzrConfigurationError

logger = logging.getLogger(__name__)

APP_NAME: str = "onzr"
SECRETS_FILE: Path = Path(".secrets.toml")
SETTINGS_FILE: Path = Path("settings.toml")


def get_onzr_dir() -> Path:
    """Get Onzr application directory."""
    return Path(get_app_dir(APP_NAME))


def get_settings() -> Dynaconf:
    """Get Dynaconf settiings."""
    logger.debug("Getting settings…")
    settings = Dynaconf(
        envvar_prefix=APP_NAME.upper(),
        root_path=get_onzr_dir(),
        settings_files=[SECRETS_FILE.name, SETTINGS_FILE.name],
        validators=[
            Validator("ARL", must_exist=True),
            Validator("DEEZER_BLOWFISH_SECRET", must_exist=True),
            Validator("QUALITY", must_exist=True, cast=StreamQuality)
        ],
    )

    # Check settings
    try:
        settings.validators.validate_all()
    except ValidationError as err:
        mess = "Onzr is not properly configured:\n"
        mess += "\n".join([f"- {e[1]}" for e in err.details])
        raise OnzrConfigurationError(mess) from err
    return settings
