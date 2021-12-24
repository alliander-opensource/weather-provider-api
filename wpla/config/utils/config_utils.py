#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from typing import Dict, Any

"""Configuration Utilities

This module holds the tools that properly prioritize construct the final configuration from its separate components.
This system should be able to handle any reasonable level of complexity from its supplied configuration dictionaries.  
"""


ConfigDict = Dict[str, Any]


def _extend_config_dict(base_config: ConfigDict, extension: ConfigDict):
    for key in extension.keys():
        if (key in base_config.keys()
                and isinstance(base_config[key], dict)
                and isinstance(extension[key], dict)):
            _extend_config_dict(base_config[key], extension[key])
        else:
            base_config[key] = extension[key]


def build_config(base_config: ConfigDict, *specific_configs: ConfigDict) -> ConfigDict:
    result_config = base_config
    for specific_config in specific_configs:
        _extend_config_dict(result_config, specific_config)

    return result_config
