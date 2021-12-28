#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
###################
Debug Configuration
###################

This module holds the debugging configuration options to be used for the API.

Note:
    As the DebugConfig dictionary is always added last (if applicable), settings in this dictionary will overwrite any
    settings with the same name in any other configuration file.
"""
import os


DebugConfig = {
    "log_level": os.environ.get("WPLA_LOG_LEVEL", "DEBUG"),
}
