#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""Core endpoints."""
from typing import Dict

from fastapi import APIRouter

from wpla.configuration import app_config

app = APIRouter()


@app.get("/ping")
def get_api_alive() -> Dict:
    """Returns a JSON object. Can be used to check if the API is running.
    Returns:     JSON object
    """
    return {"api_running": True}


@app.get("/status")
def get_api_status() -> Dict:
    """Returns an API health check.
    Includes: API expiry and unit testing
    """
    # TODO: implement API status
    return {"api_status": "API status check not implemented"}


@app.get("/version")
def get_app_version() -> Dict:
    """Returns app version."""
    return {"app_version": app_config.version}


@app.get("/info")
def get_app_information() -> Dict:
    """Returns app information."""
    return {
        "app_name": app_config.name,
        "app_description": app_config.description,
        "app_version": app_config.version,
        "app_maintainer": app_config.maintainer,
        "app_maintainer_email": app_config.maintainer_email,
    }
