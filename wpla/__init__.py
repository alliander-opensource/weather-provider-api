#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Init that loads the proper package version.

- If running from a package this init will get the version from the package settings.
- If running locally from its project environment it will gather the version from the pyproject.toml file.
- If none of those work, it will use a default version of '0.0.0' to fill the version number.

"""

import importlib.metadata as importlib_metadata

try:
    __version__ = importlib_metadata.version(__name__)
except importlib_metadata.PackageNotFoundError as e:
    try:
        import toml

        __version__ = toml.load("..\\pyproject.toml")["tool"]["poetry"]["version"]
    except FileNotFoundError as err:
        __version__ = "0.0.0"
