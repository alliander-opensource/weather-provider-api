#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from slowapi import Limiter
from slowapi.util import get_remote_address

from weather_provider_api.configuration import API_CONFIGURATION

DEFAULT_RATE_LIMITER = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{API_CONFIGURATION.component_settings.rate_limiter.get('max_requests')}/minute"],
)
HEAVY_LOAD_RATE_LIMITER = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{API_CONFIGURATION.component_settings.rate_limiter.get('max_requests_heavy_load')}/minute"],
)
MINIMAL_LOAD_RATE_LIMITER = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{API_CONFIGURATION.component_settings.rate_limiter.get('max_requests_minimal_load')}/minute"],
)
