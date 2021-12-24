#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import tempfile

# Core Application Settings:
app_name = "weather_provider_lib_api"
description = "The Weather Provider Library and API"
maintainer_name = "DNB Verbindingsteam (Raoul Linnenbank)"
maintainer_email = "weather.provider@alliander.com"
package_name = "wpla"
valid_until_date = "2023-12-31"

# Extra Settings and Log Level:
show_maintainer = "True"
log_level = "INFO"

# Network settings:
network_interface = "127.0.0.1"
network_port = "8080"

# Storage settings:
storage_folder = tempfile.gettempdir()

# Deployment and debugging status:
deployed = False
debug = False

# API version data:
v2_version = "v2_0.8"
v3_version = "v3_0.8"
v2_valid_until_date = "2022-12-31"
v3_valid_until_date = "2023-12-31"
