#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from pathlib import Path

from loguru import logger

_NEEDED_CONFIG_FILES = ["config.toml"]


def get_main_project_folder() -> Path:
    """Identify and return the main project folder for the Weather Provider Libraries."""
    presumed_main_project_folder = Path(__file__).parent.parent.parent

    if (
        not presumed_main_project_folder.exists()
        or not presumed_main_project_folder.is_dir()
    ):
        raise NotADirectoryError(
            f"Main project folder for Weather Provider Libraries not found at: {presumed_main_project_folder}"
        )

    if (
        not presumed_main_project_folder.joinpath("core").exists()
        or not presumed_main_project_folder.joinpath("core").is_dir()
    ):
        raise NotADirectoryError(
            "Main project folder for Weather Provider Libraries is missing the 'data_classes' subfolder."
            "As such, it cannot be the main project folder."
            f"Main project folder for Weather Provider Libraries not found at: {presumed_main_project_folder}"
        )

    return presumed_main_project_folder


def get_main_config_folder() -> Path:
    """Identify and return the main configuration folder for the Weather Provider Libraries."""
    list_of_possible_config_folder_locations = [
        get_main_project_folder().parent.parent.joinpath("wpa_config"),
        Path("./wpa_config"),
        Path("/wpa_config"),
        Path("/etc/wpa_config"),
    ]
    for location in list_of_possible_config_folder_locations:
        if location.exists() and location.is_dir():
            for filename in _NEEDED_CONFIG_FILES:
                file = location.joinpath(filename)
                if not file.exists() or not file.is_file():
                    break
            return location
    # TODO: Fix
    raise FileNotFoundError(
        "No valid configuration folder found for the Weather Provider Libraries."
    )
