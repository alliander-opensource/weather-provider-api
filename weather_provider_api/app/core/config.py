#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, Any

from weather_provider_api import config

# --- START OF UTILITIES TO SET UP CONFIG FILE ---

ConfigDict = Dict[str, Any]


def _extend_config_dict(base_config: ConfigDict, extension: ConfigDict):
    """ This function extends a single ConfigDict with another ConfigDict and returns the result

    Args:
        base_config:    The base ConfigDict to extend
        extension:      The ConfigDict to extend it with

    Returns:
        Nothing: the base_config alterations don't need to be returned

    """
    for key in extension.keys():
        if (key in base_config.keys()
                and isinstance(base_config[key], dict)
                and isinstance(extension[key], dict)):
            _extend_config_dict(base_config[key], extension[key])
        else:
            base_config[key] = extension[key]


def _build_config(base_config: ConfigDict, *specific_configs: ConfigDict) -> ConfigDict:
    """ This function builds a composite ConfigDict from multiple ConfigDicts and returns the result

    It does this by extending a generic base configuration with one or more specific configuration settings into a
    single ConfigDict

    Args:
        base_config:        A Base ConfigDict to use
        *specific_configs:  One or more specific sub-ConfigDicts to extend the base with

    Returns:
        A ConfigDict item consisting of all of the ConfigDict data supplied
    """
    result_config = base_config
    for specific_config in specific_configs:
        _extend_config_dict(result_config, specific_config)

    return result_config


def _get_config(deployed: bool, debug: bool):
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


# --- END OF UTILITIES TO SET UP CONFIG FILE ---

""" This Module set up the configuration settings for the requested run, and makes it readily available to other modules.

The variable 'Config' from this module holds the the proper configuration.
"""
Config = _get_config(config.BaseConfig["deployed"], config.BaseConfig["debug"])
