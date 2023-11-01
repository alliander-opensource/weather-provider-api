#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.sources.cds.models.era5sl import ERA5SLModel


class CDS(WeatherSourceBase):
    def __init__(self):
        model_instances = [
            ERA5SLModel(),
        ]

        self.id = "cds"
        self.name = "Climate Data Store"
        self.url = "https://cds.climate.copernicus.eu/"
        self._models = None
        self._async_models = None

        self.setup_models(model_instances)
