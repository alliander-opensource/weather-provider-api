# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class ExceptionResponseModel(BaseModel):
    """Model for error responses from the API."""

    detail: str


class APIExpiredException(HTTPException):
    """Exception to raise when an API has expired and should not be used anymore."""

    def __init__(self, detail: Any = None):
        """Initialize the exception with a custom or default expiration message.

        Args:
            detail (Any | None): Custom error detail, or the default expiration message.
        """
        self.detail = (
            detail
            or "This API has passed it's expiry date and should be revalidated. Please contact the API maintainer."
        )
        self.status_code = 404
