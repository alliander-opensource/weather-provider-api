#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Main executable module """

import uvicorn
from loguru import logger

from weather_provider_api.core.initializers.logging_handler import initialize_logging

# Logging is initialized before the importing of APP_CONFIG, to ensure custom logging for APP_CONFIG initialisation.
initialize_logging()

# Import application configuration settings
from weather_provider_api.config import APP_CONFIG


def launch_api(run_mode: str = "uvicorn", host: str = "127.0.0.1", port: int = 8080):
    """The main method for running this application directly.

    (The Dockerfile uses the WPLA_APPLICATION object in [vbd_memo_api.core.application].)

    Args:
        run_mode (str): The run mode for the application. Accepted values are 'uvicorn' and 'gunicorn'.
        host (str):     The host id to run this application on. Usually 'localhost', '127.0.0.1' or '0.0.0.0' in this
                         context.
        port (str):     The port to broadcast the application at.

    Returns:
        Nothing. Either runs successfully until stopped, or breaks from an Exception.

    Notes:
        As Gunicorn only works within the Linux OS, the 'gunicorn' run_mode setting will not work from any other OS.

    """
    project_title = (
        APP_CONFIG["base"]["full_title"] if APP_CONFIG["base"]["full_title"] else APP_CONFIG["base"]["title"]
    )
    launch_string = f"Launching: {project_title}..."
    logger.info("-" * len(launch_string))
    logger.info(launch_string)
    logger.info("-" * len(launch_string))

    from weather_provider_api.core.application import WPLA_APPLICATION

    # start application based on parameters
    if run_mode.upper() == "UVICORN":
        uvicorn.run(WPLA_APPLICATION, host=host, port=port)
    elif run_mode.upper() == "GUNICORN":
        # Error handling for problems with the Gunicorn application get handled by Gunicorn itself.
        from weather_provider_api.core.gunicorn_application import GunicornApplication

        gunicorn_app = GunicornApplication(options={"bind": f"{host}:{port}"}, fastapi_application=WPLA_APPLICATION)
        gunicorn_app.run()
    else:
        raise ValueError(f"Invalid run-mode selected: {run_mode}")

    shutting_down_string = f"Shutting down: {project_title}"
    logger.info("-" * len(shutting_down_string))
    logger.info(shutting_down_string)
    logger.info("-" * len(shutting_down_string))


# The main function for easy local execution
if __name__ == "__main__":
    # If run from main start using the defaults
    launch_api()
