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

project_file = Path(os.getcwd()).parent.joinpath('var_maps').joinpath('arome_var_map.json')
package_file = Path(sys.prefix).joinpath('var_maps').joinpath('arome_var_map.json')

if project_file.exists():
    file_to_use = project_file
else:
    file_to_use = package_file

with open(file_to_use, "r") as _f:
    arome_factors = json.load(_f)
