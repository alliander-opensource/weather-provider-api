#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import os
import tempfile
from importlib import metadata as importlib_metadata
from pathlib import Path

import tomli


class BaseConfig(object):
    """ Base configuration class

    This class holds and/or gathers all the APIs base settings...

    """

    APP_NAME = os.environ.get("APP_NAME", __name__)
    APP_DESCRIPTION = os.environ.get("APP_DESCRIPTION", """Alliander Weather Provider API""")
    APP_MAINTAINER = os.environ.get("APP_MAINTAINER", "DNB/ST Innovatieteam")
    APP_MAINTAINER_EMAIL = os.environ.get(
        "APP_MAINTAINER_EMAIL", "weather.provider@alliander.com"
    )
    SHOW_MAINTAINER = os.environ.get("SHOW_MAINTAINER", False)

    default_version = None
    try:
        if Path('./pyproject.toml').exists():
            pyproject_file = Path('./pyproject.toml')
        elif Path('../pyproject.toml').exists():
            pyproject_file = Path('../pyproject.toml')
        with open(pyproject_file, mode='rb') as file:
            default_version = tomli.load(file)['tool']['poetry']['version']
    except Exception:
        default_version = importlib_metadata.version(__package__)
    finally:
        if not default_version:
            default_version = 'Version Unidentified'
    APP_VERSION = os.environ.get("APP_VERSION", default_version)

    APP_V1_VERSION = os.environ.get("APP_V1_VERSION", f"{APP_VERSION} - v1 API (1.0.3)")
    APP_V2_VERSION = os.environ.get("APP_V1_VERSION", f"{APP_VERSION} - v2 API (2.0.3)")
    APP_VALID_DATE = os.environ.get("APP_VALID_DATE", "2024-12-31")
    NETWORK_INTERFACE = os.environ.get("NETWORK_INTERFACE", "127.0.0.1")
    NETWORK_PORT = os.environ.get("NETWORK_PORT", 8080)
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")

    # The following two parameters determine the active configuration
    DEPLOYED = os.environ.get("DEPLOYED", False)
    DEBUG = os.environ.get("DEBUG", True)

    REPO_FOLDER = os.environ.get("REPO_FOLDER", f"{tempfile.gettempdir()}/Weather_Repository")


class LocalConfig(BaseConfig):
    pass


class LocalDebugConfig(LocalConfig):
    DEBUG = True
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")


class DeployedConfig(BaseConfig):
    NETWORK_INTERFACE = os.environ.get("NETWORK_INTERFACE", "0.0.0.0")
    DEPLOYED = True


class DeployedDebugConfig(DeployedConfig):
    DEBUG = True
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")


_active_config = None


def get_active_config():  # pragma: no cover
    """Retrieve the active configuration.

    The active configuration is based on the DEPLOYED and DEBUG
    environment variables. The active config is set once and returned
    for each subsequent call.

    Returns:
        Active configuration
    """
    global _active_config

    is_deployed = os.environ.get("DEPLOYED", False)
    is_debug = os.environ.get("DEBUG", False)

    if _active_config is None:
        if is_deployed:
            if is_debug:
                _active_config = DeployedDebugConfig
            else:
                _active_config = DeployedConfig
        else:
            if is_debug:
                _active_config = LocalDebugConfig
            else:
                _active_config = LocalConfig

    return _active_config


def get_setting(key: str):
    """Return value set for key.

    Args:
        key (str): key of configuration setting

    Returns:
        value if key exists, None otherwise
    """
    active_config = get_active_config()
    return getattr(active_config, key, None)
