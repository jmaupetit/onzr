"""Dzr configuration."""

import logging
from pathlib import Path

from dynaconf import Dynaconf
from typer import get_app_dir

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
    return Dynaconf(
        envvar_prefix=APP_NAME.upper(),
        root_path=get_onzr_dir(),
        settings_files=[SECRETS_FILE.name, SETTINGS_FILE.name],
    )


def check_settings(settings: Dynaconf):
    """Check settings are properly set."""
    # Settings or secret files does not exist
    try:
        settings.get("arl")
    except OSError as err:
        raise OnzrConfigurationError(
            "Onzr is not configured. You should run the 'onzr init' command first."
        ) from err

    # ARL is not set
    if settings.get("arl", None) is None:
        raise OnzrConfigurationError(
            "Onzr is not properly configured. You should set the ARL secret."
        )
