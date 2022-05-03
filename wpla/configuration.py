#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The configuration for the API itself

This module processes the appropriate configuration for the API itself.
The settings themselves are gathered using the following separate files:
    - base_config.py
    - debug_config.py
    - deployed_config.py
    - deployed_debug_config.py

These files configure the settings appropriate for their specific configurations by reading configuration settings
from the environment, if available, or by supplying default settings when they are not.

Depending on any found {ENVIRONMENT_PREFIX}_DEBUG and {ENVIRONMENT_PREFIX}_DEPLOYED environment settings a
configuration will be loaded.

As DebugConfiguration and DeployedConfiguration extend the base configuration and DebugDeployedConfiguration extends
both the DebugConfiguration and the DeployedConfiguration, settings will carry over as follows:

 * Settings made in the Configuration class in base_config.py will be inherited by all other configuration classes
 unless overwritten.
 * Settings made in the DebugConfiguration and DeployedConfiguration classes can overwrite settings made in the
 Configuration class, and will be inherited by the DebugDeployedConfiguration class. DebugConfiguration settings will
 take precedence over DeployedConfiguration settings if settings exist in both classes.
 * The DebugDeployedConfiguration settings will only affect environments configured with both the DEBUG and DEPLOYED
 settings as true. As most configuration settings will already be properly inherited from the DebugConfiguration and
 DeployedConfiguration classes, there will usually be little reason to keep settings in this class.

"""

import os

from wpla.config.base_config import ENVIRONMENT_PREFIX, Configuration
from wpla.config.debug_config import DebugConfiguration
from wpla.config.deployed_config import DeployedConfiguration
from wpla.config.deployed_debug_config import DebugDeployedConfiguration


def get_configuration(debugging: bool, deployed: bool):
    """Fetch the proper configuration based on the debugging and deployment settings."""
    if not debugging and not deployed:
        return Configuration()
    if debugging and not deployed:
        return DebugConfiguration()
    if not debugging and deployed:
        return DeployedConfiguration()
    return DebugDeployedConfiguration()


app_config = get_configuration(
    bool(os.environ.get(f"{ENVIRONMENT_PREFIX}_DEBUG", False)),
    bool(os.environ.get(f"{ENVIRONMENT_PREFIX}_DEPLOYED", False)),
)
