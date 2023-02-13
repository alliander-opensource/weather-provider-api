#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

# factor name mapping

import json

from weather_provider_api.routers.weather.utils.file_helpers import get_var_map_file_location

file_to_use_era5sl = get_var_map_file_location("era5sl_var_map.json")
file_to_use_era5land = get_var_map_file_location("era5land_var_map.json")

with open(file_to_use_era5sl, "r") as _f:
    era5sl_factors = json.load(_f)

with open(file_to_use_era5land, "r") as _f:
    era5land_factors = json.load(_f)
