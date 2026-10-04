# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from enum import StrEnum
from typing import Final


class GeoCoordinateSystem(StrEnum):
    """Enum representing different coordinate systems."""

    RD = "RD"
    WGS84 = "WGS84"


Coeff = tuple[int, int, float]


class GeoPosition:
    """Class representing a geographical position.

    This class provides methods to convert between RD (Rijksdriehoeksmeting) and WGS84 coordinate systems.
    """

    # Zero point configuration according to table 3 in the source, based on the center point of the RD coordinate system
    # (phi and lambda, representing the WGS84 offset, shift ever so slightly over the years)

    x_0: Final[float] = 155_000.0
    y_0: Final[float] = 463_000.0
    phi_0: Final[float] = 52.155_174_40
    lambda_0: Final[float] = 5.387_206_21

    # Grid conversion data from tables 4 and 5 in the source
    k: Final[tuple[Coeff, ...]] = (
        (0, 1, 3235.65389),
        (2, 0, -32.58297),
        (0, 2, -0.24750),
        (2, 1, -0.84978),
        (0, 3, -0.06550),
        (2, 2, -0.01709),
        (1, 0, -0.00738),
        (4, 0, 0.00530),
        (2, 3, -0.00039),
        (4, 1, 0.00033),
        (1, 1, -0.00012),
    )
    l: Final[tuple[Coeff, ...]] = (  # noqa: E741
        (1, 0, 5260.52916),
        (1, 1, 105.94684),
        (1, 2, 2.45656),
        (3, 0, -0.81885),
        (1, 3, 0.05594),
        (3, 1, -0.05607),
        (0, 1, 0.01199),
        (3, 2, -0.00256),
        (1, 4, 0.00128),
        (0, 2, 0.00022),
        (2, 0, -0.00022),
        (5, 0, 0.00026),
    )
    r: Final[tuple[Coeff, ...]] = (
        (0, 1, 190094.945),
        (1, 1, -11832.228),
        (2, 1, -114.221),
        (0, 3, -32.391),
        (1, 0, -0.705),
        (3, 1, -2.340),
        (1, 3, -0.608),
        (0, 2, -0.008),
        (2, 3, 0.148),
    )
    s: Final[tuple[Coeff, ...]] = (
        (1, 0, 309056.544),
        (0, 2, 3638.893),
        (2, 0, 73.077),
        (1, 2, -157.984),
        (3, 0, 59.788),
        (0, 1, 0.433),
        (2, 2, -6.439),
        (1, 1, -0.032),
        (0, 4, 0.092),
        (1, 4, -0.054),
    )

    def __init__(
        self, x_coord: float | int, y_coord: float | int, coordinate_system: GeoCoordinateSystem | str | None = None
    ) -> None:
        """Initialize a GeoPosition instance with coordinates and an optional coordinate system format."""
        self.x = x_coord
        self.y = y_coord
        self.system: GeoCoordinateSystem | None = None

        if isinstance(coordinate_system, GeoCoordinateSystem):
            self.system = coordinate_system
        elif isinstance(coordinate_system, str):
            try:
                self.system = GeoCoordinateSystem(coordinate_system)
            except ValueError:
                # Unknown coordinate system, attempting to infer from values
                self.system = self._determine_coordinate_system()
        else:
            # Unknown coordinate system, attempting to infer from values
            self.system = self._determine_coordinate_system()

        if self.system is None:
            raise ValueError("No valid coordinate system could be determined from the coordinates given.")

        if self._out_of_bounds():
            raise ValueError("Invalid coordinates for type were used")

        self._rd_cache: tuple[float, float] | None = None
        self._wgs84_cache: tuple[float, float] | None = None

    @staticmethod
    def _rd_in_bounds(x: float, y: float) -> bool:
        """Check whether coordinates are within the Dutch RD bounds.

        Args:
            x (float): RD x-coordinate.
            y (float): RD y-coordinate.

        Returns:
            bool: Whether the coordinates are valid RD coordinates.
        """
        return 7000 <= x <= 300000 and 289000 <= y <= 629000 and x < y

    @staticmethod
    def _wgs84_in_bounds(x: float, y: float) -> bool:
        """Check whether coordinates are within WGS84 bounds.

        Args:
            x (float): Longitude.
            y (float): Latitude.

        Returns:
            bool: Whether the coordinates are valid WGS84 coordinates.
        """
        return -180 <= x <= 180 and -90 <= y <= 90

    def _determine_coordinate_system(self) -> GeoCoordinateSystem | None:
        """Infer the coordinate system from the coordinate bounds.

        Returns:
            GeoCoordinateSystem | None: Inferred coordinate system, or ``None`` when no system matches.
        """
        if self._rd_in_bounds(self.x, self.y):
            return GeoCoordinateSystem.RD
        if self._wgs84_in_bounds(self.x, self.y):
            return GeoCoordinateSystem.WGS84
        return None

    def _out_of_bounds(self) -> bool:
        """Check whether the coordinates are outside the selected system's valid bounds.

        Returns:
            bool: ``True`` when the coordinates are invalid for the selected system.
        """
        if self.system == GeoCoordinateSystem.WGS84:
            return not self._wgs84_in_bounds(self.x, self.y)
        return not self._rd_in_bounds(self.x, self.y)

    @staticmethod
    def _powers(base: float, max_exp: int) -> list[float]:
        """Calculate powers from zero through a maximum exponent.

        Args:
            base (float): Value to exponentiate.
            max_exp (int): Highest exponent to calculate.

        Returns:
            list[float]: Powers of ``base`` in ascending exponent order.
        """
        powers = [1.0] * (max_exp + 1)
        for i in range(1, max_exp + 1):
            powers[i] = powers[i - 1] * base
        return powers

    @staticmethod
    def _poly_sum(coeffs: tuple[Coeff, ...], x_powers: list[float], y_powers: list[float]) -> float:
        """Evaluate a polynomial using coefficient and power tables.

        Args:
            coeffs (tuple[Coeff, ...]): Polynomial exponent and factor tuples.
            x_powers (list[float]): Powers of the x value.
            y_powers (list[float]): Powers of the y value.

        Returns:
            float: Evaluated polynomial value.
        """
        total = 0.0
        for x_exp, y_exp, factor in coeffs:
            total += factor * x_powers[x_exp] * y_powers[y_exp]
        return total

    def _wgs84_to_rd(self) -> tuple[float, float]:
        """Convert this WGS84 position to RD coordinates.

        Returns:
            tuple[float, float]: Converted RD x and y coordinates.
        """
        d_phi = 0.36 * (self.x - self.phi_0)
        d_lambda = 0.36 * (self.y - self.lambda_0)

        d_phi_p = self._powers(d_phi, 3)
        d_lambda_p = self._powers(d_lambda, 4)

        x_delta = self._poly_sum(self.r, d_phi_p, d_lambda_p)
        y_delta = self._poly_sum(self.s, d_phi_p, d_lambda_p)

        x = self.x_0 + round(x_delta, 0)
        y = self.y_0 + round(y_delta, 0)
        return x, y

    def _rd_to_wgs84(self) -> tuple[float, float]:
        """Convert this RD position to WGS84 coordinates.

        Returns:
            tuple[float, float]: Converted WGS84 latitude and longitude.
        """
        d_x = (self.x - self.x_0) * 0.00001
        d_y = (self.y - self.y_0) * 0.00001

        d_x_p = self._powers(d_x, 5)
        d_y_p = self._powers(d_y, 4)

        phi_arcsec = self._poly_sum(self.k, d_x_p, d_y_p)
        lambda_arcsec = self._poly_sum(self.l, d_x_p, d_y_p)

        phi = self.phi_0 + (phi_arcsec / 3600)
        _lambda = self.lambda_0 + (lambda_arcsec / 3600)
        return phi, _lambda

    @property
    def as_wgs84(self) -> tuple[float, float]:
        """Get the coordinates in the WGS84 coordinate system."""
        if self._wgs84_cache is not None:
            return self._wgs84_cache

        if self.system == GeoCoordinateSystem.RD:
            self._wgs84_cache = result = self._rd_to_wgs84()
        else:
            self._wgs84_cache = result = (self.x, self.y)

        return result

    @property
    def as_rd(self) -> tuple[float, float]:
        """Get the coordinates in the RD coordinate system."""
        if self._rd_cache is not None:
            return self._rd_cache

        if self.system == GeoCoordinateSystem.WGS84:
            self._rd_cache = result = self._wgs84_to_rd()
        else:
            self._rd_cache = result = (self.x, self.y)

        return result

    @property
    def as_original(self) -> tuple[float, float]:
        """Get the original coordinates as they were inputted, without conversion."""
        return self.x, self.y
