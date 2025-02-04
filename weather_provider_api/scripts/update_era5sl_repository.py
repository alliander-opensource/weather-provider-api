#!/usr/bin/env python


#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
import sys

from loguru import logger

from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import (
    ERA5SLRepository,
)


def main(args) -> None:
    """Run the update of the ERA5SL repository."""
    test_mode = False

    if len(args) == 2 and args[1] == "testmode":
        logger.warning("WARNING: Running in test mode")
        test_mode = True

    era5sl_repo = ERA5SLRepository()
    era5sl_repo.update(test_mode)


if __name__ == "__main__":
    main(sys.argv)
