#!/usr/bin/env python

#  SPDX-FileCopyrightText: 2019-2025 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""This is the module that contains the tools for the CDS API.

The cdsapi package and methods used to interact with the CDS API are defined here.
These are accredited to the Copernicus Climate Data Store (CDS) and the European Centre for Medium-Range Weather
Forecasts (ECMWF) and are licensed under the Apache License, Version 2.0 which can be found at
https://www.apache.org/licenses/LICENSE-2.0.

"""

from datetime import date
from enum import Enum

import cdsapi
from loguru import logger
from pydantic import BaseModel, Field

_DEFAULT_VARIABLES = [
    "stl1",
    "stl2",
    "stl3",
    "stl4",
    "swvl1",
    "swvl2",
    "swvl3",
    "swvl4",
]


def _info_callback(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
    """This is a callback function that is used to print information about the download process."""
    if len(args) > 0 or len(kwargs) > 0:
        logger.info("Callback received:")
        logger.info(" - args: ", *args)
        logger.info(" - kwargs: ", **kwargs)


class CDSDataSets(str, Enum):
    """Currently supported datasets for the CDS API."""

    ERA5SL = "reanalysis-era5-single-levels"
    ERA5LAND = "reanalysis-era5-land"


class CDSRequest(BaseModel):
    """A class that holds all necessary information for a CDS API request."""

    product_type: list[str] = Field(["reanalysis"])
    variables: list[str]
    year: list[str] = Field([date.strftime(date.today(), "%Y")])
    month: list[str] = Field([date.strftime(date.today(), "%m")])
    day: list[str] = Field([date.strftime(date.today(), "%d")])
    time: list[str] = Field(
        [
            "00:00",
            "01:00",
            "02:00",
            "03:00",
            "04:00",
            "05:00",
            "06:00",
            "07:00",
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
            "19:00",
            "20:00",
            "21:00",
            "22:00",
            "23:00",
        ],
    )
    data_format: str = "netcdf"
    download_format: str = "zip"
    area: tuple[float, float, float, float] = (53.7, 3.2, 50.75, 7.22)

    @property
    def request_parameters(self) -> dict[str, str | list[str] | tuple[float]]:
        """Returns the request parameters as a dictionary."""
        return {
            "product_type": self.product_type,
            "format": self.data_format,
            "variable": self.variables,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "time": self.time,
            "area": self.area,
            "data_format": self.data_format,
            "download_format": self.download_format,
            "grid_resolution": (0.25, 0.25),
        }


CDS_CLIENT = cdsapi.Client(info_callback=_info_callback(), url="https://cds.climate.copernicus.eu/api")
