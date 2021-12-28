#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import json
import os
from http.client import HTTPException

import pytest
from fastapi import HTTPException as FastAPIHTTPException
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from wpla.api.core.initializers.error_handling import handle_http_exception
from wpla.configuration import Config


@pytest.mark.asyncio
async def test_handle_http_exception():
    # Case #1: Valid Request and valid Starlette HTTPException
    exception_detail = 'An Exception! Oh no!'
    request = Request({
        "type": "http",
        "headers": Headers({}).raw
    })
    exception = StarletteHTTPException(404, exception_detail)
    response = await handle_http_exception(request, exception)

    assert response.status_code == 404
    assert json.loads(response.body)['detail'] == exception_detail

    # Case #2: Test effects 'show_maintainer' setting":
    maintainer = Config['app']['maintainer']
    maintainer_email = Config['app']['maintainer_email']
    original_show_maintainer_value = Config['show_maintainer']
    Config['show_maintainer'] = True
    response = await handle_http_exception(request, exception)

    assert response.status_code == 404
    assert json.loads(response.body)['detail'] == exception_detail
    assert json.loads(response.body)['maintainer'] == maintainer
    assert json.loads(response.body)['maintainer_email'] == maintainer_email

    Config['show_maintainer'] = False
    response = await handle_http_exception(request, exception)

    assert response.status_code == 404
    assert json.loads(response.body)['detail'] == exception_detail
    assert 'maintainer' not in json.loads(response.body)
    assert 'maintainer_email' not in json.loads(response.body)

    Config['show_maintainer'] = original_show_maintainer_value

    # Case #3: FastAPI HTTPException instead of the Starlette type should still work
    exception = FastAPIHTTPException(404, exception_detail)
    response = await handle_http_exception(request, exception)

    assert response.status_code == 404
    assert json.loads(response.body)['detail'] == exception_detail

    # Case #4: HTTP client HTTPException instead of the Starlette type is incompatible however
    exception = HTTPException(404, exception_detail)

    with pytest.raises(AttributeError):
        await handle_http_exception(request, exception)
