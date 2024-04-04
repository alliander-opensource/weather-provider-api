#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/liveliness")
def liveliness():
    """The liveliness endpoint for the API."""
    return {"status": "ok"}


@health_router.get("/readiness")
def readiness():
    """The readiness endpoint for the API."""
    # TODO: Implement
    # 1. Check access to storage
    # 2. Check access to external services
    # 3. Check validity of sources, models and storage
    return {"status": "ok"}
