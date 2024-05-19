#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/liveliness")
def liveliness():
    return {"status": "ok"}


@health_router.get("/readiness")
def readiness():
    # TODO: Implement
    # 1. Check access to storage
    # 2. Check access to external services
    # 3. Check validity of sources, models and storage
    return {
        "Storage functionality": "ok",
        "Access to external sources": "ok",
        "Validity of sources": "ok",
    }
