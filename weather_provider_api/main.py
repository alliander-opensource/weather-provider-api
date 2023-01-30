#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0


"""Main API executable
This module contains everything required to boot the Weather Provider API.
Its '__main__' if-clause handles running it directly from a directory or IDE setting.

"""
from datetime import datetime

import structlog
import uvicorn
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.responses import RedirectResponse

from weather_provider_api.app_config import get_setting
from weather_provider_api.core.initializers.error_handling import \
    initialize_error_handling
from weather_provider_api.core.initializers.headers import \
    initialize_metadata_header_middleware
from weather_provider_api.core.initializers.logging import initialize_logging
from weather_provider_api.core.initializers.monitoring import \
    initialize_prometheus_middleware
from weather_provider_api.core.initializers.mounting import mount_api_version
from weather_provider_api.core.initializers.rate_limiter import API_RATE_LIMITER
from weather_provider_api.core.initializers.validation import \
    initialize_validation_middleware
from weather_provider_api.versions.v1 import app as v1
from weather_provider_api.versions.v2 import app as v2

app = FastAPI(version=get_setting("APP_VERSION"), title=get_setting("APP_NAME"))

# Add rate limiter
app.state.limiter = API_RATE_LIMITER
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Enable logging
initialize_logging()
logger = structlog.get_logger(__name__)
logger.info('--------------------------------------', datetime=datetime.utcnow())
logger.info('Booting Weather Provider API Systems..', datetime=datetime.utcnow())
logger.info('--------------------------------------', datetime=datetime.utcnow())

# Create and configure new application instance
initialize_error_handling(app)
initialize_metadata_header_middleware(app)
initialize_validation_middleware(app)
initialize_prometheus_middleware(app)

# Activate enabled API versions
mount_api_version(app, v1)
mount_api_version(app, v2)


# Redirect users to the docs
@app.get("/")
def redirect_to_docs():
    redirect_url = "/api/v2/docs"  # replace with docs URL or use weather_provider_api.url_path_for()
    return RedirectResponse(url=redirect_url)


logger.info(f'--------------------------------------', datetime=datetime.utcnow())
logger.info(f'Finished booting; starting uvicorn...', datetime=datetime.utcnow())
logger.info(f'--------------------------------------', datetime=datetime.utcnow())


def main():
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()
