#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""CORS support."""

from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from weather_provider_api.config import APP_CONFIG


def _normalize_origin_regex(origins_regex: object) -> str | None:
    """Convert config regex values to a single regex string expected by CORSMiddleware."""
    if origins_regex is None:
        return None

    if isinstance(origins_regex, str):
        regex = origins_regex.strip()
        return regex or None

    if isinstance(origins_regex, (list, tuple)):
        patterns: list[str] = []
        for regex in cast(list[object] | tuple[object, ...], origins_regex):
            if isinstance(regex, str):
                cleaned_regex = regex.strip()
                if cleaned_regex:
                    patterns.append(cleaned_regex)
        if not patterns:
            return None
        return "|".join(f"(?:{pattern})" for pattern in patterns)

    logger.warning(
        f"Invalid type for CORS allowed origins regex: {type(origins_regex)}. Expected str or list/tuple of str."
    )
    return None


def initialize_cors_middleware(app: FastAPI) -> None:
    """Initializes the CORS middleware.

    Enables CORS handling for the allowed origins set in the config setting `CORS_ALLOWED_ORIGINS`, a list of strings
     each corresponding to a host. The FastAPI CORSMiddleware is used to enable CORS handling.

    Args:
        app (FastAPI):  The FastAPI application to attach the CORS middleware to.

    Returns:
        Nothing. The application itself is updated.

    """
    origins = APP_CONFIG["components"]["cors_allowed_origins"]
    origins_regex = _normalize_origin_regex(APP_CONFIG["components"]["cors_allowed_origins_regex"])

    if origins and len(origins) == 0:
        origins = None

    cors_config: dict[str, list[str] | str | bool | type] = {
        "middleware_class": CORSMiddleware,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

    if origins:
        cors_config["allow_origins"] = origins

    if origins_regex:
        cors_config["allow_origin_regex"] = origins_regex

    if not origins and not origins_regex:
        logger.warning("CORS middleware enabled but no allowed origins are set.")
        return

    app.add_middleware(**cors_config)  # type: ignore
