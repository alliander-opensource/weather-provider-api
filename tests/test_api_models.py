#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import datetime

from weather_provider_api.routers.weather.api_models import ScientificJSONResponse


# The custom float encoder is the sole function inside api_models.py and is therefore the only thing that needs testing.
def test_custom_json_float_encoder():
    # Setting up generic weather output format, ready for value injection
    mock_response = ScientificJSONResponse(
        {
            "coords": {
                "time": {
                    "dims": ("time",),
                    "attrs": {"long_name": "time"},
                    "data": [datetime.utcnow()],
                    "coord": {"dims": ("coord",), "attrs": {}, "data": [(5.25, 52.0)]},
                },
                "attrs": {},
                "dims": {"coord": 1, "time": 744},
                "data_vars": {
                    "2m_dewpoint_temperature": {
                        "dims": ("time", "coord"),
                        "attrs": {
                            "units": "K",
                            "long_name": "2 metre dewpoint temperature",
                        },
                        "data": [[279.6545715332031]],
                    }
                },
            }
        }
    )

    # Test NaN
    assert mock_response.render(float("nan")) == b"null"

    # Test infinity
    assert mock_response.render(float("inf")) == b"Infinity"

    # Test negative infinity
    assert mock_response.render(-float("inf")) == b"-Infinity"
