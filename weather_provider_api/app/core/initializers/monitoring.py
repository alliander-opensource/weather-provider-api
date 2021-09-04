#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import structlog
from starlette_prometheus import metrics, PrometheusMiddleware

from weather_provider_api.app.core.config import Config

logger = structlog.get_logger(__name__)


def initialize_prometheus_middleware(app, endpoint="/metrics"):
    """ This function initializes the HTTP endpoint for Prometheus monitoring

    Args:
        app:        The FastAPI app instance to bind Prometheus to
        endpoint:   The endpoint location where to make the metrics available
    """
    if Config["deployed"]:
        logger.info(f'Enabling Prometheus endpoint on: "{endpoint}"')
        app.add_middleware(PrometheusMiddleware)
        app.add_route(endpoint, metrics)
