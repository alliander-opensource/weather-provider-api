#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import os

"""Debug Configuration

This module holds the debugging configuration options to be used for the API.
"""

DebugConfig = {
    "log_level": os.environ.get("WPLA_LOG_LEVEL", "DEBUG"),
}
