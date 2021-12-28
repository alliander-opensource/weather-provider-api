#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
##################
Base Configuration
##################

This module holds all the base configuration options that will be used to configure the API.

Note:
    Any settings made in the DevelopmentConfig, DeployedConfig and DebugConfig dictionaries that overlap with a setting
    in this file will overwrite that setting.
"""
import os
import tempfile
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version

from wpla.api.versions.v2 import v2_api_version, v2_api_validation_date
from wpla.api.versions.v3 import v3_api_version, v3_api_validation_date

try:
    main_version = version("wpla")
except PackageNotFoundError:
    main_version = "0.0.001"

_date_as_string_format = '%Y-%m-%d'

BaseConfig = {
    # Core Application Settings:
    "app": {
        "name": os.environ.get("WPLA_APP_NAME", "weather_provider_lib_api"),
        "description": os.environ.get("WPLA_APP_DESCRIPTION", "The Weather Provider Libraries and API"),
        "maintainer": os.environ.get("WPLA_APP_MAINTAINER", "DNB Verbindingsteam (Contact: Raoul Linnenbank)"),
        "maintainer_email": os.environ.get("WPLA_APP_MAINTAINER_EMAIL", "weather.provider@alliander.com"),
        "version": os.environ.get("WPLA_MAIN_VERSION", main_version),
        "valid_until": datetime.strptime(os.environ.get("WPLA_VALID_UNTIL_DATE", "2023-12-31"), _date_as_string_format),
        "active_api_versions": {
            "v2_version": os.environ.get("WPLA_API_V2_VERSION", v2_api_version),
            "v2_valid_until": datetime.strptime(
                os.environ.get("WPLA_API_V2_VALID_UNTIL_DATE", v2_api_validation_date),
                _date_as_string_format
            ),
            "v3_version": os.environ.get("WPLA_API_V3_VERSION", v3_api_version),
            "v3_valid_until": datetime.strptime(
                os.environ.get("WPLA_API_V3_VALID_UNTIL_DATE", v3_api_validation_date),
                _date_as_string_format
            )
        }
    },

    # Extra Settings and Log Level:
    "show_maintainer":  bool(os.environ.get("WPLA_SHOW_MAINTAINER", True)),
    "log_level": os.environ.get("WPLA_LOG_LEVEL", "INFO"),

    # Network settings:
    "network_interface": os.environ.get("WPLA_NETWORK_INTERFACE", "127.0.0.1"),
    "network_port": int(os.environ.get("WPLA_NETWORK_PORT", "8080")),

    # Storage settings:
    "storage_folder": os.environ.get("WPLA_STORAGE_FOLDER", tempfile.gettempdir()),

    # Deployment and debugging status:
    "deployed": bool(os.environ.get("WPLA_DEPLOYED", False)),
    "debug": bool(os.environ.get("WPLA_DEBUG", False))
}
