#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
======================================
The WPLA API v2.x app interface module
======================================
This module holds all of the interface hooks for the v2.x version of the WPLA API. Any and all intended functionality
for this API version should be connected to the router in this module.
"""

from fastapi import APIRouter

from wpla.libraries.controller import MeteoController


app = APIRouter()
controller = MeteoController()


@app.get("/sources", tags=["common"])
async def get_sources():
    """endpoint to request sources"""
    return "fake_sources"


@app.get("/sources/{source_id}", tags=["common"])
async def get_source(source_id: str):
    """endpoint to request specific source data"""
    return f"fake_source: {source_id.lower()}"


@app.get("/sources/{source_id}/models", tags=["common", "synchronous"])
async def get_sync_models(source_id: str):
    """endpoint to request models from a source"""
    return f"fake_models: {source_id.lower()}-models"


@app.get("/sources/{source_id}/models", tags=["common", "a-synchronous"])
async def get_sync_model(source_id: str):
    """endpoint to request a specific model from a source"""
    return f"fake_model: {source_id.lower()}-model"


@app.get("/sources/{source_id}/models/{model_id}", tags=["synchronous"])
async def get_synchronous_meteo_data(stuff: str):
    """endpoint to request meteorological data from a specific model"""
    return f"fake_meteo_data: {stuff}-data"
