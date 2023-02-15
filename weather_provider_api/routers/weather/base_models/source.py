#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0


class WeatherSourceBase(object):  # pragma: no cover
    """
    Base class that contains the basic functionality for all sources. Any new sources should implement this as their
    base class!
    """

    def setup_models(self, model_instances):
        self._models = {model.id: model for model in model_instances if not model.async_model}
        self._async_models = {model.id: model for model in model_instances if model.async_model}

    def get_model(self, model_id, fetch_async=False):
        if fetch_async:
            return self._async_models.get(model_id, None)
        return self._models.get(model_id, None)

    def get_models(self, fetch_async=False):
        if fetch_async:
            return list(self._async_models.values())
        return list(self._models.values())

    @property
    def models(self):
        return self.get_models(fetch_async=False)

    @property
    def async_models(self):
        return self.get_models(fetch_async=True)
