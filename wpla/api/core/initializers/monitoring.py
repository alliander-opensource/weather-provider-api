#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Prometheus Monitoring

This module initializes the Prometheus middleware component.

"""

from fastapi import FastAPI
from loguru import logger

from starlette_prometheus import PrometheusMiddleware, metrics
from wpla.configuration import app_config


def initialize_prometheus_middleware(app: FastAPI, endpoint: str = "/metrics"):
    """Starts the HTTP endpoint for Prometheus monitoring.

    Args:
        app:        FastAPI app instance
        endpoint:   URL at which the metrics should be available
    """
    if app_config.deployed:
        app.add_middleware(PrometheusMiddleware)
        app.add_route(endpoint, metrics)
        logger.info(f"Initialised a Prometheus endpoint on: {endpoint}")
