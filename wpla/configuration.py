#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
===========================
API Configuration Interface
===========================

This module supplies the project with its configuration settings. It processes and selects an appropriate configuration
 based on only two base settings from the system environment, though alternate settings can be passed using that
 same system environment.

Based on any existing {ENVIRONMENT_PREFIX}_DEBUG and/or {ENVIRONMENT_PREFIX}_DEPLOYED environment variables found, a
 specific configuration is selected and retrieved from the four configuration files in the config package folder.

These four configuration files each contain solely the settings for one specific situation:

- base_config.py:              Holds all of the configuration settings that need to be applied regardless of the
  environment
- debug_config.py:             Holds all of the configuration settings that only apply in debugging situations
- deployed_config.py:          Holds all of the configuration settings that only apply when deployed
- deployed_debug_config.py:    Holds all of the configuration settings that only apply in situations where the project
  is both being debugged and deployed

Notes:

    As DebugConfiguration and DeployedConfiguration extend the base configuration and DebugDeployedConfiguration extends
     both the DebugConfiguration and the DeployedConfiguration, settings will carry over as follows:

    * Settings made in the Configuration class in base_config.py will be inherited by all other configuration classes
      unless overwritten.
    * Settings made in the DebugConfiguration and DeployedConfiguration classes can overwrite settings made in the
      Configuration class, and will be inherited by the DebugDeployedConfiguration class. DebugConfiguration settings
      will take precedence over DeployedConfiguration settings if settings exist in both classes.
    * The DebugDeployedConfiguration settings will only affect environments configured with both the DEBUG and DEPLOYED
      settings as true. As most configuration settings will already be properly inherited from the DebugConfiguration
      and DeployedConfiguration classes, there will usually be little reason to keep settings in this class.

"""

import os

from wpla.config.base_config import ENVIRONMENT_PREFIX, Configuration
from wpla.config.debug_config import DebugConfiguration
from wpla.config.deployed_config import DeployedConfiguration
from wpla.config.deployed_debug_config import DebugDeployedConfiguration


def get_configuration(debugging: bool, deployed: bool):
    """ This function returns the appropriate configuration based on the two passed parameters """
    if not debugging and not deployed:
        return Configuration()
    if debugging and not deployed:
        return DebugConfiguration()
    if not debugging and deployed:
        return DeployedConfiguration()
    return DebugDeployedConfiguration()


# The app_config variable is how the project knows what configuration settings to use while running
app_config = get_configuration(
    bool(os.environ.get(f"{ENVIRONMENT_PREFIX}_DEBUG", False)),
    bool(os.environ.get(f"{ENVIRONMENT_PREFIX}_DEPLOYED", False)),
)
