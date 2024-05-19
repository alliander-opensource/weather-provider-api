#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from enum import StrEnum

PLAIN_TEXT = "plain_text"
JSON = "json"


class LogFormats(StrEnum):
    """Log formats for the logger."""

    plain = (
        "<level>[{level: <8}]</level>"
        "<green>[{time:YYYY-MM-DD HH:mm:ss:SSS!UTC} UTC]</green>: "
        "<level>{message}</level>"
    )
    extended = (
        "<level>[{level: <8}]</level>"
        "<green>[{time:YYYY-MM-DD HH:mm:ss:SSS!UTC} UTC]</green>"
        "<yellow>[{name: <64}]</yellow>"
        "<blue><b>[{function: <36}]</b></blue>: "
        "<level>{message}</level>"
    )
    server_plain = "[{level}][UTC {time:YYYY-MM-DD HH:mm:ss:SSS!UTC}]: {message}"
    json = "{message}"
