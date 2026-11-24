# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# Tests for the prepare_example_response helper in weather_provider_api.core.utils.example_responses.

from weather_provider_api.core.utils.example_responses import prepare_example_response


def test_prepare_example_response_with_dict_and_default_content_type():
    """A dict example should be wrapped for the default application/json content type."""
    example = {"temperature": 20.5, "humidity": 55}

    result = prepare_example_response(example)

    assert result == {"content": {"application/json": {"example": example}}}


def test_prepare_example_response_with_list_and_custom_content_type():
    """A list example should be wrapped for the provided content type."""
    example = [{"temperature": 20.5}, {"temperature": 21.0}]

    result = prepare_example_response(example, content_type="text/csv")

    assert result == {"content": {"text/csv": {"example": example}}}


def test_prepare_example_response_preserves_example_object_identity():
    """The helper should embed the exact example object it was given, not a copy."""
    example = {"a": 1}

    result = prepare_example_response(example)

    assert result["content"]["application/json"]["example"] is example
