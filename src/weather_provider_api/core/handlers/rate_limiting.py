#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from weather_provider_api.configuration import API_CONFIGURATION

DEFAULT_RATE_LIMITER = f"{API_CONFIGURATION.component_settings.rate_limiter.get('max_requests')}/minute"
HEAVY_LOAD_RATE_LIMITER = f"{API_CONFIGURATION.component_settings.rate_limiter.get('max_requests_heavy_load')}/minute"
MINIMAL_LOAD_RATE_LIMITER = (
    f"{API_CONFIGURATION.component_settings.rate_limiter.get('max_requests_minimal_load')}/minute"
)


def attach_rate_limiter(application: FastAPI):
    """Attach the rate limiter middleware to the FastAPI application."""
    application.state.limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_RATE_LIMITER])

    # noinspection PyTypeChecker
    application.add_middleware(SlowAPIMiddleware)
    # noinspection PyTypeChecker
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logging.debug("Rate limiter middleware successfully added to the application")


custom_rate_limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_RATE_LIMITER])
