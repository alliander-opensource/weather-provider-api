# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from typing import Any

from fastapi import HTTPException


class UnknownSourceException(HTTPException):  # pragma: no cover
    """An unknown Source Exception type."""

    def __init__(self, detail: Any = None):
        """Initialize an exception for an unknown weather source.

        Args:
            detail (Any | None): Custom error detail, or the default source error message.
        """
        self.detail = detail or "unknown data source id"
        self.status_code = 404


class UnknownModelException(HTTPException):  # pragma: no cover
    """An unknown Model Exception type."""

    def __init__(self, detail: Any = None):
        """Initialize an exception for an unknown weather model.

        Args:
            detail (Any | None): Custom error detail, or the default model error message.
        """
        self.detail = detail or "unknown model id"
        self.status_code = 404
