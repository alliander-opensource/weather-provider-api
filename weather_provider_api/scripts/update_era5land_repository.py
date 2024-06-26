#!/usr/bin/env python

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

# -*- coding: utf-8 -*-
from weather_provider_api.routers.weather.sources.cds.client.era5land_repository import (
    ERA5LandRepository,
)


def main():
    era5land_repo = ERA5LandRepository()
    era5land_repo.update()


if __name__ == "__main__":  # pragma: no cover
    main()
