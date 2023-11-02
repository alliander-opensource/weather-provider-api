#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Version detection module """

from importlib import metadata

import tomli
from loguru import logger


def _get_app_version() -> str:
    """This method tries to identify the API's main version identifier and return it.

    Returns:
        str:    The found version identifier, if found. If no version identifier was found, a warning value is returned
                 instead.

    """
    # First attempt: Get the version number by looking for a pyproject.toml file in the working directory.
    # Please note that this assumes that this function was called from a context that has the Project's main folder as
    #  the working directory.
    try:
        with open("./pyproject.toml", mode="rb") as project_file:
            version = tomli.load(project_file)["tool"]["poetry"]["version"]
        logger.info(f"Retrieved the project version from the pyproject.toml file: {version}")
        return version
    except FileNotFoundError as fnf_error:
        logger.debug(f"Could not retrieve the active version from the pyproject.toml file: {fnf_error}")

    # Second attempt: Get the version number from the package that was used to install this component, if applicable.
    try:
        version = metadata.version(__package__)
        logger.info(f"Retrieved the project version from package data: {version}")
        return version
    except metadata.PackageNotFoundError as pnf_error:
        logger.debug(f"Could not retrieve the active version from package data: {pnf_error}")

    # No version could be determined
    logger.warning("No version could be found for the project!")
    return "<< version could not be determined >>"


APP_VERSION = _get_app_version()
