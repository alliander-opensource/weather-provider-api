from pathlib import Path

from weather_provider_api.config.api_metadata import load_api_metadata
from weather_provider_api.config.config import WPLASettings

APP_CONFIG = WPLASettings()
API_METADATA = load_api_metadata(path=Path(__file__).with_name("api-config.toml"))
