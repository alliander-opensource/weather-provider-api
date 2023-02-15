#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.api_view_v2 import header_accept_type


def test_header_accept_type():
    assert header_accept_type(accept=str("application/netcdf")) == "netcdf4"
    assert header_accept_type(accept=str("application/netcdf3")) == "netcdf3"
    assert header_accept_type(accept=str("application/json")) == "json"
    assert header_accept_type(accept=str("application/json-dataset")) == "json_dataset"
    assert header_accept_type(accept=str("text/csv")) == "csv"


# The get_source, get_sources and get_sync_models only pass on requests to other functions and do not need to be tested

# All of the code inside get_sync_weather consists of either externally called functions that are already covered in
# their respective modules, or either Python system calls or calls to external libraries outside of the testing scope.
# Full coverage is therefore implied and assumed
