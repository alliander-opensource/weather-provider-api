#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0


from weather_provider_api.routers.weather.sources.cds.client.era5land_repository import (
    ERA5LandRepository,
)


def main() -> None:
    """Script to erase the ERA5-Land repository.
    
    This is used to clear the repository of old data, for example when the data is corrupted or when the repository is
    full and needs to be cleared to make space for new data.
    """
    era5land_repo = ERA5LandRepository()
    era5land_repo.purge_repository(identifier="era5land")


if __name__ == "__main__":  # pragma: no cover
    main()
