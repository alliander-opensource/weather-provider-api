#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

def parse_bool(string_to_parse: str, setting_name: str = None, suppress_parsing_errors: bool = False):
    """ This function tries to interpret a given string as a boolean value and returns that boolean value

    Returns a ValueError if no boolean value could be interpreted.
    """

    string_to_process = string_to_parse

    if isinstance(string_to_process, bool):
        return bool(string_to_process)

    string_to_process = string_to_process.lower()
    if string_to_process in ("true", "t", "1", "yes", "y"):
        return True
    elif string_to_process in ("false", "f", "0", "no", "n"):
        return False
    else:
        if suppress_parsing_errors:
            return None
        else:
            raise ValueError(
                f"Conversion of {setting_name or 'a'} setting into a boolean failed. Original value: {string_to_parse}"
            )
