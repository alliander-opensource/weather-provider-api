# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import pytest

from weather_provider_api.routers.weather.api_models import get_weather_content_request_multi_location_query
from weather_provider_api.routers.weather.api_view_v2 import (
    get_sync_weather_multi_loc,
    header_accept_type,
)
from weather_provider_api.versions.v2 import app


@pytest.mark.parametrize(
    "accept_string, expected_output",
    [
        # Direct matches
        ("application/netcdf", "netcdf4"),
        ("application/netcdf3", "netcdf3"),
        ("application/json", "json"),
        ("application/json-dataset", "json_dataset"),
        ("text/csv", "csv"),
        # Near matches (with parameters)
        ("application/netcdf; version=4", "netcdf4"),
        ("application/json; charset=utf-8", "json"),
        ("text/csv; header=present", "csv"),
    ],
)
def test_header_accept_type(accept_string: str, expected_output: str):
    """Test the header_accept_type function for various MIME types."""
    assert header_accept_type(accept=str(accept_string)) == expected_output


def test_multi_location_route_uses_multi_location_query_dependency():
    """The multi-location route exposes and parses a locations query parameter."""
    ret_args = get_sync_weather_multi_loc.__annotations__["ret_args"]
    assert ret_args.__metadata__[0].dependency is get_weather_content_request_multi_location_query

    parameters = app.openapi()["paths"]["/weather/sources/{source_id}/models/{model_id}/multiple-locations/"]["get"][
        "parameters"
    ]
    parameter_names = {parameter["name"] for parameter in parameters}
    assert "locations" in parameter_names
    assert "lat" not in parameter_names
    assert "lon" not in parameter_names


# The get_source, get_sources and get_sync_models only pass on requests to other functions and do not need to be tested

# All the code inside get_sync_weather consists of either externally called functions that are already covered in
# their respective modules, or either Python system calls or calls to external libraries outside the testing scope.
# Full coverage is therefore implied and assumed
