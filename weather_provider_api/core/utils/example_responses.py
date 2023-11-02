#!/usr/bin/env python
# -*- coding: utf-8 -*-


def prepare_example_response(example_response, content_type: str = "application/json") -> dict:
    """A method to translate simple output example lists and dictionaries into FastAPI response dictionaries fit for
     use within the OpenAPI specifications and Swagger UI.

    Args:
        example_response (dict | list): An example response object (either a list or dict of items)
        content_type:                   A string holding the output content type.

    Returns:
        A FastAPI response dictionary fit for the OpenAPI specifications (and Swagger UI)

    """
    return {"content": {content_type: {"example": example_response}}}
