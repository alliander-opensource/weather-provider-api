#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI

from weather_provider_api.core.handlers.configuration_handler import WP_API_CONFIG, WP_API_ENV_VARS
from weather_provider_api.core.utils.version_detection import WP_API_APP_VERSION
from weather_provider_api.routing.views.v2_specific.router import v2_router

v2_sub_app = FastAPI(
    version=WP_API_APP_VERSION,
    title=f"{WP_API_CONFIG['base'].get('title', 'Weather Provider API')} - V2",
    root_path="/v2/api",
    servers=[{"url": f"{WP_API_ENV_VARS.get('SERVER', 'http://127.0.0.1:8080')}/v2/api"}],
    description=F"The supporting endpoint interface for {WP_API_CONFIG['base'].get('title', 'Weather Provider API')}",
    contact={"name": WP_API_CONFIG["maintainer"].get("name", "Alliander N.V."),
             "email": WP_API_CONFIG["maintainer"].get("email_address", "weather.provider@alliander.com")},
)

v2_sub_app.include_router(v2_router, prefix="/v2/api/weather")
v2_sub_app.openapi()
