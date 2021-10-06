#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# factor name mapping

import json
import os
import sys
from pathlib import Path


def _get_proper_file_location() -> Path:
    file_name = 'arome_var_map.json'
    var_map_folder = 'var_maps'

    possible_main_folders = [
        Path(os.getcwd()),
        Path(os.getcwd()).parent,
        Path(sys.prefix)
    ]

    for folder in possible_main_folders:
        if folder.joinpath(var_map_folder).exists():
            return folder.joinpath(var_map_folder).joinpath(file_name)

    raise FileNotFoundError


file_to_use = _get_proper_file_location()
print("FILE TO USE:", file_to_use)

with open(file_to_use, "r") as _f:
    arome_factors = json.load(_f)
