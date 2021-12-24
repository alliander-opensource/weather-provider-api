#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import structlog

import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from wpla.api.core.initializers.error_handling import initialize_error_handling
from wpla.api.core.initializers.headers import initialize_metadata_header_middleware
from wpla.api.core.initializers.logging import initialize_logging
from wpla.api.core.initializers.monitoring import initialize_prometheus_middleware
from wpla.api.core.initializers.validation import initialize_validation_middleware
from wpla.api.core.initializers.version_mounting import mount_api_version
from wpla.api.versions.v2 import app as v2
from wpla.api.versions.v3 import app as v3
from wpla.configuration import Config

"""This is a module for starting the WPLA API application.

Being both a guide to how to mount your own WPLA API components (if so desired), as well as a default option to run the 
API directly without any prior knowledge, this module starts a FastAPI application and loads it with the WPLAs default 
metadata enhancing, error handling and monitoring middleware and boots up the currently active versions of the API. 
"""

# Enable logging:
initialize_logging()
logger = structlog.get_logger(__name__)

# Create and configure new application instance. Just an empty app for now.
app = FastAPI(version=Config['app']['version'], title=Config['app']['name'])

# Hook up the  Error handling, Prometheus monitoring and metadata extra's
initialize_error_handling(app)
initialize_metadata_header_middleware(app)
initialize_validation_middleware(app)
initialize_prometheus_middleware(app)

# Mount the actual API output versions. This is where we hook up the actual functionality of the API:
mount_api_version(app, v2)
mount_api_version(app, v3)


# Finally, we redirect the visitors from the root location to the default version's 'docs' for its Swagger UI
@app.get('/')
def redirect_to_docs():
    return RedirectResponse(url='/api/v3/docs')


# This is purely to allow for running this module directly (locally)
if __name__ == "__main__":
    # noinspection PyTypeChecker
    uvicorn.run(app, host='127.0.0.1', port=8080)
