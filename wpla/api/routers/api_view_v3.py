#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import APIRouter

"""The WPLA V3.x API Interface

This module holds the full interface for the v3.x version of the WPLA API. If there is functionality that should be 
available to this version of the API, it should be hooked up to the router here.
"""

app = APIRouter()


@app.get("/test_v3", tags=['test'])
async def get_test_result():
    return "I am a ham sandwich"
