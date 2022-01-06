#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime
from typing import List

import structlog

from wpla.models.base_classes.abc_enhanced import ABCEnhanced
from wpla.models.base_classes.base_model import WeatherModelBase
from wpla.models.errors.exceptions import InvalidWeatherModelException, InvalidWeatherSourceException


class WeatherSourceBase(metaclass=ABCEnhanced):
    required_attributes = [
        'short_name',  # The short name and ID of the WeatherSource
        'long_name',  # A longer more descriptive name for the WeatherSource
        'source_description',  # A short description informing of the identity of the source and what kind of data can
                               # can be expected from it. References to any main API or other interface systems can
                               # also be mentioned here
        'source_url',  # A URL leading to the source's main website
    ]

    def __init__(self):
        self.logger = structlog.getLogger(__name__)
        self.sync_models = {}
        self.async_models = {}

    def initialize_models(self, model_instances: List[WeatherModelBase]):
        self.sync_models = {model.short_name: model for model in model_instances if model.synchronous}
        self.async_models = {model.short_name: model for model in model_instances if not model.synchronous}

    def get_model(self, short_name: str, get_sync_model: bool = True):
        if get_sync_model:
            if short_name not in self.sync_models:
                raise InvalidWeatherModelException(source=self.id, model=short_name, sync=get_sync_model,
                                                   detail=f"WeatherSource {self.id} could not find "
                                                          f"WeatherModel:{short_name} (synchronous: {get_sync_model}).")
            return self.sync_models.get(short_name, None)
        else:
            if short_name not in self.async_models:
                raise InvalidWeatherModelException(source=self.id, model=short_name, sync=get_sync_model,
                                                   detail=f"WeatherSource {self.id} could not find "
                                                          f"WeatherModel:{short_name} (synchronous: {get_sync_model}).")
            return self.async_models.get(short_name, None)

    @property
    def self_validate(self):
        """Validates the WeatherSource by validating all of its models, removing any that are not working and finally
        verifying at least one model still remains.

        Returns:
            The value True if everything was validated successfully and raises an InvalidWeatherSourceException
        """
        for model in self.sync_models.copy():
            try:
                _ = model.is_valid()  # We just want to trigger the is_valid() function. An invalid
            except InvalidWeatherModelException as e:
                self.logger.error(f"Removing WeatherModel {model.short_name} from WeatherSource {self.id} as "
                                  f"it was found invalid: {e}",
                                  datetime=datetime.utcnow())
                self.sync_models.pop(model)

        for model in self.async_models.copy():
            try:
                _ = model.is_valid()  # We just want to trigger the is_valid() function. An invalid
            except InvalidWeatherModelException as e:
                self.logger.error(f"Removing WeatherModel {model.short_name} from WeatherSource {self.id} as "
                                  f"it was found invalid: {e}",
                                  datetime=datetime.utcnow())
                self.async_models.pop(model)

        no_of_models = len(self.sync_models.keys()) + len(self.async_models.keys())
        if no_of_models <= 0:
            raise InvalidWeatherSourceException(source=self.id,
                                                detail=f"WeatherSource [{self.id}] has no models left and is "
                                                       f"therefore invalid")

        return True

    @property
    def id(self):
        return self.short_name  # routing short_name to id for easier access
