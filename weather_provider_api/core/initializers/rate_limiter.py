# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Request Rate Limiter initializer."""

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import Response

API_RATE_LIMITER = Limiter(key_func=get_remote_address, default_limits=["5/minute"])


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Return SlowAPI's standard response for a rate-limit exception."""
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    return _rate_limit_exceeded_handler(request, exc)


def initialize_rate_limiter(application: FastAPI) -> None:
    """Attach SlowAPI's default and route-specific limits to an application."""
    application.state.limiter = API_RATE_LIMITER
    application.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)


async def enforce_default_rate_limit(request: Request) -> None:
    """Apply default limits when FastAPI's included-router wrappers hide route handlers from SlowAPI."""
    endpoint = request.scope.get("endpoint")
    endpoint_name = f"{endpoint.__module__}.{endpoint.__name__}" if endpoint is not None else ""
    if endpoint_name not in API_RATE_LIMITER._route_limits:
        API_RATE_LIMITER._check_request_limit(request, endpoint, in_middleware=True)
