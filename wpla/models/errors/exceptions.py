#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import inspect
from typing import Any


class ModelMissingClassAttributeException(Exception):
    def __init__(self, parent_class: str, attribute_missing: str, detail: Any = None):
        self.parent_class = parent_class
        self.attribute_missing = attribute_missing
        self.detail = (
                detail or "A WeatherModelBase class is missing a required attribute."
        )

    def __str__(self):
        return f"class=={self.parent_class} \\ attribute=={self.attribute_missing} >> {self.detail}"


class SourceMissingClassAttributeException(Exception):
    def __init__(self, parent_class: str, attribute_missing: str, detail: Any = None):
        self.parent_class = parent_class
        self.attribute_missing = attribute_missing
        self.detail = (
                detail or "A WeatherSourceBase class is missing a required attribute."
        )

    def __str__(self):
        return f"class=={self.parent_class} \\ attribute=={self.attribute_missing} >> {self.detail}"


class InvalidWeatherModelException(Exception):
    def __init__(self, source: str, model: str, sync: bool, detail: Any = None):
        self.source = source
        self.model = model
        self.sync = sync
        self.detail = (
                detail or "An invalid WeatherModel was requested by a WeatherSource"
        )

    def __str__(self):
        return f"WeatherSource: {self.source} \\ WeatherModel: {self.model} \\ sync: {self.sync} >> {self.detail}"


class InvalidWeatherSourceException(Exception):
    def __init__(self, source: str, detail: Any = None):
        self.source = source
        self.detail = (
                detail or "A WeatherSource object is not considered a valid WeatherSource"
        )

    def __str__(self):
        return f"WeatherSource: {self.source} >> {self.detail}"
