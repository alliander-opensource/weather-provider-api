#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from pathlib import Path

import structlog


async def remove_file(
    file_path, logger=structlog.get_logger(__name__)
):  # pragma: no cover
    if file_path is not None:
        try:
            file_to_rm = Path(file_path).resolve()
            logger.info("Removing temporary file", file_path=file_to_rm)
            if file_to_rm.exists() and file_to_rm.is_file():
                file_to_rm.unlink()
        except FileNotFoundError as e:
            logger.exception(e)
            raise
    return True
