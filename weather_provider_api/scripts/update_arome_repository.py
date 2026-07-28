# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import (
    HarmonieAromeRepository,
)


def main() -> None:
    """Script to update the Arome repository."""
    arome_repo = HarmonieAromeRepository()
    arome_repo.update()


if __name__ == "__main__":
    main()
