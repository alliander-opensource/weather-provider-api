# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from enum import StrEnum


class OutputUnit(StrEnum):
    """Enumeration of valid output unit sets for weather data."""

    si = "si"
    human = "human"
    original = "original"
