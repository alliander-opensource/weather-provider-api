#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository import (
    ActueleWaarnemingenRegisterRepository,
)


def main():
    # Simple method wrapper for purging data
    waarnemingen_repo = ActueleWaarnemingenRegisterRepository()
    waarnemingen_repo.purge_repository()


if __name__ == "__main__":
    main()
