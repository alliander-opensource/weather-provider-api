#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import importlib.metadata as importlib_metadata
from importlib import reload
import pytest
import toml

from wpla.configuration import get_configuration
import wpla


@pytest.mark.parametrize(
    "debugging,deployed,config_type",
    [
        (False, False, 'configuration'),
        (True, False, 'debug_configuration'),
        (False, True, 'deployed_configuration'),
        (True, True, 'debug_deployed_configuration')
    ],
)
def test_get_configuration(debugging, deployed, config_type):
    assert get_configuration(debugging, deployed).config_type == config_type


def test_version_init_by_package(monkeypatch):
    # Fix metadata outcome
    def mock_metadata_version(_: str):
        return '1.1.1'
    monkeypatch.setattr(importlib_metadata, 'version', mock_metadata_version)

    reload(wpla)  # Reload to prevent the originally loaded value from interfering
    assert wpla.__version__ == '1.1.1'


def test_version_init_by_toml(monkeypatch):
    # Prevent metadata outcome
    def mock_metadata_version(_: str):
        raise importlib_metadata.PackageNotFoundError
    monkeypatch.setattr(importlib_metadata, 'version', mock_metadata_version)

    # Fix toml outcome
    def mock_toml_load(_: str):
        return {
            'tool': {
                'poetry': {
                    'version': '9.9.9'
                }
            }
        }
    monkeypatch.setattr(toml, "load", mock_toml_load)

    reload(wpla)  # Reload to prevent the originally loaded value from interfering
    assert wpla.__version__ == '9.9.9'


def test_version_init_by_failure(monkeypatch):
    # Prevent metadata outcome
    def mock_metadata_version(_: str):
        raise importlib_metadata.PackageNotFoundError
    monkeypatch.setattr(importlib_metadata, 'version', mock_metadata_version)

    # Prevent toml outcome
    def mock_toml_load(_: str):
        raise FileNotFoundError()
    monkeypatch.setattr(toml, "load", mock_toml_load)

    reload(wpla)  # Reload to prevent the originally loaded value from interfering
    assert wpla.__version__ == '0.0.0'
