#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

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
    def __init__(self):
        model_instances = [
            UurgegevensModel(),
            DagGegevensModel(),
            HarmonieAromeModel(),
            PluimModel(),
            ActueleWaarnemingenModel(),
            ActueleWaarnemingenRegisterModel(),
        ]

        self.id = "knmi"
        self.name = "Koninklijk Nederlands Meteorologisch Instituut (KNMI)"
        self.url = "https://knmi.nl/"
        self._models = None
        self._async_models = None

        self.setup_models(model_instances)
