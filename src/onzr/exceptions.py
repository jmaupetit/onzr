"""Onzr exceptions."""


class OnzrConfigurationError(Exception):
    """Raised when onzr cannot load or create its configuration."""


class DeezerTrackException(Exception):
    """Raised when onzr cannot handle a Deezer track."""
