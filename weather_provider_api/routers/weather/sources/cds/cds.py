#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.sources.cds.models.era5land import ERA5LandModel
from weather_provider_api.routers.weather.sources.cds.models.era5sl import ERA5SLModel


class CDS(WeatherSourceBase):
    """Climate Data Store (CDS) weather source implementation."""

    def __init__(self):
        """Initialize the CDS source and set up its models."""
        model_instances: list[WeatherModelBase] = [ERA5SLModel(), ERA5LandModel()]

        super().__init__(
            source_id="cds",
            name="Climate Data Store",
            url="https://cds.climate.copernicus.eu/",
            model_instances=model_instances,
        )
