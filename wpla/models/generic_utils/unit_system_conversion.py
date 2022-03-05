#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from enum import Enum


class UnitSystem(str, Enum):
    Metric = 'metric'
    Imperial = 'imperial'
    SI = 'si'
    OriginalFormat = 'original'  # The original format of the data
