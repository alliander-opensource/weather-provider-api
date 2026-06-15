#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository import (
    ActueleWaarnemingenRegisterRepository,
)


def main() -> None:
    """Script to erase the Actuele Waarnemingen Register repository.
    
    This is used to clear the repository of old data, for example when the data is corrupted or when the repository is
    full and needs to be cleared to make space for new data.
    """
    waarnemingen_repo = ActueleWaarnemingenRegisterRepository()
    waarnemingen_repo.purge_repository(identifier="waarnemingen_register")


if __name__ == "__main__":  # pragma: no cover
    main()
