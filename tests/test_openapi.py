# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import json
from typing import Any
from unittest.mock import mock_open, patch

from weather_provider_api.scripts.openapi import generate_openapi_spec


class TestGenerateOpenAPISpec:
    """Test suite for the generate_openapi_spec function."""

    def test_generate_openapi_spec_creates_file(self, tmp_path: str):
        """Test that generate_openapi_spec creates an openapi.json file."""
        _ = tmp_path  # Unused fixture
        mock_spec: dict[str, dict[str, str] | str] = {
            "openapi": "3.0.2",
            "info": {"title": "Weather API (v2)", "version": "2.0.0"},
            "paths": {},
        }

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                # Verify file was opened with correct parameters
                mock_file.assert_called_once_with("openapi.json", "w", encoding="utf-8")

                # Verify the spec was written to file
                handle = mock_file()
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)
                assert written_content == json.dumps(mock_spec, ensure_ascii=False, indent=2)

    def test_generate_openapi_spec_calls_openapi_method(self):
        """Test that the v2_app.openapi() method is called."""
        mock_spec = {"openapi": "3.0.2"}

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()):
                generate_openapi_spec()

                # Verify openapi() was called exactly once
                mock_app.openapi.assert_called_once_with()

    def test_generate_openapi_spec_writes_valid_json(self):
        """Test that the generated file contains valid JSON."""
        mock_spec: dict[str, dict[str, Any] | str] = {
            "openapi": "3.0.2",
            "info": {
                "title": "Weather API (v2)",
                "version": "2.0.0",
                "description": "Test API",
            },
            "paths": {
                "/weather": {
                    "get": {
                        "summary": "Get weather data",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                handle = mock_file()
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)

                # Verify the content is valid JSON and matches the spec
                parsed_json = json.loads(written_content)
                assert parsed_json == mock_spec

    def test_generate_openapi_spec_handles_complex_spec(self):
        """Test that complex OpenAPI specifications are handled correctly."""
        mock_spec = {  # type: ignore
            "openapi": "3.0.2",
            "info": {
                "title": "Weather API (v2)",
                "version": "2.0.0",
                "contact": {
                    "name": "Test Team",
                    "email": "test@example.com",
                },
            },
            "servers": [{"url": "https://api.example.com/api/v2"}],
            "paths": {
                "/weather/{location}": {
                    "get": {
                        "parameters": [
                            {
                                "name": "location",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "temperature": {"type": "number"},
                                                "humidity": {"type": "number"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "WeatherData": {
                        "type": "object",
                        "properties": {
                            "temperature": {"type": "number"},
                            "humidity": {"type": "number"},
                        },
                    }
                }
            },
        }

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                handle = mock_file()
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)

                parsed_json = json.loads(written_content)
                assert parsed_json == mock_spec
                assert "components" in parsed_json
                assert "schemas" in parsed_json["components"]

    def test_generate_openapi_spec_overwrites_existing_file(self):
        """Test that the function overwrites an existing openapi.json file."""
        mock_spec = {"openapi": "3.0.2", "info": {"title": "Test", "version": "1.0.0"}}  # type: ignore

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                # File should be opened in write mode, which overwrites
                mock_file.assert_called_once_with("openapi.json", "w", encoding="utf-8")

    def test_generate_openapi_spec_with_empty_paths(self):
        """Test handling of OpenAPI spec with no paths defined."""
        mock_spec = {  # type: ignore
            "openapi": "3.0.2",
            "info": {"title": "Weather API (v2)", "version": "2.0.0"},
            "paths": {},
        }

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                handle = mock_file()
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)

                parsed_json = json.loads(written_content)
                assert parsed_json["paths"] == {}

    def test_generate_openapi_spec_json_formatting(self):
        """Test that the JSON is written in a pretty-printed format."""
        mock_spec = {  # type: ignore
            "openapi": "3.0.2",
            "info": {"title": "Test", "version": "1.0.0"},
        }

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                handle = mock_file()
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)

                # Verify it's pretty JSON with indentation/newlines
                expected = json.dumps(mock_spec, ensure_ascii=False, indent=2)
                assert written_content == expected
                assert "\n" in written_content

    def test_generate_openapi_spec_integration(self):
        """Integration test verifying the complete flow."""
        mock_spec = {  # type: ignore
            "openapi": "3.0.2",
            "info": {
                "title": "Weather API (v2)",
                "version": "2.73.16",
            },
            "paths": {
                "/weather/sources": {
                    "get": {
                        "summary": "Get available weather sources",
                    }
                }
            },
        }

        with patch("weather_provider_api.scripts.openapi.v2_app") as mock_app:
            mock_app.openapi.return_value = mock_spec

            with patch("builtins.open", mock_open()) as mock_file:
                generate_openapi_spec()

                # Verify the complete interaction
                mock_app.openapi.assert_called_once()
                mock_file.assert_called_once_with("openapi.json", "w", encoding="utf-8")

                handle = mock_file()
                handle.write.assert_called_once_with(json.dumps(mock_spec, ensure_ascii=False, indent=2))
