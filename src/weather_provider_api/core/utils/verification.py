#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------


def get_value_from_class_if_it_exists(class_object: any, attribute_name: str) -> any:
    """Get the value of an attribute from a class if it exists, otherwise return None."""
    return getattr(class_object, attribute_name) if hasattr(class_object, attribute_name) else None
