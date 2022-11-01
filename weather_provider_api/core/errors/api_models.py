#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from weather_provider_api.core.base_model import BaseModel


class ErrorResponseModel(BaseModel):
    detail: str  # error message
