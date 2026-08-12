# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# Unit tests for weather_provider_api.routers.weather.sources.cds.client.cds_api_tools.
#
# These tests deliberately avoid any real CDS credentials or network access: the only place a real client would be
# created (get_cds_client) is exercised with cdsapi.Client monkeypatched to a fake, which is possible precisely because
# the client is now instantiated lazily instead of at import time.

import weather_provider_api.routers.weather.sources.cds.client.cds_api_tools as cds_tools
from weather_provider_api.routers.weather.sources.cds.client.cds_api_tools import (
    CDSDataSets,
    CDSRequest,
    get_cds_client,
)


def test_cds_datasets_enum_values():
    """The supported dataset enum should expose the documented CDS dataset identifiers."""
    assert CDSDataSets.ERA5SL.value == "reanalysis-era5-single-levels"
    assert CDSDataSets.ERA5LAND.value == "reanalysis-era5-land"


def test_cds_request_defaults_and_parameters():
    """A minimal CDSRequest should expose sensible defaults through request_parameters."""
    request = CDSRequest(variables=["stl1", "stl2"])
    params = request.request_parameters

    assert params["variable"] == ["stl1", "stl2"]
    assert params["area"] == (53.7, 3.2, 50.75, 7.22)
    assert params["data_format"] == "netcdf"
    assert params["download_format"] == "zip"
    # Date fields default to a single current-date entry; time defaults to all 24 hours.
    assert len(params["year"]) == 1
    assert len(params["month"]) == 1
    assert len(params["day"]) == 1
    assert len(params["time"]) == 24
    # Without a product_type the key should be omitted entirely.
    assert "product_type" not in params


def test_cds_request_includes_product_type_when_set():
    """A CDSRequest with a product_type should surface it in request_parameters."""
    request = CDSRequest(variables=["stl1"], product_type=["reanalysis"])

    assert request.request_parameters["product_type"] == ["reanalysis"]


def test_info_callback_is_noop_without_arguments():
    """The info callback should do nothing (and not raise) when called without arguments."""
    assert cds_tools._info_callback() is None


def test_info_callback_handles_positional_arguments():
    """The info callback should accept positional arguments without raising."""
    assert cds_tools._info_callback("some-progress-info") is None


def test_get_cds_client_is_lazily_created_and_cached(monkeypatch):
    """get_cds_client should build the client only once and return the cached instance thereafter."""
    created: list[dict] = []

    class _FakeClient:
        def __init__(self, **kwargs):
            created.append(kwargs)

    monkeypatch.setattr(cds_tools.cdsapi, "Client", _FakeClient)
    get_cds_client.cache_clear()

    try:
        first = get_cds_client()
        second = get_cds_client()

        assert first is second  # cached: same instance returned
        assert len(created) == 1  # constructed exactly once
        assert created[0]["url"] == "https://cds.climate.copernicus.eu/api"
        assert created[0]["info_callback"] is cds_tools._info_callback
    finally:
        get_cds_client.cache_clear()
