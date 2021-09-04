#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def get_api_status():
    """
        'api_status': {
            'api_v2_running': True/False,
            'api_v3_running': True/False,
            'source_knmi_no_issues': True/False,  # Validate source function that returns True if all models pass 
            'source_cds_no_issues': True/False,   # their tests and outside connections to the source could be made
        }
    """
    # TODO: PRIORITY_3 -- implement API status check

    api_status_dict = {"api_status": "API status check not implemented"}
    return api_status_dict


@router.get("/ping")
def get_api_alive():
    """Returns a JSON object. Can be used to check if the API is running.

    Returns:
        JSON object
    """
    return {"api_running": True}
