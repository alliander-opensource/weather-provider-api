#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import (
    HarmonieAromeRepository,
)


def main() -> None:
    """Script to erase the Arome repository.
    
    This is used to clear the repository of old data, for example when the data is corrupted or when the repository is
    full and needs to be cleared to make space for new data.
    """
    arome_repo = HarmonieAromeRepository()
    arome_repo.purge_repository(identifier="arome")


if __name__ == "__main__": # pragma: no cover
    main()
