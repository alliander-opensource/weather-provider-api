#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import os
from pathlib import Path

"""Deployed Configuration

This module holds the deployed configuration options to be used for the API.
"""

DeployedConfig = {
    # Network settings:
    "network_interface": os.environ.get("WPLA_NETWORK_INTERFACE", "0.0.0.0"),

    # Storage settings:
    "storage_folder": os.environ.get("WPLA_STORAGE_FOLDER", str(Path(__file__).absolute().root.join("WPLA_STORAGE"))),
}
