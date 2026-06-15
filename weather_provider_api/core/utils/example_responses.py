#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import Any


def prepare_example_response(example_response: dict[str, Any] | list[dict[str, Any]], content_type: str = "application/json") -> dict[str, Any]:
    """Translates a simple example response into a FastAPI response dictionary.

     This method is used to translate simple output example lists and dictionaries into FastAPI response dictionaries
     fit for use within the OpenAPI specifications and Swagger UI. It takes an example response object (either a list
     or dict of items) and a content type string, and returns a FastAPI response dictionary that can be used in the
     OpenAPI specifications (and Swagger UI) to provide example responses for API endpoints.

    Args:
        example_response (dict | list): An example response object (either a list or dict of items)
        content_type:                   A string holding the output content type.

    Returns:
        A FastAPI response dictionary fit for the OpenAPI specifications (and Swagger UI)

    """
    return {"content": {content_type: {"example": example_response}}}
