# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# Tests for the small models and exception in weather_provider_api.core.exceptions.

from fastapi import HTTPException

from weather_provider_api.core.exceptions.additional_responses import ERROR_RESPONSE
from weather_provider_api.core.exceptions.api_models import ErrorResponseModel
from weather_provider_api.core.exceptions.exceptions import (
    APIExpiredException,
    ExceptionResponseModel,
)


def test_error_response_model_holds_detail():
    """ErrorResponseModel should carry the detail message it is given."""
    assert ErrorResponseModel(detail="something went wrong").detail == "something went wrong"


def test_exception_response_model_holds_detail():
    """ExceptionResponseModel should carry the detail message it is given."""
    assert ExceptionResponseModel(detail="failure").detail == "failure"


def test_error_response_mapping_points_to_error_model():
    """The shared ERROR_RESPONSE mapping should reference the ErrorResponseModel."""
    assert {"model": ErrorResponseModel} == ERROR_RESPONSE


def test_api_expired_exception_is_http_exception():
    """APIExpiredException should be an HTTPException subclass instance."""
    assert isinstance(APIExpiredException(), HTTPException)


def test_api_expired_exception_uses_default_detail():
    """Without a detail, a default expiry message and a 404 status code should be set."""
    exc = APIExpiredException()

    assert exc.status_code == 404
    assert "expiry date" in exc.detail
    assert "maintainer" in exc.detail


def test_api_expired_exception_uses_custom_detail():
    """A provided detail should override the default message while keeping the 404 status."""
    exc = APIExpiredException("This specific interface expired.")

    assert exc.status_code == 404
    assert exc.detail == "This specific interface expired."


def test_api_expired_exception_falsy_detail_falls_back_to_default():
    """A falsy detail (like an empty string) should still fall back to the default message."""
    exc = APIExpiredException("")

    assert exc.detail.startswith("This API has passed")
