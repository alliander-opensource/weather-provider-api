#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import os
from datetime import date, datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from . import __version__


class _MaintainerSettings(BaseModel):
    name: str
    email: str
    add_to_headers: bool


class _ConnectedAPISettings(BaseModel):
    version: int
    expiration_date: date | None

    # Pydantic configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)


class _ComponentSettings(BaseModel):
    prometheus_endpoint: str | None
    cors: dict | None
    rate_limiter: dict | None
    project_logger: dict


class _APISettings(BaseModel):
    title: str
    full_title: str
    description: str
    expiration_date: date | None
    server_url: str


class _WPAConfiguration(BaseModel):
    version: str
    api_settings: _APISettings
    maintainer: _MaintainerSettings | None
    connected_apis: list[_ConnectedAPISettings] = []
    component_settings: _ComponentSettings

    # Pydantic configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)


def __get_configuration() -> _WPAConfiguration:
    settings = __load_settings_from_config_file()
    return settings


def __load_settings_from_config_file() -> _WPAConfiguration:
    project_folder = __find_main_project_folder()
    config_file = __find_applicable_config_file(project_folder)

    settings = __process_config_file_into_settings(config_file)

    return settings


def __find_main_project_folder() -> Path:
    try:
        project_folder = Path(__file__).parent
    except NameError as name_error:
        raise NameError(f"Error finding main project folder: {name_error}") from name_error

    return project_folder


def __find_applicable_config_file(project_folder: Path) -> Path:
    list_of_possible_config_file_locations_in_order = [
        Path(os.getcwd()).joinpath("config.yaml"),
        Path(os.getcwd()).joinpath("config/config.yaml"),
        Path("/app/config.yaml"),
        Path("/app_config/config.yaml"),
        Path("/etc/weather-provider-api/config.yaml"),
        project_folder.joinpath("config.yaml"),
        project_folder.joinpath("config/config.yaml"),
    ]

    for location in list_of_possible_config_file_locations_in_order:
        if location.exists() and location.is_file():
            return location

    raise FileNotFoundError("No valid configuration file found for the Weather Provider API.")


def __process_config_file_into_settings(config_file: Path) -> _WPAConfiguration:
    try:
        with open(config_file) as file:
            yaml_content = yaml.safe_load(file)
    except Exception as error:
        raise ValueError(f"Error processing settings from configuration file: {error}") from error

    if yaml_content.get("weather-provider-api") is None:
        raise ValueError("No API settings found in configuration file.")

    settings = __process_config_yaml_into_settings(yaml_content.get("weather-provider-api"))

    return settings


def __process_config_yaml_into_settings(yaml_content: dict) -> _WPAConfiguration:
    api_settings = __load_api_settings_from_yaml(yaml_content)
    maintainer = __load_maintainer_settings_from_yaml(yaml_content.get("maintainer"))
    connected_apis = __load_connected_apis_from_yaml(yaml_content.get("connected-api-versions"))
    component_settings = __load_component_settings_from_yaml(yaml_content.get("components"))

    return _WPAConfiguration(
        version=__version__,
        api_settings=api_settings,
        maintainer=maintainer,
        connected_apis=connected_apis,
        component_settings=component_settings,
    )


def __load_api_settings_from_yaml(base_yaml: dict) -> _APISettings:
    api_settings = _APISettings(
        title=base_yaml.get("short-title"),
        full_title=base_yaml.get("full-title"),
        description=base_yaml.get("description"),
        expiration_date=(
            datetime.strptime(base_yaml.get("expiration-date"), "%Y-%m-%d").date()
            if base_yaml.get("expiration-date")
            else None
        ),
        server_url=base_yaml.get("server-url"),
    )

    return api_settings


def __load_maintainer_settings_from_yaml(maintainer_yaml: dict) -> _MaintainerSettings | None:
    maintainer_settings = _MaintainerSettings(
        name=maintainer_yaml.get("name"),
        email=maintainer_yaml.get("email"),
        add_to_headers=maintainer_yaml.get("add-maintainer-to-headers", False),
    )

    return maintainer_settings


def __load_connected_apis_from_yaml(connected_apis_yaml: dict) -> [_ConnectedAPISettings]:
    connected_apis = (
        [
            _ConnectedAPISettings(
                version=connected_api.get("version"),
                expiration_date=(
                    datetime.strptime(connected_api.get("expiration-date"), "%Y-%m-%d").date()
                    if connected_api.get("expiration-date")
                    else None
                ),
            )
            for connected_api in connected_apis_yaml
        ]
        if connected_apis_yaml
        else []
    )

    return connected_apis


def __load_component_settings_from_yaml(components_yaml: dict) -> _ComponentSettings:
    prometheus_settings = components_yaml.get("prometheus-endpoint")
    cors_settings = (
        {
            "allow_origins": components_yaml.get("cors").get("allow-origins"),
            "allow_origins_regex": components_yaml.get("cors").get("allow-origins-regex"),
        }
        if components_yaml.get("cors")
        else None
    )
    rate_limiter_settings = (
        {
            "max_requests": components_yaml.get("rate-limiter").get("default-max-requests-per-minute"),
            "max_requests_heavy_load": components_yaml.get("rate-limiter").get(
                "heavy-load-max-requests-per-minute", None
            ),
            "max_requests_minimal_load": components_yaml.get("rate-limiter").get(
                "minimal-load-max-requests-per-minute", None
            ),
        }
        if components_yaml.get("rate-limiter")
        else None
    )
    project_logger_settings = {
        "log_level": components_yaml.get("project-logger").get("log-level", "debug"),
        "log_format": components_yaml.get("project-logger").get("log-format", "plain"),
    }

    return _ComponentSettings(
        prometheus_endpoint=prometheus_settings,
        cors=cors_settings,
        rate_limiter=rate_limiter_settings,
        project_logger=project_logger_settings,
    )


API_CONFIGURATION = __get_configuration()
