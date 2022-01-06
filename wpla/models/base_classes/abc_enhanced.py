#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from abc import ABCMeta

from wpla.models.errors.exceptions import ModelMissingClassAttributeException


class ABCEnhanced(ABCMeta):
    required_attributes = []

    def __call__(self, *args, **kwargs):
        parent_class = super(ABCEnhanced, self).__call__(*args, **kwargs)
        for attr_name in parent_class.required_attributes:
            if not getattr(parent_class, attr_name):
                raise ModelMissingClassAttributeException(parent_class.__name__, attr_name)

        return parent_class
