#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging

from fastapi import FastAPI
from starlette_prometheus import PrometheusMiddleware, metrics

from weather_provider_api.configuration import API_CONFIGURATION


def attach_prometheus_handler(app: FastAPI):
    """Attach a Prometheus monitoring system handler to the FastAPI application."""
    metrics_endpoint = API_CONFIGURATION.component_settings.prometheus_endpoint

    # noinspection PyTypeChecker
    app.add_middleware(middleware_class=PrometheusMiddleware, filter_unhandled_paths=True)
    app.add_route(metrics_endpoint, metrics)

    logging.debug(f"Connected Prometheus middleware and set up a metrics endpoint at: [{metrics_endpoint}]")
