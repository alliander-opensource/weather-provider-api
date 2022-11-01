#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import numpy as np
import xarray as xr

from weather_provider_api.routers.weather.api_models import OutputUnit, ResponseFormat, WeatherContentRequestQuery
from weather_provider_api.routers.weather.api_view_v2 import controller
from weather_provider_api.routers.weather.utils import serializers

"""
    This is a DEMO for a specific weather model: ERA5 Single Levels
    
    The purpose of this demo is to show users a method of how they can use specific models from the Weather Provider API
    to request specific output. 
"""

if __name__ == '__main__':
    coords = [[(51.873419, 5.705929), (51.873419, 5.71), (51.88, 5.71)],
              [(52.121976, 4.782497)],
              [(52.424793, 4.776927)]]

    ds_hist_day: xr.Dataset = controller.get_weather(
        source_id='cds',
        model_id='era5sl',
        fetch_async=False,
        coords=coords,
        begin=datetime(2018, 2, 1, 0, 0),
        end=datetime(2018, 2, 28, 23, 59)
    )

    response_format = ResponseFormat.netcdf4

    converted_weather_data = controller.convert_names_and_units(
        'cds', 'era5sl', False, ds_hist_day, OutputUnit.si
    )

    ret_args = WeatherContentRequestQuery(begin='2018-01-01 00:00', end='2018-01-31 23:59', lat=52.1, lon=5.18,
                                          factors=None)

    coords = [
        (
            float(np.mean([single_point[0] for single_point in single_polygon])),
            float(np.mean([single_point[1] for single_point in single_polygon])),
        )
        for single_polygon in coords
    ]  # means to match the used coordinates for the request
    response, optional_file_path = serializers.file_or_text_response(
        converted_weather_data, response_format, 'cds', 'era5sl', ret_args, coords
    )

    print(response, optional_file_path)
