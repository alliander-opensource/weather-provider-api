#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from wpla.models.base_classes.base_source import WeatherSourceBase


class KNMI(WeatherSourceBase):
    def __init__(self):
        super().__init__()
        model_instances = [

        ]

        self.short_name = "knmi"
        self.long_name = "Koninklijk Nederlands Meteorologisch Instituut (KNMI)"
        self.source_description = "The 'Koninklijk Nederlands Meteorologisch Instituut (KNMI)' or " \
                                  "'Royal Netherlands Meteorological Institute' is the Dutch national weather " \
                                  "service. Primary tasks of KNMI are weather forecasting and monitoring of weather, " \
                                  "climate, air quality and seismic activity. KNMI is also the national research and " \
                                  "information centre for meteorology, climate, air quality, and seismology."
        self.source_url = "https://knmi.nl/"

        self.initialize_models(model_instances=model_instances)
