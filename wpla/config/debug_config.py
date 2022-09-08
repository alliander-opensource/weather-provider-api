#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
==========================
Debug Configuration Module
==========================

This module contains the base DebugConfiguration class that holds all of the settings that should apply when debugging.

"""


import os

from wpla.config.base_config import Configuration, ENVIRONMENT_PREFIX


class DebugConfiguration(Configuration):
    """Debug settings."""
    config_type = 'debug_configuration'

    logging_level = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_DEFAULT_LOGGING_LEVEL", "DEBUG"
    )
    debugging = True
