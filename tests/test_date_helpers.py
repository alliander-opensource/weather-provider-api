# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, date, datetime

import numpy as np
import pytest
from starlette.exceptions import HTTPException

import weather_provider_api.routers.weather.utils.date_helpers as dh

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
@pytest.mark.parametrize(
    "test_datetime,test_round_time,test_round_days,test_raise_errors,test_loc,test_result",
    [
        ("2019-01-01 00:00", False, False, False, None, datetime(2019, 1, 1, 0, 0)),
        ("2019-01-01 23:59", True, True, False, None, datetime(2019, 1, 1, 23, 59)),
        ("2019-01-01", True, False, False, None, datetime(2019, 1, 1, 23, 59, 59)),
        ("2019-01-01", False, True, False, None, datetime(2019, 1, 2, 0, 0)),
        ("2019-01-01", True, True, False, None, datetime(2019, 1, 2, 0, 0)),
    ],
)
def test_parse_datetime(
    test_datetime: str,
    test_round_time: bool,
    test_round_days: bool,
    test_raise_errors: bool,
    test_loc: list[str] | None,
    test_result: datetime,
):
    """Test the parse_datetime function for various datetime string formats and rounding options."""
    assert (
        dh.parse_datetime(
            datetime_string=test_datetime,
            round_missing_time_up=test_round_time,
            round_to_days=test_round_days,
            raise_errors=test_raise_errors,
            loc=test_loc,
        )
        == test_result
    )


def test_parse_datetime_error_handling():
    """Test the error handling of the parse_datetime function for invalid datetime strings."""
    with pytest.raises(HTTPException) as e:
        dh.parse_datetime(
            datetime_string="2019-01-0Z",
            round_missing_time_up=False,
            round_to_days=False,
            raise_errors=True,
            loc=["Oh no"],
        )
    assert e.value.status_code == 422
    assert e.value.detail == "{'loc': ['Oh no'], 'msg': 'invalid datetime format', 'type': 'type_error.datetime'}"

    assert (
        dh.parse_datetime(
            datetime_string="2019-01-0Z",
            round_missing_time_up=False,
            round_to_days=False,
            raise_errors=False,
            loc=["Oh no"],
        )
        is None
    )


def test_parse_datetime_preserves_timezone_offset() -> None:
    """Preserve timezone information so validation can normalize the actual instant to UTC."""
    result = dh.parse_datetime("2026-10-04T06:00:00+02:00")

    assert result == datetime.fromisoformat("2026-10-04T06:00:00+02:00")


def test_validate_begin_and_end_treats_naive_datetimes_as_utc() -> None:
    """Interpret timezone-naive request times consistently as UTC, independent of host timezone."""
    start, end = dh.validate_begin_and_end(
        datetime(2026, 10, 4, 6),
        datetime(2026, 10, 4, 7),
        date(2026, 10, 1),
        date(2026, 10, 10),
    )

    assert start == datetime(2026, 10, 4, 6, tzinfo=UTC)
    assert end == datetime(2026, 10, 4, 7, tzinfo=UTC)


def test_datetime_to_numpy_datetime64_converts_offset_to_utc() -> None:
    """Return a timezone-naive NumPy datetime representing the same UTC instant."""
    result = dh.datetime_to_numpy_datetime64(datetime.fromisoformat("2026-10-04T06:00:00+02:00"))

    assert result == np.datetime64("2026-10-04T04:00:00")

    assert (
        dh.parse_datetime(
            datetime_string=None,
            round_missing_time_up=False,
            round_to_days=False,
            raise_errors=False,
            loc=["Oh no"],
        )
        is None
    )
