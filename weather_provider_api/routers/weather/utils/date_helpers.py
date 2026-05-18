#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import UTC, date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger
from starlette.exceptions import HTTPException

_TWO_DIGITS_REGEX = r"\d{2}"

def parse_datetime(
    datetime_string: str | None,
    round_missing_time_up: bool = False,
    round_to_days: bool = False,
    raise_errors: bool = False,
    loc: list[str] | None = None,
) -> datetime | None:
    """Parse a datetime string into a datetime object, with options to round up missing time and raise errors."""
    if datetime_string is None:
        return None

    dt = pd.to_datetime(datetime_string, dayfirst=False, errors="coerce")

    if pd.isnull(dt):
        logger.exception("Error while parsing datetime string", input=datetime_string)
        if raise_errors:
            # Note: replace when FastAPI supports Pydantic models to define query parameters
            # (meaning Validators can be used)
            error_msg: dict[str, Any] = {
                "loc": loc,
                "msg": "invalid datetime format",
                "type": "type_error.datetime",
            }
            raise HTTPException(status_code=422, detail=str(error_msg))

        dt = None

    if dt is not None and (round_missing_time_up or round_to_days) and time_unknown(dt, datetime_string):
        if round_to_days:
            dt = dt + timedelta(days=1)
        else:
            dt = dt.replace(hour=23, minute=59, second=59)

    if dt is not None:
        dt = np.datetime64(dt).astype(datetime)

    return dt


def time_unknown(dt: datetime, datetime_string: str) -> bool:  # pragma: no cover
    """Check if the time part of a datetime is unknown (i.e., not specified in the string)."""
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and ":" not in datetime_string:
        return True
    return False


def validate_begin_and_end(
    start: datetime | None,
    end: datetime | None,
    data_start: date | None = None,
    data_end: date | None = None,
) -> tuple[datetime, datetime]:
    """Check the given date parameters and replace them with default values if they aren't valid."""
    if not start or not end:
        raise HTTPException(status_code=422, detail="Both [start] and [end] parameters must be provided")

    # Normalize to UTC
    start = start.astimezone(UTC)
    end = end.astimezone(UTC)
    data_start = datetime.combine(data_start, datetime.min.time()).astimezone(UTC) if data_start else None
    data_end = datetime.combine(data_end, datetime.max.time()).astimezone(UTC) if data_end else datetime.now(UTC)

    # Clamp start and end to available data range
    if data_start and start < data_start:
        start = data_start
    if end > data_end:
        end = data_end

    # Validation checks
    if start >= data_end:
        raise HTTPException(
            422,
            f"[start] ({start}) is after the last available model time ({data_end})",
        )
    if data_start and end <= data_start:
        raise HTTPException(
            422,
            f"[end] ({end}) is before the first available model time ({data_start})",
        )
    if end < start:
        raise HTTPException(
            422,
            f"[end] ({end}) is before [start] ({start})",
        )

    return start, end


def subtract_months(dt: date, months: int) -> date:
    """Subtract a number of months from a datetime, correctly handling year changes and varying month lengths."""
    year = dt.year
    month = dt.month - months
    while month <= 0:
        month += 12
        year -= 1
    return dt.replace(year=year, month=month, day=1)


def strftime_to_regex(fmt: str) -> str:
    """Convert a strftime format string to a regex pattern."""
    # Regex pattern for two digits
    replacements = {
        "%Y": r"\d{4}",
        "%m": _TWO_DIGITS_REGEX,
        "%d": _TWO_DIGITS_REGEX,
        "%H": _TWO_DIGITS_REGEX,
        "%M": _TWO_DIGITS_REGEX,
        "%S": _TWO_DIGITS_REGEX,
    }
    regex = fmt
    for k, v in replacements.items():
        regex = regex.replace(k, v)
    return regex
