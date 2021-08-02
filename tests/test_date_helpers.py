#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

from datetime import datetime

import pytest
from fastapi import HTTPException

import app.routers.weather.utils.date_helpers as dh


# The function time_unknown() isn't tested as it only verifies that no time may have been set in the datetime conversion
# and that the datetime string didn't contain a colon.

# The parse_datetime() function converts a string to a datetime, returning the exact date and time passed as a string.
# If no time was given, however:
# - It should return 00:00 if neither time or date were rounded up
# - It should return 23:59:59 for the given day if the time is rounded up
# - It should return 00:00 for the next day if the date is rounded up
#   (if both were rounded up, only the day roundup is used)
# Also, if an invalid string is passed, the result should be:
# - None, if the raise_errors parameter was False
# - A FastAPI HTTPException (status code 422), also containing any given value for loc,
#   if the raise_errors parameter was True
# If no value was given at all, None should be returned
@pytest.mark.parametrize("test_datetime,test_round_time,test_round_days,test_raise_errors,test_loc,test_result", [
    ("2019-01-01 00:00", False, False, False, None, datetime(2019, 1, 1, 0, 0)),
    ("2019-01-01 23:59", True, True, False, None, datetime(2019, 1, 1, 23, 59)),
    ("2019-01-01", True, False, False, None, datetime(2019, 1, 1, 23, 59, 59)),
    ("2019-01-01", False, True, False, None, datetime(2019, 1, 2, 0, 0)),
    ("2019-01-01", True, True, False, None, datetime(2019, 1, 2, 0, 0)),
])
def test_parse_datetime(test_datetime, test_round_time, test_round_days, test_raise_errors, test_loc, test_result):
    assert dh.parse_datetime(datetime_string=test_datetime,
                             round_missing_time_up=test_round_time,
                             round_to_days=test_round_days,
                             raise_errors=test_raise_errors,
                             loc=test_loc) == test_result


def test_parse_datetime_error_handling():
    with pytest.raises(HTTPException) as e:
        assert dh.parse_datetime(datetime_string="2019-01-0Z",
                                 round_missing_time_up=False,
                                 round_to_days=False,
                                 raise_errors=True,
                                 loc="Oh no")
    assert e is not None

    assert dh.parse_datetime(datetime_string="2019-01-0Z",
                             round_missing_time_up=False,
                             round_to_days=False,
                             raise_errors=False,
                             loc="Oh no") is None

    assert dh.parse_datetime(datetime_string=None,
                             round_missing_time_up=False,
                             round_to_days=False,
                             raise_errors=False,
                             loc="Oh no") is None

"""
@pytest.mark.parametrize("starting_date, ending_date, result", [
    # VALIDATION TEST 1: Date range lies within scope. Expected results: identical to input
    (datetime(2019, 4, 13), datetime(2019, 4, 18), (datetime(2019, 4, 13), datetime(2019, 4, 18))),
    # VALIDATION TEST 2: Starting time before scope. Expected results: move start to repo start
    (datetime(2019, 3, 1), datetime(2019, 3, 10), (datetime(2019, 3, 3), datetime(2019, 3, 10))),
    # VALIDATION TEST 3: Ending time after scope. Expected results: move end to repo end
    (datetime(2020, 3, 11), datetime(2020, 8, 12), (datetime(2020, 3, 11), datetime(2020, 8, 8))),
    # VALIDATION TEST 4: Range before scope. Expected results: end at 7 days after starting time, start at starting time
    (datetime(2019, 1, 1), datetime(2019, 1, 12), (datetime(2019, 3, 3), datetime(2019, 3, 10))),
    # VALIDATION TEST 5: Range after scope. Expected results: end at ending time, start seven days before that
    (datetime(2021, 1, 1), datetime(2021, 1, 12), (datetime(2020, 8, 1), datetime(2020, 8, 8))),
    # VALIDATION TEST 6: No starting time. Expected results: starting time at 7 days before ending time
    (None, datetime(2019, 4, 18), (datetime(2019, 4, 11), datetime(2019, 4, 18))),
    # VALIDATION TEST 7: No ending time. Expected results: ending time at repo ending time
    (datetime(2019, 4, 13), None, (datetime(2019, 4, 13), datetime(2020, 8, 8))),
    # VALIDATION TEST 8: No times at all. Expected results: ending time at repo ending, starting time 7 days before that
    (None, None, (datetime(2020, 8, 1), datetime(2020, 8, 8))),
])
def test_validate_begin_and_end(starting_date, ending_date, result):
    # Testing assumes a repo starting date of 2019-03-03 and an ending date of 2020-08-08
    assert dh.validate_begin_and_end(starting_date, ending_date, datetime(2019, 3, 3), datetime(2020, 8, 8)) == result
"""  # Temporarily disabled due to fixes for this function