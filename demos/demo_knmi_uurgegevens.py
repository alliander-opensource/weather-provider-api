#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import xarray as xr

from weather_provider_api.routers.weather.api_models import ResponseFormat, OutputUnit, WeatherContentRequestQuery
from weather_provider_api.routers.weather.api_view_v2 import controller
from weather_provider_api.routers.weather.utils import serializers

"""
    This is a DEMO for a specific weather model: KNMI Uurgegevens

    The purpose of this demo is to show users a method of how they can use specific models from the Weather Provider API
    to request specific output. 
"""

if __name__ == "__main__":
    coords = [
        [(51.873419, 5.705929)],
        [(52.121976, 4.782497)],
        [(52.424793, 4.776927)],
        [(51.873777, 5.705111)],
    ]

    ds_hist_day: xr.Dataset = controller.get_weather(
        source_id='knmi',
        model_id='uurgegevens',
        fetch_async=False,
        coords=coords,
        begin=datetime(year=2018, month=1, day=1),
        end=datetime(year=2018, month=1, day=31)
    )

    response_format = ResponseFormat.netcdf4

    converted_weather_data = controller.convert_names_and_units(
        'knmi', 'uurgegevens', False, ds_hist_day, OutputUnit.si
    )

    ret_args = WeatherContentRequestQuery(begin='2018-01-01 00:00',
                                          end='2018-01-31 23:59',
                                          lat=[51.873419],
                                          lon=[5.705929],
                                          factors=None)

    response, optional_file_path = serializers.file_or_text_response(
        converted_weather_data, response_format, 'knmi', 'uurgegevens', ret_args, coords
    )

    print(response)
    print(optional_file_path)
