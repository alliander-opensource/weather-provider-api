from loguru import logger

from weather_provider_api.weather.base_models.model import WeatherModelBase
from weather_provider_api.weather.base_models.source import WeatherSourceBase

model_instances: list[WeatherModelBase] = []


class KNMI(WeatherSourceBase):
    """Class representing the KNMI as a weather source, containing all the models that are available from the KNMI."""

    def __init__(self):
        """Initialize the KNMI source and set up its models."""
        super().__init__(
            source_id="knmi",
            name="Koninklijk Nederlands Meteorologisch Instituut (KNMI)",
            url="https://knmi.nl/",
            model_instances=model_instances,
        )
        logger.info(f"Initialized KNMI source with {len(model_instances)} models.")
        logger.debug(f"Model instances: {model_instances}")
