#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import json

import pytest

from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from wpla.api.core.initializers.exception_handling import handle_http_exception
from wpla.configuration import app_config


@pytest.mark.asyncio
async def test_handle_http_exception(monkeypatch):
    mocked_request_scope = {
        "type": "http",
        "path": '/dummy_path',
        "headers": Headers().raw,
        "http_version": "1.1",
        "method": 'GET',
        "scheme": "https",
        "client": ("127.0.0.1", 8080),
        "server": ("127.0.0.1", 443),
    }
    mocked_request = Request(mocked_request_scope)
    mocked_exception = StarletteHTTPException(404, 'just a test')

    # With maintainer information
    old_value = app_config.show_maintainer_info
    app_config.show_maintainer_info = True
    handled_exception = await handle_http_exception(mocked_request, mocked_exception)

    assert handled_exception.status_code == 404
    exception_body = json.loads(handled_exception.body.decode('ascii'))

    assert exception_body['detail'] == 'just a test'
    assert exception_body['request'] == 'https://127.0.0.1/dummy_path'

    assert exception_body['maintainer'] == app_config.maintainer
    assert exception_body['maintainer_email'] == app_config.maintainer_email

    # Without maintainer information
    app_config.show_maintainer_info = False
    handled_exception = await handle_http_exception(mocked_request, mocked_exception)

    assert handled_exception.status_code == 404
    exception_body = json.loads(handled_exception.body.decode('ascii'))
    assert exception_body['detail'] == 'just a test'
    assert exception_body['request'] == 'https://127.0.0.1/dummy_path'

    with pytest.raises(KeyError) as exception_info:
        assert exception_body['maintainer']
    assert str(exception_info.value) == "'maintainer'"

    app_config.show_maintainer_info = old_value
