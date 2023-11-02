#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import datetime, timedelta
from typing import Optional, Union

import numpy as np
import pandas as pd
from fastapi import HTTPException
from loguru import logger


def parse_datetime(
    datetime_string,
    round_missing_time_up=False,
    round_to_days=False,
    raise_errors=False,
    loc=None,
) -> Optional[datetime]:
    if datetime_string is None:
        return None

    dt = pd.to_datetime(datetime_string, dayfirst=False, errors="coerce")

    if pd.isnull(dt):
        logger.exception("Error while parsing datetime string", input=datetime_string)
        if raise_errors:
            # Note: replace when FastAPI supports Pydantic models to define query parameters
            # (meaning Validators can be used)
            error_msg = {
                "loc": loc,
                "msg": "invalid datetime format",
                "type": "type_error.datetime",
            }
            raise HTTPException(status_code=422, detail=[error_msg])

        dt = None

    if dt is not None and (round_missing_time_up or round_to_days) and time_unknown(dt, datetime_string):
        if round_to_days:
            dt = dt + timedelta(days=1)
        else:
            dt = dt.replace(hour=23, minute=59, second=59)

    if dt is not None:
        dt = np.datetime64(dt).astype(datetime)

    return dt


def time_unknown(dt: datetime, datetime_string: str):  # pragma: no cover
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and ":" not in datetime_string:
        return True
    return False


def validate_begin_and_end(
    start: datetime, end: datetime, data_start: Union[datetime, None] = None, data_end: Union[datetime, None] = None
):
    """
    Checks the given date parameters and replaces them with default values if they aren't valid.
    The resulting values are then returned.
    """
    if data_end is None:
        # Assuming predictions fill in this value, the most recent value for the past is before "now".
        data_end = datetime.utcnow()

    if data_start is not None and data_start > start:
        # If the starting moment lies before what can be requested, put it at the moment from which it can be requested
        start = data_start

    if data_end is not None and data_end < end:
        end = data_end

    if start >= data_end:
        raise HTTPException(
            422, f"Invalid [start] value [{start}]: value lies after last available moment for model ({data_end})"
        )
    if data_start is not None and end <= data_start:
        raise HTTPException(
            422, f"Invalid [end] value [{end}]: value lies before first available moment for model ({data_start})"
        )

    if end < start:
        raise HTTPException(422, f"Invalid [start] and [end] values: [end]({end}) lies before [start]({start})")

    return start, end
