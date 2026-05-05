#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen import (
    ActueleWaarnemingenModel,
)
from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen_register import (
    ActueleWaarnemingenRegisterModel,
)
from weather_provider_api.routers.weather.sources.knmi.models.daggegevens import (
    DagGegevensModel,
)
from weather_provider_api.routers.weather.sources.knmi.models.harmonie_arome import (
    HarmonieAromeModel,
)
from weather_provider_api.routers.weather.sources.knmi.models.pluim import PluimModel
from weather_provider_api.routers.weather.sources.knmi.models.uurgegevens import (
    UurgegevensModel,
)


class KNMI(WeatherSourceBase):
    """Class representing the KNMI as a weather source, containing all the models that are available from the KNMI."""

    def __init__(self):
        """Initialize the KNMI source and set up its models."""
        model_instances: list[WeatherModelBase] = [
            UurgegevensModel(),
            DagGegevensModel(),
            HarmonieAromeModel(),
            PluimModel(),
            ActueleWaarnemingenModel(),
            ActueleWaarnemingenRegisterModel(),
        ]

        super().__init__(
            source_id="knmi",
            name="Koninklijk Nederlands Meteorologisch Instituut (KNMI)",
            url="https://knmi.nl/",
            model_instances=model_instances,
        )
