#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

import pytest

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture
def input_value():
    return 5


def test_location_type_detection():
    # Tests to verify proper type detection for regular and extreme coordinate values

    # Test 1: Out of bounds 'coordinate' for both WGS84 and RD, using auto-detection
    with pytest.raises(ValueError) as e:
        assert GeoPosition(52.2, 182)
    assert str(e.value.args[0]) == "No valid coordinate system could be determined from the coordinates given.."

    # Test 2:  Value in bounds as WSG84, but specified as RD and out of bounds for RD.
    with pytest.raises(ValueError) as e:
        assert GeoPosition(52.2, 90, 'RD')
    assert str(e.value.args[0]) == "Invalid coordinates for type were used"

    # Test 3: Value in bounds as RD, but specified as WGS84 and out of bounds for WGS84.
    with pytest.raises(ValueError) as e:
        assert GeoPosition(155000, 463000, 'WGS84')
    assert str(e.value.args[0]) == "Invalid coordinates for type were used"

    # Test 4: Highest possible and lowest possible values for WGS84, autodetect.
    assert GeoPosition(180, 90)
    assert GeoPosition(-180, -90)

    # Test 5: Highest possible and lowest possible values for RD, autodetect.
    assert GeoPosition(7000, 289000)
    assert GeoPosition(300000, 629000)

    # Test 6: Unknown coordinate system is passed for a coordinate. Coordinate resolves (to RD) though.
    assert GeoPosition(155000, 463000, 'MARSHMALLOW').system == "RD", \
        'GeoPosition should determine RD to be the correctformat'

    # Test 7: Unknown coordinate system is passed for a coordinate. Coordinate does not resolve.
    with pytest.raises(ValueError) as e:
        GeoPosition(-1000, -2000, 'MARSHMALLOW')
    assert str(e.value.args[0]) == "No valid coordinate system could be determined from the coordinates given.."


def test_coordinate_live_locations():
    """
    Tests using existing locations in the Netherlands to verify proper conversion between RD and WGS84
    Location positions were verified using reliable online registers containing RD coordinates for streets, matching
    them to their Google WGS84 locations, and using a known reliable tertiary conversion tool to confirm everything.
    """

    # Test 1: "Onze Lieve Vrouwe Toren" - Amersfoort (building and the center point of the RD coordinate system)
    geo_pos = GeoPosition(155000, 463000, "RD")

    assert geo_pos.get_RD() == (155000, 463000), "Error - Value not properly saved as RD-value"
    assert geo_pos.get_WGS84() == (52.15517440, 5.38720621), "Error - WGS84 value not within allowed constraints"

    # Test 2: Wijnbergseweg - Braamt (street on the middle east side of the country)
    geo_pos = GeoPosition(215803, 438150)

    assert geo_pos.get_RD() == (215803, 438150), "Error - Value not properly identified or saved as RD"
    assert geo_pos.get_WGS84() == pytest.approx((51.92849584, 6.27121733), rel=1e-5), \
        "Error - WGS84 value not within allowed constraints"

    # Test 3: Admiralengracht - Amsterdam (street on the middle west side of the country)
    geo_pos = GeoPosition(52.36954423, 4.85667541)

    assert geo_pos.get_RD() == (118868, 486984), "Error - RD value not within allowed constraints"
    assert geo_pos.get_WGS84() == (52.36954423, 4.85667541), "Error - Value not properly identified or saved as WGS84"

    # Test 4: Gasthuisstraat - Dokkum (street on the middle north side of the country)
    geo_pos = GeoPosition(195703, 593452)

    assert geo_pos.get_RD() == (195703, 593452), "Error - Value not properly identified or saved as RD"
    assert geo_pos.get_WGS84() == pytest.approx((53.3259597, 5.9980788), rel=1e-5), \
        "Error - WGS84 value not within allowed constraints"

    # Test 5: Burgemeester de Grauwstraat - Baarle Nassau (street on the middle south side of the country)
    geo_pos = GeoPosition(51.4450399, 4.9284643)

    assert geo_pos.get_RD() == (123108, 384094), "Error - RD value not within allowed constraints"
    assert geo_pos.get_WGS84() == (51.4450399, 4.9284643), "Error - Value not properly identified or saved as WGS84"
