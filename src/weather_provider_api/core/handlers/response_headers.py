#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from weather_provider_api.configuration import API_CONFIGURATION


async def customize_response_headers(request, call_next):
    """Customize response headers to include API information."""
    response = await call_next(request)
    response.headers["X-App-Version"] = API_CONFIGURATION.version
    response.headers["X-App-Name"] = API_CONFIGURATION.api_settings.full_title

    if API_CONFIGURATION.api_settings.expiration_date:
        response.headers["X-App-Valid-Till"] = API_CONFIGURATION.api_settings.expiration_date.strftime("%Y-%m-%d")

    if API_CONFIGURATION.maintainer.add_to_headers:
        response.headers["X-Maintainer"] = API_CONFIGURATION.maintainer.name
        response.headers["X-Maintainer-Email"] = API_CONFIGURATION.maintainer.email

    return response
