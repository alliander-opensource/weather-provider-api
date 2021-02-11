#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from app.routers.weather.sources.cds.client.era5sl_repository import ERA5SLRepository

if __name__ == "__main__":
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.purge_repository()
