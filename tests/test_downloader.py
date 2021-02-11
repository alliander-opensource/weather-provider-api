#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

import os
import re

import pytest

from app.routers.weather.sources.cds.client import downloader
from app.routers.weather.sources.cds.client.downloader import bytes_to_string, Client


# downloader.py is based on a file by ECMWF. This

def test_bytes_to_string():
    assert bytes_to_string(1024 ** 0) == "1"  # Bytes
    assert bytes_to_string(1024 ** 1) == "1K"  # Kilobytes
    assert bytes_to_string(1024 ** 2) == "1M"  # Megabytes
    assert bytes_to_string(1024 ** 3) == "1G"  # Gigabytes
    assert bytes_to_string(1024 ** 4) == "1T"  # Terabytes
    assert bytes_to_string(1024 ** 5) == "1P"  # Peta-bytes

    assert bytes_to_string(0.003) == "0"  # should be rounded down to zero
    assert bytes_to_string(0.08) == "0.1"  # should be rounded to the nearest tenth

    # (Border-value) Result should be 1024 and not 1K because it rounds up, but it doesn't divide by 1024
    assert bytes_to_string(1023.96) == "1024"


def mock_callback(*args, **kwargs):
    print("Received args:", args)
    print("Received kwargs: ", kwargs)


@pytest.mark.skip(reason="Monkeypatch for _request_handler() not working. ")  # TODO: FIX
def test_client(monkeypatch):
    mock_client = Client(persist_request_callback=mock_callback(), debug=True)
    mock_request = {'product_type': 'reanalysis',
                    'variable': ['2m_dewpoint_temperature', ],
                    'year': [2020], 'month': [1, ], 'day': [1, ],
                    'time': ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00'],
                    'area': [51, 3.5, 53.75, 7.25], 'grid': [0.25, 0.25],
                    'format': 'netcdf'}

    mock_client.retrieve('reanalysis-era5-single-levels',
                         mock_request,
                         'C:/Temp/dummyfile.nc')

    # Regular use: Dummyfile should exist.
    assert os.path.isfile('C:/Temp/dummyfile.nc')

    # Call without destination file: Dummyfile should not exist.
    result = mock_client.retrieve('reanalysis-era5-single-levels', mock_request)
    assert os.path.isfile(result.location) is False
    assert re.match(r"http://.*nc", result.location) is not None

    # Calls to trigger specific Client._api() states
    era5sl_url = "%s/resources/%s" % (mock_client.url, 'reanalysis-era5-single-levels')
    monkeypatch.setattr(downloader.Client, '_request_handler', {"state": "queued", "request_id": 1})

    mock_client._load_cdsapi_config(None, None, None)
    mock_client._api(era5sl_url, mock_request, 1)

    monkeypatch.setattr(downloader.Client, '_request_handler', {"state": "failed", "request_id": 2})
    mock_client._api(era5sl_url, mock_request, 2)
