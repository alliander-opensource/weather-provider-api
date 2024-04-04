#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import uvicorn

from weather_provider_api.core.handlers.configuration_handler import WP_API_ENV_VARS
from weather_provider_api.core.handlers.logging_handler import initialize_logging
from weather_provider_api.core.wpa_application import get_wpa_application

# The main function for easy local execution
if __name__ == "__main__":
    initialize_logging()
    # Establish easyrun configuration
    port = int(WP_API_ENV_VARS.get("PORT", "8080"))
    host = WP_API_ENV_VARS.get("HOST", "127.0.0.1")
    run_mode = WP_API_ENV_VARS.get("RUN_MODE", "gunicorn").lower()

    # Get the application
    app = get_wpa_application()

    # Run the application based on the parameters
    if run_mode == "uvicorn":
        uvicorn.run(app, host=host, port=port)
    elif run_mode == "gunicorn":
        from weather_provider_api.core.gunicorn_application import GunicornApplication
        GunicornApplication(fastapi_application=app, options={"bind": f"{host}:{port}"}).run()
    else:
        raise ValueError(f"WP API - Invalid run-mode selected: {run_mode}")

