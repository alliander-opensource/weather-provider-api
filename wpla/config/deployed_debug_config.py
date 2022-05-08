#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The debug-deployed configuration

Contains any settings that should be specific for an environment that is both for debugging and full deployment.

"""

from wpla.config.debug_config import DebugConfiguration
from wpla.config.deployed_config import DeployedConfiguration


class DebugDeployedConfiguration(DebugConfiguration, DeployedConfiguration):
    """Debugging and deployed settings."""
    config_type = 'debug_deployed_configuration'
