#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from app.routers.weather.base_models.source import WeatherSourceBase
from app.routers.weather.sources.knmi.models.actuele_waarnemingen import (
    ActueleWaarnemingenModel,
)
from app.routers.weather.sources.knmi.models.daggegevens import DagGegevensModel
from app.routers.weather.sources.knmi.models.harmonie_arome import AromeModel
from app.routers.weather.sources.knmi.models.pluim import PluimModel
from app.routers.weather.sources.knmi.models.uurgegevens import UurgegevensModel


class KNMI(WeatherSourceBase):
    def __init__(self):
        model_instances = [
            UurgegevensModel(),
            DagGegevensModel(),
            AromeModel(),
            PluimModel(),
            ActueleWaarnemingenModel(),
        ]

        self.id = "knmi"
        self.name = "Koninklijk Nederlands Meteorologisch Instituut (KNMI)"
        self.url = "https://knmi.nl/"
        self._models = None
        self._async_models = None

        self.setup_models(model_instances)
