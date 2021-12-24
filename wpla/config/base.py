#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import os
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version

from wpla.config import default_settings

"""Base Configuration

This module holds the base configuration options to be used for the API. Duplicates for a specific setting (deployed, 
development or debugging) may overwrite these settings.
"""

try:
    main_version = version(default_settings.package_name)
except PackageNotFoundError:
    main_version = "0.0.001"

_date_as_string_format = '%Y-%m-%d'

BaseConfig = {
    # Core Application Settings:
    "app": {
        "name": os.environ.get("WPLA_APP_NAME", default_settings.app_name),
        "description": os.environ.get("WPLA_APP_DESCRIPTION", default_settings.description),
        "maintainer": os.environ.get("WPLA_APP_MAINTAINER", default_settings.maintainer_name),
        "maintainer_email": os.environ.get("WPLA_APP_MAINTAINER_EMAIL", default_settings.maintainer_email),
        "version": os.environ.get("WPLA_MAIN_VERSION", main_version),
        "valid_until": datetime.strptime(os.environ.get("WPLA_VALID_UNTIL_DATE", default_settings.valid_until_date),
                                         _date_as_string_format),
        "active_api_versions": {
            "v2_version": os.environ.get("WPLA_API_V2_VERSION", default_settings.v2_version),
            "v2_valid_until": datetime.strptime(
                os.environ.get("WPLA_API_V2_VALID_UNTIL_DATE", default_settings.v2_valid_until_date),
                _date_as_string_format
            ),
            "v3_version": os.environ.get("WPLA_API_V3_VERSION", default_settings.v3_version),
            "v3_valid_until": datetime.strptime(
                os.environ.get("WPLA_API_V3_VALID_UNTIL_DATE", default_settings.v3_valid_until_date),
                _date_as_string_format
            )
        }
    },

    # Extra Settings and Log Level:
    "show_maintainer": os.environ.get("WPLA_SHOW_MAINTAINER", default_settings.show_maintainer),
    "log_level": os.environ.get("WPLA_LOG_LEVEL", default_settings.log_level),

    # Network settings:
    "network_interface": os.environ.get("WPLA_NETWORK_INTERFACE", default_settings.network_interface),
    "network_port": int(os.environ.get("WPLA_NETWORK_PORT", default_settings.network_port)),

    # Storage settings:
    "storage_folder": os.environ.get("WPLA_STORAGE_FOLDER", default_settings.storage_folder),

    # Deployment and debugging status:
    "deployed": bool(os.environ.get("WPLA_DEPLOYED", default_settings.deployed)),
    "debug": bool(os.environ.get("WPLA_DEBUG", default_settings.debug))
}
