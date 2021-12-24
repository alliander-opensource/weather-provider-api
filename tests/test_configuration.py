#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from wpla import config
from wpla.config.utils.config_utils import build_config
from wpla.configuration import _get_config


def test__get_config():
    # Case #1 Deployed and Debugging
    valid_result = build_config(config.BaseConfig, config.DeployedConfig, config.DebugConfig)
    result = _get_config(True, True)
    assert result == valid_result

    # Case #2 Deployed and NOT Debugging
    valid_result = build_config(config.BaseConfig, config.DeployedConfig)
    result = _get_config(True, False)
    assert result == valid_result

    # Case #3 NOT Deployed and Debugging
    valid_result = build_config(config.BaseConfig, config.DebugConfig, config.DevelopmentConfig)
    result = _get_config(False, True)
    assert result == valid_result

    # Case #3 NOT Deployed and NOT Debugging
    valid_result = build_config(config.BaseConfig, config.DevelopmentConfig)
    result = _get_config(False, False)
    assert result == valid_result
