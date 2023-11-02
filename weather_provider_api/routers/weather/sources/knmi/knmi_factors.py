#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

# factor name mapping

import json

from weather_provider_api.routers.weather.utils.file_helpers import get_var_map_file_location

file_to_use = get_var_map_file_location("arome_var_map.json")

with open(file_to_use, "r") as _f:
    arome_factors: dict = json.load(_f)
