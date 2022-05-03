#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The MeteoSource

The MeteoSource class is what allows us to use similar names for similar models, while still being able to identify
which model it is.

"""

from abc import ABCMeta
from urllib.parse import urlparse

from loguru import logger

from wpla.libraries.exceptions.exceptions import (
    InvalidMeteoSourceException,
    ModelNotFoundException,
)
from wpla.libraries.model import MeteoModel


class MeteoSource(metaclass=ABCMeta):
    """The MeteoSource class

    This class is used to group a number of models together by linking them to common origin.
    (this can be a meteorological organisation, a website for weather-data, or any other grouping of models that can
    be identified through a common name, description and ideally a website.

    """

    def __init__(self):
        self.short_name = None
        self.long_name = None
        self.description = None
        self.information_url = None
        self.models = {}

    @property
    def valid(self):
        """MeteoSource self-check"""
        if self.short_name is None or len(self.short_name) > 24:
            raise InvalidMeteoSourceException(
                f"MeteoModel short name is missing or too long: [{self.short_name}]"
            )

        if self.long_name is None or len(self.short_name) > len(
            self.long_name
        ):
            raise InvalidMeteoSourceException(
                f"MeteoModel long name is missing or too short: [{self.long_name}]"
            )

        if self.description is None:
            raise InvalidMeteoSourceException(
                "MeteoModel description is missing"
            )

        if (
            self.information_url is None
            or urlparse(self.information_url).scheme is None
            or urlparse(self.information_url).netloc is None
        ):
            raise InvalidMeteoSourceException(
                f"MeteoModel information URL is missing or invalid: [{self.information_url}]"
            )

        if len(self.models) == 0:
            raise InvalidMeteoSourceException(
                "MeteoModel is not populated by any models"
            )

        return True

    def get_model(self, model_short_name: str, asynchronous: bool = None):
        """Gather and return a specific model in the MeteoSource if it can be found"""
        if model_short_name not in self.models:
            raise ModelNotFoundException(model_short_name)

        model = self.models[model_short_name]
        if asynchronous is not None:
            if model.asynchronous != asynchronous:
                if model.asynchronous:
                    status_string = "a-synchronous"
                    not_status_string = "synchronous"
                else:
                    status_string = "synchronous"
                    not_status_string = "a-synchronous"
                raise ModelNotFoundException(
                    model_short_name,
                    detail=f"MeteoModel [{model_short_name}] was requested as a {status_string} model, "
                    f"but could only be found as [{not_status_string}] model.",
                )

        return model

    @property
    def name(self):
        """Shorthand property for the short_name attribute."""
        return self.short_name

    def add_model(self, meteo_model: MeteoModel):
        """Adds a model to the MeteoSource"""
        self.models[meteo_model.short_name] = meteo_model
        logger.info(
            f"Added model [{meteo_model.short_name}] to source {self.short_name}"
        )
