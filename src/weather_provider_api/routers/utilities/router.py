#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import APIRouter

utilities_router = APIRouter()


@utilities_router.get("/available-datafiles/{source_id}/{model_id}")
def get_available_datafiles(source_id: str, model_id: str):
    """Get the available datafiles for a given source and model."""
    pass
