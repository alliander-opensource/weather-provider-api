#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from importlib import metadata

import tomli

from weather_provider_api.core.utils.file_transformers import get_main_project_folder


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
        with open(get_main_project_folder().parent.parent.joinpath("pyproject.toml"), mode="rb") as project_file:
            version = tomli.load(project_file)["tool"]["poetry"]["version"]
        return version
    except FileNotFoundError:
        pass

    # Second attempt: Get the version number from the package that was used to install this component, if applicable.
    try:
        version = metadata.version(__package__)
        return version
    except metadata.PackageNotFoundError:
        pass

    # No version could be determined
    return "<< version could not be determined >>"


WP_API_APP_VERSION = _get_app_version()
