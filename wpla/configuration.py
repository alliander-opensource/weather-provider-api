#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from wpla import config
from wpla.config.utils.config_utils import build_config, ConfigDict

"""Main configuration file.

This module loads the appropriate configuration dictionary for the deployment and debug settings gathered from the 
environment. It does this by loading a BaseConfig dictionary of settings and merging it with the Config dictionary or 
dictionaries that match the environment. The resulting configuration is loaded into the "Config" variable which can 
easily be loaded directly from this module. 

The default behaviour when no deployment or debug information can be gathered from the system is as follows:
- Debugging: False
- Deployed: False
This should cause only the development settings to be loaded next to the base configuration.

Notes:
    Though three extending configuration settings exist, only up to two will be loaded. Development and Deployed 
    configurations are mutually exclusive. In a "Deployed" environment, the DeployedConfig settings will be added, and
    in a "not Deployed" environment, this will be the DevelopmentConfig settings.
    
    A Debugging configuration will then be added if the environments indicate a debugging environment.
    
    __This configuration file has nothing to do with the available WeatherSource or WeatherModel resources!__ 
"""


def _get_config(deployed: bool, debug: bool) -> ConfigDict:
    if deployed:
        if debug:
            return build_config(config.BaseConfig, config.DeployedConfig, config.DebugConfig)
        else:
            return build_config(config.BaseConfig, config.DeployedConfig)
    else:
        if debug:
            return build_config(config.BaseConfig, config.DevelopmentConfig, config.DebugConfig)
        else:
            return build_config(config.BaseConfig, config.DevelopmentConfig)


Config = _get_config(config.BaseConfig["deployed"], config.BaseConfig["debug"])
