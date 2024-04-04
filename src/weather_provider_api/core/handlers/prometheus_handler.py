#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from loguru import logger
from starlette_prometheus import PrometheusMiddleware, metrics


def install_prometheus_handler(app: FastAPI, mount_path: str = "/metrics"):
    """Install a Prometheus monitoring system handler to the FastAPI application.

    Args:
        app: The FastAPI application to attach the Prometheus Middleware to.
        mount_path: The endpoint at which the Prometheus data should become available.


    """
    logger.info(f"WP API - Installing Prometheus handler and opening metrics endpoint at: [{mount_path}]")

    # noinspection PyTypeChecker
    app.add_middleware(middleware_class=PrometheusMiddleware, filter_unhandled_paths=True)
    app.add_route(mount_path, metrics)
