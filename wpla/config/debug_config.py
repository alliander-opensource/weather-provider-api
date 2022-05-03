#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The debug configuration

Contains any settings that should be specific for a debugging environment.

"""


import os

from wpla.config.base_config import Configuration, ENVIRONMENT_PREFIX


class DebugConfiguration(Configuration):
    """Debug settings."""
    logging_level = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_DEFAULT_LOGGING_LEVEL", "DEBUG"
    )
    debugging = True
