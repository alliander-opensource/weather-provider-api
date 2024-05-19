#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging

from fastapi import FastAPI

from weather_provider_api.core.assemble_application import assemble_application_from_configuration
from weather_provider_api.core.handlers.logging import setup_included_project_logger


def __build_app() -> FastAPI:
    setup_included_project_logger()  # Initial logger interception

    application = assemble_application_from_configuration()
    logging.info(
        f"Application successfully assembled from configuration settings: "
        f"[{getattr(application, 'title', 'Weather Provider API')} "
        f"({getattr(application, 'version', '<version unknown>')})"
    )
    return application


app = __build_app()
