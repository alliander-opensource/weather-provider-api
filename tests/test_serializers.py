#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from enum import Enum

import pytest

from weather_provider_api.routers.weather import api_models
from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    WeatherContentRequestQuery,
)
from weather_provider_api.routers.weather.utils.serializers import (
    file_or_text_response,
    file_response,
)


class MockResponseFormat(str, Enum):
    mock_format = "mock_format"


@pytest.fixture()
def mock_response_query(mock_factors):
    result = WeatherContentRequestQuery(
        "2020-01-01", "2020-02-02", 51.873419, 5.705929, mock_factors
    )
    return result


@pytest.mark.parametrize(
    "response_format", [response.value for response in ResponseFormat]
)
def test_file_or_text_response_regular(
    response_format, mock_coordinates, mock_dataset, mock_response_query
):
    assert file_or_text_response(
        mock_dataset,
        ResponseFormat(response_format),
        "knmi",
        "pluim",
        mock_response_query,
        mock_coordinates,
    )


def test_file_or_text_response_forged_response_format(
    monkeypatch, mock_coordinates, mock_dataset, mock_response_query
):
    # TEST 1: Non-existing ResponseFormat is intercepted by Class
    with pytest.raises(ValueError) as e:
        assert file_or_text_response(
            mock_dataset,
            ResponseFormat("mock_format"),
            "knmi",
            "pluim",
            mock_response_query,
            [mock_coordinates],
        )
    assert str(e.value.args[0]) == "'mock_format' is not a valid ResponseFormat"

    # TEST 2: Forged non-existing ResponseFormat should be intercepted by file_response
    monkeypatch.setattr(api_models, "ResponseFormat", MockResponseFormat)
    with pytest.raises(NotImplementedError) as e:
        assert file_response(
            mock_dataset,
            api_models.ResponseFormat.mock_format,
            "knmi",
            "pluim",
            mock_response_query,
            [mock_coordinates],
        )
    assert (
        str(e.value.args[0])
        == f"Cannot create file response for the mock_format response format"
    )
