#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import os
import site
from pathlib import Path

from loguru import logger


async def remove_file(file_path):  # pragma: no cover
    if file_path is not None:
        try:
            file_to_rm = Path(file_path).resolve()
            logger.info("Removing temporary file", file_path=file_to_rm)
            if file_to_rm.exists() and file_to_rm.is_file():
                file_to_rm.unlink()
        except FileNotFoundError as e:
            logger.exception(e)
            raise
    return True


def get_var_map_file_location(filename: str) -> Path:
    var_map_folder = "var_maps"

    possible_main_folders = [
        Path(os.getcwd()),  # Running from main folder
        Path(os.getcwd()).parent,  # Running from weather_provider_api folder or scripts
        Path(site.getsitepackages()[-1]),  # Running as package
    ]

    for folder in possible_main_folders:
        possible_var_map_folder = folder.joinpath(var_map_folder)
        if possible_var_map_folder.exists():
            logger.info(f'"var_maps" folder was found at: {possible_var_map_folder}')
            return possible_var_map_folder.joinpath(filename)

    logger.exception(f"File was not found: {filename}")
    raise FileNotFoundError
