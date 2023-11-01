#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Configuration folder """

import os
import tempfile
from pathlib import Path

from tomli import load

config_file_path = Path(__file__).parent.joinpath("config.toml")
with config_file_path.open(mode="rb") as file_processor:
    # TODO: Check if config.toml overwrite is set in the environment and replace accordingly!!!
    APP_CONFIG = load(file_processor)


# Settings taken from the environment if available.
APP_DEBUGGING = os.environ.get("WPLA_DEBUG", "False").lower() in ("true", "1", "y", "yes")
APP_DEPLOYED = os.environ.get("WPLA_DEPLOYED", "False").lower() in ("true", "1", "y", "yes")
APP_STORAGE_FOLDER = os.environ.get("WPLA_STORAGE_FOLDER", f"{tempfile.gettempdir()}/Weather_Repository")
APP_LOG_LEVEL = os.environ.get("WPLA_LOG_LEVEL", APP_CONFIG["logging"]["log_level"]).upper()
APP_SERVER = os.environ.get("WPLA_SERVER_URL", "http://127.0.0.1:8080")  # 127.0.0.1:8080 for debugging is the default
