#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import pytest

from wpla.api.core.exceptions.exceptions import APIExpiredException


def test_APIExpiredException():
    def raise_test(text: str):
        raise APIExpiredException(text)

    with pytest.raises(APIExpiredException) as exception_info:
        assert raise_test('Test details')
    assert exception_info.value.detail == 'Test details'
    assert exception_info.value.status_code == 503
    assert str(exception_info.value) == 'Test details'
