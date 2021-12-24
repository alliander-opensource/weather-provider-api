#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import structlog
from starlette_prometheus import PrometheusMiddleware, metrics

from wpla.configuration import Config

"""Prometheus Monitoring

This module sets up a '/metrics' endpoint for Prometheus monitoring.

TODO: Further build out Prometheus monitoring 
"""


logger = structlog.get_logger(__name__)


def initialize_prometheus_middleware(app, endpoint='/metrics'):
    if Config['deployed']:
        logger.info(f'Enabling a Prometheus endpoint on "{endpoint}".')
        app.add_middleware(PrometheusMiddleware)
        app.add_route(endpoint, metrics)
