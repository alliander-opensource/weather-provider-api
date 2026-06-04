#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import (
    ERA5SLRepository,
)


def main() -> None:
    """Script to erase the ERA5-SL repository.
    
    This is used to clear the repository of old data, for example when the data is corrupted or when the repository is
    full and needs to be cleared to make space for new data.
    """
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.purge_repository(identifier="era5sl")


if __name__ == "__main__":  # pragma: no cover
    main()
