#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import APIRouter

"""
======================================
The WPLA API v2.x app interface module
======================================

This module holds all of the interface hooks for the v2.x version of the WPLA API. Any and all intended functionality 
for this API version should be connected to the router in this module.
"""

app = APIRouter()


@app.get("/test_v2", tags=['test'])
async def dummy_endpoint():
    return "Version 2 - Dummy Endpoint"
