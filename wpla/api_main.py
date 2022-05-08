#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Main file for running the full API.

This module can be used in two ways:
 - as an easy way to get started by running the API for you
 - or as an example to use when building your own distribution of the API

In essence we do the following:
 1. we setup the FastAPI app itself
 2. We hookup the logging, both inside the app, and outside of it to capture everything.
 3. We add the middleware we want. (Error handling, metadata addition, version validation, Prometheus..)
 4. We hook up any components as their own apps, with their own routers.
 5. We set any redirects
 6. And finally, we start the app using uvicorn, gunicorn, etcetera.

Todo:
    * Give more information on running under uvicorn, gunicorn and one or two other methods.
"""

import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from wpla.api.core.initializers.exception_handling import initialize_error_handling
from wpla.api.core.initializers.headers import initialize_metadata_header_middleware
from wpla.api.core.initializers.logging import initialize_logging
from wpla.api.core.initializers.monitoring import initialize_prometheus_middleware
from wpla.api.core.initializers.mounting import mount_api_version
from wpla.api.core.initializers.validation import initialize_validation_middleware

from wpla.configuration import app_config

from wpla.api.versions.core import app as core_view
from wpla.api.versions.v2 import app as v2
from wpla.api.versions.v3 import app as v3

# Set up the app
wpla_app = FastAPI(
    version=app_config.version,
    title=app_config.name,
    description=app_config.description,
)
wpla_app.add_event_handler("startup", initialize_logging)
initialize_logging()

# Add the middleware
initialize_error_handling(wpla_app)
initialize_metadata_header_middleware(wpla_app)
initialize_validation_middleware(wpla_app)
initialize_prometheus_middleware(wpla_app)  # Optional

# Add the endpoints
mount_api_version(wpla_app, core_view)
mount_api_version(wpla_app, v2)
mount_api_version(wpla_app, v3)


# Add Redirects
@wpla_app.get("/")
def redirect_to_docs():
    """Redirect the visitors from the root location to the default version's 'docs' for its Swagger UI"""
    return RedirectResponse(url="/api/v3/docs")


if __name__ == "__main__":
    # And finally, if run directly, use uvicorn to start the app
    uvicorn.run(wpla_app, host="127.0.0.1", port=8080)
