#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import pytest

from weather_provider_api.routers.weather.api_view_v2 import header_accept_type


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


# The get_source, get_sources and get_sync_models only pass on requests to other functions and do not need to be tested

# All the code inside get_sync_weather consists of either externally called functions that are already covered in
# their respective modules, or either Python system calls or calls to external libraries outside the testing scope.
# Full coverage is therefore implied and assumed
