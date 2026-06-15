#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.core.base_model import BaseModel


class ErrorResponseModel(BaseModel):
    """Model for error responses from the API."""
    detail: str  # error message
