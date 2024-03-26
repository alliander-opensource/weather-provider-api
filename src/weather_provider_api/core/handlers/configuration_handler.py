#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import os

import tomli
from loguru import logger

from weather_provider_api.core.utils.file_transformers import get_main_config_folder


with open(get_main_config_folder().joinpath("config.toml"), mode="rb") as config_file:
    WP_API_CONFIG = tomli.load(config_file)

logger.debug("WP API - Loaded the configuration file.")

WP_API_ENV_VARS = {
    key.replace("WP_API_", "").upper(): value.upper()
    for key, value in os.environ.items()
    if key.startswith("WP_API_")
}
