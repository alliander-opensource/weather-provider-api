#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import asyncio
import os
import site
from pathlib import Path

from loguru import logger


async def remove_file(file_path: str | Path | None) -> bool:  # pragma: no cover
    """Remove a file asynchronously."""
    if file_path is not None:
        file_to_rm = Path(file_path).resolve()
        logger.info("Removing temporary file", file_path=file_to_rm)
        if file_to_rm.exists() and file_to_rm.is_file():
            await asyncio.to_thread(file_to_rm.unlink)
    return True


def get_var_map_file_location(filename: str) -> Path:
    """Get the location of a variable map file."""
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
