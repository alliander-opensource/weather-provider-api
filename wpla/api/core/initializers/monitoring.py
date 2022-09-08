#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
================================
Prometheus Monitoring Middleware
================================

This module initializes a Prometheus middleware component that allows Prometheus installations to interact with this
project.

"""

from fastapi import FastAPI
from loguru import logger

from starlette_prometheus import PrometheusMiddleware, metrics
from wpla.configuration import app_config


def initialize_prometheus_middleware(app, endpoint: str = "/metrics"):
    """ This function adds (Starlette) Prometheus middleware to the given app at the given endpoint

    Args:
        app:        The app to add the middleware to
        endpoint:   A string that holds the endpoint location for the app where the middleware should be mounted

    """
    if app_config.deployed:
        app.add_middleware(PrometheusMiddleware)
        app.add_route(endpoint, metrics)
        logger.info(f"Initialised the Prometheus endpoint at: {endpoint}")
