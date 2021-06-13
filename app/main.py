#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Main API executable
This module contains everything required to boot the Weather Provider API.
Its '__main__' if-clause handles running it directly from a directory or IDE setting.

"""

import structlog
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from app.core.initializers.error_handling import initialize_error_handling
from app.core.initializers.headers import initialize_metadata_header_middleware
from app.core.initializers.logging import initialize_logging
from app.core.initializers.monitoring import initialize_prometheus_middleware
from app.core.initializers.mounting import mount_api_version
from app.core.initializers.validation import initialize_validation_middleware
from app.versions.v1 import app as v1
from app.versions.v2 import app as v2

# Enable logging
initialize_logging()
logger = structlog.get_logger(__name__)

# Create and configure new application instance
app = FastAPI()
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
    redirect_url = "/api/v2/docs"  # replace with docs URL or use app.url_path_for()
    return RedirectResponse(url=redirect_url)


if __name__ == "__main__":
    # Run the application locally
    uvicorn.run(app, host="127.0.0.1", port=8080)
