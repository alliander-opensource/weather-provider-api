#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import structlog
from starlette_prometheus import PrometheusMiddleware, metrics

from weather_provider_api.app_config import get_setting

logger = structlog.get_logger(__name__)


def initialize_prometheus_middleware(app, endpoint="/metrics"):
    """Start HTTP endpoint for Prometheus monitoring.

    Args:
        app: FastAPI weather_provider_api instance
        endpoint (str): URL at which the metrics should be available
    """
    if get_setting("DEPLOYED"):
        logger.info(f'Enabling Prometheus endpoint on: "{endpoint}"')
        app.add_middleware(PrometheusMiddleware)
        app.add_route(endpoint, metrics)
