#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import os

DeployedConfig = {
    "data_storage_folder": os.environ.get("REPO_FOLDER", '/tmp/Weather_Repository'),

    "network_interface": os.environ.get("NETWORK_INTERFACE", "0.0.0.0"),
    "deployed": True
}
