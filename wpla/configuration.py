#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
******************************
WPLA main configuration module
******************************

This module loads the appropriate configuration dictionary for the deployment and debug settings gathered from the
environment. It does this by loading a BaseConfig dictionary of settings and merging it with the Config dictionary or
dictionaries that match the environment. The resulting configuration is loaded into the "Config" variable which can
easily be loaded directly from this module.

Note:
    Though three configuration dictionaries are available for extending the base configuration settings, only up to two
    of those will be loaded in practice, as DevelopmentConfig and DeployConfig are mutually exclusive.

================= ============ ============= ============ ============
Environment:      debug=False, debug==True,  debug==False debug==True
                  deploy=False deploy==False deploy==True deploy==True
================= ============ ============= ============ ============
DebugConfig       False        True          False        True
DeployConfig      False        False         True         True
DevelopmentConfig True         True          False        False
================= ============ ============= ============ ============

Warning:
    *The configuration settings mentioned in this module have nothing to do with the available WeatherSource or
    WeatherModel resources! These settings only apply to the API itself.*
"""
from typing import Any, Dict

from wpla import config

ConfigDict = Dict[str, Any]


def _extend_config_dict(base_config: ConfigDict, extension: ConfigDict):
    for key in extension.keys():
        if (key in base_config.keys()
                and isinstance(base_config[key], dict)
                and isinstance(extension[key], dict)):
            _extend_config_dict(base_config[key], extension[key])
        else:
            base_config[key] = extension[key]


def _build_config(base_config: ConfigDict, *specific_configs: ConfigDict) -> ConfigDict:
    result_config = base_config
    for specific_config in specific_configs:
        _extend_config_dict(result_config, specific_config)

    return result_config


def get_config(deployed: bool, debug: bool) -> ConfigDict:
    """Builds a configuration dictionary extending base settings with settings from files specific for the requested
    API environment.

    Args:
        deployed(bool): Is the environment considered "deployed"?
        debug(bool): Is the environment's purpose one of "debugging"?

    Returns:
        A dictionary holding the configuration settings applicable to the requested environment.

    """
    if deployed:
        if debug:
            return _build_config(config.BaseConfig, config.DeployedConfig, config.DebugConfig)
        else:
            return _build_config(config.BaseConfig, config.DeployedConfig)
    else:
        if debug:
            return _build_config(config.BaseConfig, config.DevelopmentConfig, config.DebugConfig)
        else:
            return _build_config(config.BaseConfig, config.DevelopmentConfig)


Config = get_config(config.BaseConfig["deployed"], config.BaseConfig["debug"])
