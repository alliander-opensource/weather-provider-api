#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Prometheus Middleware handler """

from fastapi import FastAPI
from loguru import logger

from starlette_prometheus import PrometheusMiddleware, metrics


def initialize_prometheus_interface(application: FastAPI, metrics_endpoint: str = "/metrics"):
    """The method that attaches the Prometheus Middleware to a FastAPI application.

    Args:
        application:        The FastAPI application to attach the Prometheus Middleware to.
        metrics_endpoint:   The endpoint at which the Prometheus data should become available.
    Returns:
        Nothing. The FastAPI application itself is updated.

    Notes:
        Prometheus is a metrics system that interprets requests and results and processes those into metrics. From a
         Prometheus server this data can be gathered and preprocessed, allowing for more extensive data on request
         and the handling thereof, like information on memory usage or the time taken to process certain types of
         requests.
        Note that the Prometheus server itself also doesn't handle processing that output into views or graphs. To
         visualize Prometheus output, you'd need something like Elastic or Grafana.
    """
    application.add_middleware(PrometheusMiddleware, filter_unhandled_paths=True)
    application.add_route(metrics_endpoint, metrics)
    logger.info(
        "Attached Prometheus Middleware to the application and opened metrics endpoint at " f"[{metrics_endpoint}]..."
    )
