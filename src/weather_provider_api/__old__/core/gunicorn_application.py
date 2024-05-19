#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from gunicorn.app.base import Application
from loguru import logger


class GunicornApplication (Application):
    """Gunicorn application class."""

    def __init__(self, fastapi_application: FastAPI, options: dict):
        """Initialize the Gunicorn application."""
        super().__init__()
        self.usage = None
        self.callable = None
        self.options = options
        self.do_load_config()
        self.fastapi_application = fastapi_application
        logger.info("WP API - Gunicorn application initialized successfully...")

    def init(self, *args):
        """Initialize the Gunicorn application."""
        config = {}
        for key, value in self.options.items():
            if key.lower() in self.cfg.settings and value is not None:
                config[key.lower()] = value
        return config

    def load(self):
        """Load the Gunicorn application."""
        return self.fastapi_application
