#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import APIRouter
from starlette.responses import FileResponse

utilities_router = APIRouter()


@utilities_router.get(
    "/available-datafiles/{source_id}/{model_id}",
    tags=["file-management"],
    response_model=list[str],
    name="Get available datafiles",
    description="Get the available datafiles for a given source and model.",
)
def get_available_datafiles(source_id: str, model_id: str):
    """Get the available datafiles for a given source and model."""
    return ["datafile1", "datafile2"]


@utilities_router.get(
    "/available-models/{source_id}/{model_id}/get/{datafile_name}",
    tags=["file-management"],
    name="Get a specific datafile",
    description="Retrieve a specific datafile by name.",
)
def get_specific_datafile(source_id: str, model_id: str, datafile_name: str):
    """Retrieve a specific datafile by name."""
    return FileResponse("datafile1")


@utilities_router.delete(
    "/available-models/{source_id}/{model_id}/delete/{datafile_name}",
    tags=["file-management"],
    name="Delete a specific datafile",
    description="Remove a specific datafile by name.",
)
def delete_specific_datafile(source_id: str, model_id: str, datafile_name: str):
    """Remove a specific datafile by name."""
    return {"message": "Datafile deleted."}


@utilities_router.put("/available-models/{source_id}/{model_id}/update/{datafile_name}")
def update_specific_datafile(source_id: str, model_id: str, datafile_name: str):
    """Update a specific datafile by name."""
    return {"message": "Datafile updated."}
