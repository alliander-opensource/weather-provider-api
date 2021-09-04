#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import os

from weather_provider_api.app.core.utilities.string_helpers import parse_bool

BaseConfig = {
    "app": {
        "name": os.environ.get("APP_NAME", "weather_provider_api"),
        "description": os.environ.get("APP_DESCRIPTION", """Weather Provider API"""),
        "maintainer": os.environ.get("APP_MAINTAINER", "DNB/ST Innovatieteam (Raoul Linnenbank)"),
        "maintainer_email": os.environ.get("APP_MAINTAINER_EMAIL", "weather.provider@alliander.com"),
        "main_version": os.environ.get("APP_VERSION", "3.0.0a"),
        "valid_date": os.environ.get("APP_VALID_DATE", "2022-12-31"),
        "endpoints": {
            "v2_version": os.environ.get("APP_V2_VERSION", "0.1_API2"),
            "v2_valid_date": os.environ.get("APP_V2_VALID_DATE", "2022-12-31"),
            "v3_version": os.environ.get("APP_V3_VERSION", "0.1_API3"),
            "v3_valid_date": os.environ.get("APP_V3_VALID_DATE", "2022-12-31"),
        }
    },

    "show_maintainer": os.environ.get("SHOW_MAINTAINER", True),  # TODO: PRIORITY_2 -- Switch the default back to False
                                                                 #  before the final release
    "log_level": os.environ.get("LOG_LEVEL", "INFO"),

    "network_interface": os.environ.get("NETWORK_INTERFACE", "127.0.0.1"),
    "network_port": os.environ.get("NETWORK_PORT", 8080),

    "data_storage_folder": os.environ.get("DATA_FOLDER", 'C:\\TEMP'),

    # The following two settings determine the active config
    "deployed": parse_bool(os.environ.get("DEPLOYED", False)),
    "debug": parse_bool(os.environ.get("DEBUG", False)),
}
