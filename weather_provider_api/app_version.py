# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Version detection module."""

from importlib.metadata import PackageNotFoundError, version

from loguru import logger


def _get_app_version() -> str:
    """Return the version recorded in the installed distribution metadata.

    Returns:
        str: The installed project version, or a marker when package metadata is unavailable.
    """
    try:
        app_version = version("weather_provider_api")
    except PackageNotFoundError:
        logger.warning("Could not retrieve the project version from installed package metadata.")
        return "<< version could not be determined >>"

    logger.info("Retrieved the project version from installed package metadata: {}", app_version)
    return app_version



APP_VERSION = _get_app_version()
