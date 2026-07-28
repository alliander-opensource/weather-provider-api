# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Request Rate Limiter initializer."""

from slowapi import Limiter
from slowapi.util import get_remote_address

API_RATE_LIMITER = Limiter(key_func=get_remote_address, default_limits=["5/minute"])
