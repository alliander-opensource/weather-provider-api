from pathlib import Path
from tempfile import gettempdir

from pydantic_settings import BaseSettings


class WPLASettings(BaseSettings):
    """Settings for the Weather Provider API."""

    # Application
    APP_NAME: str = "WPLA"
    APP_TITLE: str = "Weather Provider Libraries and API"
    APP_DESCRIPTION: str = """
        The Weather Provider Libraries and API (WPLA) is an Open Source Project intended to present an easy
        and uniform way to request meteorological data from a extensive numer of sources in a plethora of formats and
        styles.
    """

    # Deployment configuration
    APP_DEPLOYED: bool = False
    APP_DEBUGGING: bool = False
    APP_DATA_STORAGE_FOLDER: Path = Path(gettempdir()) / "Weather_Repository"
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,::1"

    # Maintainer information and configuration
    SHOW_MAINTAINER_INFO: bool = True
    MAINTAINER: str = "Verbindingsteam"
    EMAIL: str = "weather.provider@alliander.com"

    # API logging configuration
    LOG_LEVEL: str = "INFO"
    USE_STDOUT_LOGGING: bool = True
    USE_FILE_LOGGING: bool = False
    FILE_LOGGING_FOLDER: str | None = None

    # Module configuration
    ENABLE_EXPIRATION_CHECKING: bool = True
    ENABLE_PROMETHEUS_SERVER: bool = True
    ENABLE_CORS_HANDLING: bool = False
    CORS_ALLOW_ORIGINS: list[str] = []
    CORS_ALLOW_ORIGINS_REGEX: list[str] = []
    CORS_ALLOW_METHODS: list[str] = ["GET"]
    CORS_ALLOW_HEADERS: list[str] = ["Accept"]
    CORS_ALLOW_CREDENTIALS: bool = False
