#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The deployed configuration

Contains any settings that should be the default for a deployed environment.

"""


import os

from wpla.config.base_config import Configuration, ENVIRONMENT_PREFIX


class DeployedConfiguration(Configuration):
    """Deployed settings"""
    config_type = 'deployed_configuration'

    network_interface_ip = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_NETWORK_INTERFACE", "0.0.0.0"
    )
    deployed = True
