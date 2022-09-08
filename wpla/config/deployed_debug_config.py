#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
=======================================
Debug and Deployed Configuration Module
=======================================

This module contains the base DebugDeployedConfiguration class that holds all of the settings that should apply on an
actively deployed server that is being debugged.

Notes:
    Running in a mode that is both debugging and deployed should not happen without good reason.
    That goes double for any settings made for this mode.

"""

from wpla.config.debug_config import DebugConfiguration
from wpla.config.deployed_config import DeployedConfiguration


class DebugDeployedConfiguration(DebugConfiguration, DeployedConfiguration):
    """Debugging and deployed settings."""
    config_type = 'debug_deployed_configuration'
