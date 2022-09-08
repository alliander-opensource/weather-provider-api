#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import pytest
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from wpla.api.core.exceptions.exceptions import APIExpiredException
from wpla.api.core.initializers.exception_handling import handle_http_exception
from wpla.configuration import app_config


def test_api_expired_exception():
    test_string = 'testing details string'

    def raise_test(text:str):
        raise APIExpiredException(text)

    with pytest.raises(APIExpiredException) as exception_info:
        assert raise_test(test_string)
    assert exception_info.value.detail == test_string
    assert exception_info.value.status_code == 503
    assert str(exception_info.value) == test_string


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
    test_string = 'just a test'
    mocked_request = Request(mocked_request_scope)
    mocked_exception = StarletteHTTPException(404, test_string)

    # With maintainer information
    old_value = app_config.show_maintainer_info
    app_config.show_maintainer_info = True
    handled_exception = await handle_http_exception(mocked_request, mocked_exception)

    assert handled_exception.status_code == 404
    exception_body = json.loads(handled_exception.body.decode('ascii'))

    assert exception_body['detail'] == test_string
    assert exception_body['request'] == 'https://127.0.0.1/dummy_path'

    assert exception_body['maintainer'] == app_config.maintainer
    assert exception_body['maintainer_email'] == app_config.maintainer_email

    # Without maintainer information
    app_config.show_maintainer_info = False
    handled_exception = await handle_http_exception(mocked_request, mocked_exception)

    assert handled_exception.status_code == 404
    exception_body = json.loads(handled_exception.body.decode('ascii'))
    assert exception_body['detail'] == test_string
    assert exception_body['request'] == 'https://127.0.0.1/dummy_path'

    with pytest.raises(KeyError) as exception_info:
        assert exception_body['maintainer']
    assert str(exception_info.value) == "'maintainer'"

    app_config.show_maintainer_info = old_value
