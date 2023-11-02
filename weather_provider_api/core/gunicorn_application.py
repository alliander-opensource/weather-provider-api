#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Dict

from fastapi import FastAPI
from gunicorn.app.base import Application
from loguru import logger


class GunicornApplication(Application):
    """Gunicorn Application class.

    This class extends the base Gunicorn application class with the settings and methods needed to directly initialize
     the API application.

    Notes:
          This class can also serve as an example for deploying your own version of this API via Gunicorn.

    """

    def __init__(self, fastapi_application: FastAPI, options: Dict):
        """Overwrite of the base method with the purpose of automatically loading a FastAPI application and deployment
         options passed.

        Args:
            fastapi_application:    The FastAPI application to deploy
            options:                The deployment options to use
        """
        super().__init__()
        self.usage = None
        self.callable = None
        self.options = options
        self.do_load_config()  # Loads the default config and requests extra config settings via the init function
        self.fastapi_application = fastapi_application
        logger.info("Gunicorn application initialized successfully...")

    def init(self, *args):
        """Method overwrite of the base method.

        If effectively loaded upon configuration loading. The returned dictionary holds configuration settings which
         are used to overwrite and/or append self.cfg settings.

        Args:
            *args:  Not actually used.

        Returns:
            (dict): A dictionary holding the configuration settings overwrite or append in self.cfg

        """
        config = {}
        for key, value in self.options.items():
            # Match list to actual settings in self.cfg and add those validated with proper capitalization to the
            #  return value
            if key.lower() in self.cfg.settings and value is not None:
                config[key.lower()] = value

        return config

    def load(self):
        """Overwrite of the base method.

        Used to load the application for use.

        Returns:
            FastAPI:    The FastAPI application to load.

        """
        return self.fastapi_application
