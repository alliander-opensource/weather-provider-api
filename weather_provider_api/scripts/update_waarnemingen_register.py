# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import sys

from loguru import logger

from weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository import (
    ActueleWaarnemingenRegisterRepository,
)


def main(args: list[str] | None = None) -> None:
    """Run the update of the Actuele Waarnemingen Register repository."""
    test_mode = False

    if args is None:
        args = sys.argv

    if len(args) == 2 and args[1] == "testmode":
        logger.warning("WARNING: Running in test mode")
        test_mode = True

    waarnemingen_repo = ActueleWaarnemingenRegisterRepository()
    waarnemingen_repo.update(run_in_testmode=test_mode)


if __name__ == "__main__":  # pragma: no cover
    main()
