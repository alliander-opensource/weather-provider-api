#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import (
    ERA5SLRepository,
)


def main():
    # Simple method wrapper for purging data
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.purge_repository()


if __name__ == "__main__":
    main()
