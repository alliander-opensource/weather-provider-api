#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Base Model class

An expansion of the PydanticBaseModel used to build each Weather Provider Base class.
"""

from pydantic import BaseModel as PydanticBaseModel


class BaseModel(PydanticBaseModel):
    """Minimal PydanticBaseMode expansion used in all base classes"""

    class Config:
        from_attributes = True
