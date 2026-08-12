# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# Tests for weather_provider_api.core.base_model. The module only extends PydanticBaseModel with
# `from_attributes=True`, so the tests only verify that this single configuration change is active and functional.

from weather_provider_api.core.base_model import BaseModel


class _ExampleModel(BaseModel):
    name: str
    value: int


def test_base_model_enables_from_attributes():
    """The BaseModel should enable `from_attributes` in its model config."""
    assert BaseModel.model_config.get("from_attributes") is True


def test_base_model_validates_from_object_attributes():
    """Because `from_attributes` is enabled, models should be constructable from arbitrary objects."""

    class _Source:
        name = "temperature"
        value = 42

    validated = _ExampleModel.model_validate(_Source())

    assert validated.name == "temperature"
    assert validated.value == 42
