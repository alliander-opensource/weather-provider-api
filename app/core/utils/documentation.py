#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0


def prepare_example_response(
    example_response, content_type: str = "application/json"
) -> dict:
    """Creates a FastAPI example response dictionary

    Args:
        example_response (dict or list): example response
        content_type (str): response content-type

    Returns:
        FastAPI example response dict
    """
    return {"content": {content_type: {"example": example_response}}}
