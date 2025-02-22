"""Dzr configuration."""

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="ONZR",
    settings_files=["settings.toml", ".secrets.toml"],
)
