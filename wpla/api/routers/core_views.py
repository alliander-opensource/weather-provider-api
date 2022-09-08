#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
=========================
Core API Endpoints Module
=========================

This module holds the core API interface elements. This includes base API self testing options.

"""
from typing import Dict

from fastapi import APIRouter
from starlette.responses import JSONResponse

from wpla.configuration import app_config

app = APIRouter()


@app.get("/ping")
def get_api_alive() -> JSONResponse:
    """ The core API self test.

    Very easy implementation. If the API is not alive, it can't return anything and will therefor fail this test.

    Returns:
        A JSONResponse object holding the running information and status code 200

    """
    body = {"api_running": True}
    return JSONResponse(body, headers=None, status_code=200)


@app.get("/status")
def get_api_status() -> JSONResponse:
    """ Returns the results of an API status check """
    # TODO: Implement an API status check
    #       This needs to check basic installation properties like attached models and source, as well as determine
    #        any connectivity issues with dataset sources
    body = {"api_status": "API status check not yet implemented"}
    return JSONResponse(body, headers=None, status_code=200)


@app.get("/version")
def get_app_version() -> JSONResponse:
    """ Returns the current application version. """
    body = {"app_version": app_config.version}
    return JSONResponse(body, headers=None, status_code=200)


@app.get("/info")
def get_app_information() -> JSONResponse:
    """ Returns basis application information. """
    body = {
        "app_name": app_config.name,
        "app_description": app_config.description,
        "app_version": app_config.version,
        "app_maintainer": app_config.maintainer,
        "app_maintainer_email": app_config.maintainer_email,
    }
    return JSONResponse(body, headers=None, status_code=200)
