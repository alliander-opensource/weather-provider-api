#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from slowapi import Limiter
from slowapi.util import get_remote_address


RATE_LIMIT_HANDLER = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
