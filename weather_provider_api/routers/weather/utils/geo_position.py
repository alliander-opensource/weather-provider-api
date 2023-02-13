#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import math
from enum import Enum

"""
Modules translates RC coordinates to WGS84 and vice versa.
This module uses an approximation system originating from a document known as "Transformatieformules.pdf" from Dutch
site http://dekoepel.nl, though the file can no longer be found there.

To convert RC to WGS84 this module uses Function 6 from the original document in combination with Table 4.
To convert WGS84 to RC it uses Function 7 in combination with Table 5.

Because RC doesn't have its center at zero coordinates, we also use Table 3 to properly offset the coordinates for
calculation.
"""


# Coordinate Enum to allow for easy adding of more coordinate types
class CoordinateSystem(str, Enum):
    rd = "RD"
    wgs84 = "WGS84"


class GeoPosition:
    # Zero point configuration (Table 3) based on the center point of the RD coordinate system
    # (phi and lambda shift (very) slightly over the years...)
    X0 = 155000.0
    Y0 = 463000.0
    PHI0 = 52.15517440
    LAMBDA0 = 5.38720621

    # Tables 4 & 5
    K = [
        [0, 1, 3235.65389],
        [2, 0, -32.58297],
        [0, 2, -0.24750],
        [2, 1, -0.84978],
        [0, 3, -0.06550],
        [2, 2, -0.01709],
        [1, 0, -0.00738],
        [4, 0, 0.00530],
        [2, 3, -0.00039],
        [4, 1, 0.00033],
        [1, 1, -0.00012],
    ]
    L = [
        [1, 0, 5260.52916],
        [1, 1, 105.94684],
        [1, 2, 2.45656],
        [3, 0, -0.81885],
        [1, 3, 0.05594],
        [3, 1, -0.05607],
        [0, 1, 0.01199],
        [3, 2, -0.00256],
        [1, 4, 0.00128],
        [0, 2, 0.00022],
        [2, 0, -0.00022],
        [5, 0, 0.00026],
    ]
    R = [
        [0, 1, 190094.945],
        [1, 1, -11832.228],
        [2, 1, -114.221],
        [0, 3, -32.391],
        [1, 0, -0.705],
        [3, 1, -2.340],
        [1, 3, -0.608],
        [0, 2, -0.008],
        [2, 3, 0.148],
    ]
    S = [
        [1, 0, 309056.544],
        [0, 2, 3638.893],
        [2, 0, 73.077],
        [1, 2, -157.984],
        [3, 0, 59.788],
        [0, 1, 0.433],
        [2, 2, -6.439],
        [1, 1, -0.032],
        [0, 4, 0.092],
        [1, 4, -0.054],
    ]

    def __init__(self, xcoord, ycoord, locformat=None):
        self.x = xcoord
        self.y = ycoord
        if locformat is None:
            self.system = self._determine_coordinatesystem()
        elif locformat not in [item for item in CoordinateSystem]:
            self.system = self._determine_coordinatesystem()
        else:
            self.system = locformat

        if self.system == -1:
            raise ValueError("No valid coordinate system could be determined from the coordinates given..")
        if self._out_of_bounds():
            raise ValueError("Invalid coordinates for type were used")

    def _determine_coordinatesystem(self):
        # Checks for each known system whether the coordinates are within a unique range for that system
        # Upon success, it sets the found system
        if (7000 <= self.x <= 300000) and (289000 <= self.y <= 629000):
            return CoordinateSystem.rd
        if (-180 <= self.x <= 180) and (-90 <= self.y <= 90):
            return CoordinateSystem.wgs84

        return -1

    def _out_of_bounds(self):
        # Checks for the set system whether the coordinates are within bound.
        if self.system == CoordinateSystem.wgs84 and (-180 <= self.x <= 180) and (-90 <= self.y <= 90):
            return False
        if (
            self.system == CoordinateSystem.rd
            and (7000 <= self.x <= 300000)
            and (289000 <= self.y <= 629000)
            and (self.x < self.y)
        ):
            return False
        return True

    def get_RD(self):
        # If the system isn't the same as called, return the proper conversion result.
        # Otherwise, return the original values
        if self.system == CoordinateSystem.wgs84:
            return self._wgs84_to_rd()
        return self.x, self.y

    def get_WGS84(self):
        # If the system isn't the same as called, return the proper conversion result.
        # Otherwise, return the original values

        if self.system == CoordinateSystem.rd:
            return self._rd_to_wgs84()
        return self.x, self.y

    def get_original(self):
        return self.x, self.y

    def _wgs84_to_rd(self):
        # Convert WGS84 to RD, using function 7 in combination with the R and S conversion sets.
        dPhi = 0.36 * (self.x - self.PHI0)
        dLambda = 0.36 * (self.y - self.LAMBDA0)
        x = 0
        y = 0

        for row in self.R:
            x = x + row[2] * math.pow(dPhi, row[0]) * math.pow(dLambda, row[1])
        for row in self.S:
            y = y + row[2] * math.pow(dPhi, row[0]) * math.pow(dLambda, row[1])

        x = self.X0 + round(x, 0)
        y = self.Y0 + round(y, 0)

        return x, y

    def _rd_to_wgs84(self):
        # Convert RD to WGS84, using function 6 in combination with the K and L conversion sets.
        dX = (self.x - self.X0) * 0.00001
        dY = (self.y - self.Y0) * 0.00001
        phi = 0.0
        _lambda = 0.0

        for row in self.K:
            phi = phi + row[2] * math.pow(dX, row[0]) * math.pow(dY, row[1])
        for row in self.L:
            _lambda = _lambda + row[2] * math.pow(dX, row[0]) * math.pow(dY, row[1])

        phi = self.PHI0 + (phi / 3600)
        _lambda = self.LAMBDA0 + (_lambda / 3600)

        return phi, _lambda
