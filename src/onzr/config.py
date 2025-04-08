"""Dzr configuration."""

from pathlib import Path
from typing import List

from click import get_app_dir
from dynaconf import Dynaconf

APP_DIRECTORY: Path = Path(get_app_dir("onzr"))
SETTINGS_FILE: Path = APP_DIRECTORY / "settings.toml"
SECRETS_FILE: Path = APP_DIRECTORY / ".secrets.toml"
SETTINGS_FILES: List[str] = [SETTINGS_FILE.name, SECRETS_FILE.name]

settings = Dynaconf(
    envvar_prefix="ONZR",
    root_path=APP_DIRECTORY,
    settings_files=SETTINGS_FILES,
)
