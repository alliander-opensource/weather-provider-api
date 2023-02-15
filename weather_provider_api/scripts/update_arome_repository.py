#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import HarmonieAromeRepository


def main():
    arome_repo = HarmonieAromeRepository()
    arome_repo.update()


if __name__ == "__main__":
    main()
