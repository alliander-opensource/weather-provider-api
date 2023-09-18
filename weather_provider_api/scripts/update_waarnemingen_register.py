#!/usr/bin/env python
# -*- coding: utf-8 -*-


#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
from weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository import (
    ActueleWaarnemingenRegisterRepository,
)


def main():
    waarnemingen_repo = ActueleWaarnemingenRegisterRepository()
    waarnemingen_repo.update()


if __name__ == "__main__":  # pragma: no cover
    main()
