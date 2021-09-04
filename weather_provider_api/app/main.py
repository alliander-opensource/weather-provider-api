#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

""" API Main Executable
This module boots the API as it is configured in the configuration files (or system settings).
"""
import structlog
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from weather_provider_api.app.core.config import Config
from weather_provider_api.app.core.initializers.error_handling import initialize_error_handling
from weather_provider_api.app.core.initializers.headers import initialize_metadata_header_middleware
from weather_provider_api.app.core.initializers.logging import initialize_logging

from weather_provider_api.app.core.initializers.monitoring import initialize_prometheus_middleware
from weather_provider_api.app.core.initializers.mounting import mount_api_version
from weather_provider_api.app.core.initializers.validation import initialize_validation_middleware

# Initialize and start logging
from weather_provider_api.app.versions.v2 import app as v2
from weather_provider_api.app.versions.v3 import app as v3

initialize_logging()
logger = structlog.get_logger(__name__)

# Create and set up the application instance
app = FastAPI(version=Config["app"]["main_version"], title=Config["app"]["name"])

initialize_error_handling(app)
initialize_metadata_header_middleware(app)
initialize_validation_middleware(app)
initialize_prometheus_middleware(app)

# Mount API versions
mount_api_version(app, v2)
mount_api_version(app, v3)


# Redirect users to the proper docs location (v3)
@app.get("/")
def redirect_to_docs():
    redirect_url = "/api/v3/docs"  # Replace with the v3 docs URL or use app.url_path_for()
    return RedirectResponse(url=redirect_url)


# Main execution:
if __name__ == "__main__":
    # Run the application locally
    uvicorn.run(app, host="127.0.0.1", port=8080)
