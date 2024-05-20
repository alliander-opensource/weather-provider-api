#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging

from fastapi import FastAPI

from weather_provider_api.core.utils.verification import get_value_from_class_if_it_exists


def mount_sub_application_to_base_application(base_application: FastAPI, sub_application: FastAPI):
    """Mounts a sub-application to the base application."""
    base_title, sub_title, sub_root_path = __get_required_titles_and_path_for_mounting(
        base_application, sub_application
    )

    base_application.mount(path=sub_root_path, app=sub_application)

    logging.debug(f"Mounted sub-application [{sub_title}] to [{base_title}] at {sub_root_path}")


def __get_required_titles_and_path_for_mounting(base_application: FastAPI, sub_application: FastAPI):
    base_title = get_value_from_class_if_it_exists(base_application, "title")
    sub_title = get_value_from_class_if_it_exists(sub_application, "title")
    sub_root_path = get_value_from_class_if_it_exists(sub_application, "root_path")

    if not base_title or not sub_title:
        raise ValueError("Both the base and sub application must have a title")

    if not sub_root_path:
        raise ValueError("The sub application must have a root path")

    return base_title, sub_title, sub_root_path
