# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import asyncio
from types import SimpleNamespace

import numpy as np
import pytest
import xarray as xr
from fastapi import BackgroundTasks, HTTPException, Response

import weather_provider_api.routers.weather.api_view_common as api_view_common
from weather_provider_api.routers.weather.api_models import (
    OutputUnit,
    ResponseFormat,
    WeatherContentRequestQuery,
    WeatherFormattingRequestQuery,
)


def _request_args() -> tuple[WeatherContentRequestQuery, WeatherFormattingRequestQuery]:
    return (
        WeatherContentRequestQuery(
            begin="2026-09-22 00:00",
            end="2026-09-22 01:00",
            lat=52.0,
            lon=5.0,
            factors=["temperature"],
        ),
        WeatherFormattingRequestQuery(units=OutputUnit.si, response_format=ResponseFormat.json),
    )


def _weather_dataset() -> xr.Dataset:
    return xr.Dataset(
        {"temperature": (("time", "lat", "lon"), np.ones((1, 1, 1)))} ,
        coords={"time": ["2026-09-22T00:00:00"], "lat": [52.0], "lon": [5.0]},
    )


def test_get_weather_response_fetches_formats_and_registers_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the successful response path and automatic response-coordinate extraction."""
    ret_args, fmt_args = _request_args()
    calls: dict[str, object] = {}

    class FakeController:
        def get_weather(self, *args, **kwargs): # type: ignore
            calls["get_weather"] = (args, kwargs)
            return _weather_dataset()

        def convert_names_and_units(self, *args, **kwargs): # type: ignore
            calls["convert"] = (args, kwargs)
            return _weather_dataset()

    def fake_serializer(*args, **kwargs): # type: ignore
        calls["serializer"] = (args, kwargs)
        return Response(content=b"ok"), "temporary-response-file"

    monkeypatch.setattr(api_view_common, "controller", FakeController())
    monkeypatch.setattr(api_view_common.serializers, "return_file_or_text_response", fake_serializer) # type: ignore
    cleanup_tasks = BackgroundTasks()

    response = asyncio.run(
        api_view_common.get_weather_response(
            source_id="KNMI",
            model_id="AROME",
            cleanup_tasks=cleanup_tasks,
            ret_args=ret_args,
            fmt_args=fmt_args,
            accept=ResponseFormat.csv,
            coords=[[(52.0, 5.0)]],
        )
    )

    assert response.body == b"ok"
    assert calls["get_weather"][0] == ("knmi", "arome")  # type: ignore[index]
    assert calls["convert"][0][:3] == ("knmi", "arome", False)  # type: ignore[index]
    serializer_args = calls["serializer"][0]  # type: ignore[index]
    assert serializer_args[1] == ResponseFormat.json
    assert serializer_args[-1] == [(52.0, 5.0)]
    assert len(cleanup_tasks.tasks) == 1
    assert cleanup_tasks.tasks[0].args == ("temporary-response-file",)


def test_get_weather_response_uses_accept_when_response_format_is_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the Accept-header format when no response format query parameter is provided."""
    ret_args, _ = _request_args()
    fmt_args = WeatherFormattingRequestQuery(units=OutputUnit.si)
    captured: dict[str, object] = {}

    class FakeController:
        def get_weather(self, *args, **kwargs):  # type: ignore
            return _weather_dataset()

        def convert_names_and_units(self, *args, **kwargs):  # type: ignore
            return _weather_dataset()

    def fake_serializer(*args, **kwargs):  # type: ignore
        captured["response_format"] = args[1]
        return Response(content=b"ok"), None

    monkeypatch.setattr(api_view_common, "controller", FakeController())
    monkeypatch.setattr(api_view_common.serializers, "return_file_or_text_response", fake_serializer)  # type: ignore

    asyncio.run(
        api_view_common.get_weather_response(
            source_id="knmi",
            model_id="arome",
            cleanup_tasks=BackgroundTasks(),
            ret_args=ret_args,
            fmt_args=fmt_args,
            accept=ResponseFormat.csv,
            coords=[[(52.0, 5.0)]],
        )
    )

    assert captured["response_format"] == ResponseFormat.csv


def test_get_weather_response_uses_explicit_response_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that supplied response coordinates bypass coordinate extraction from the dataset."""
    ret_args, fmt_args = _request_args()
    captured: dict[str, object] = {}

    class FakeController:
        def get_weather(self, *args, **kwargs): # type: ignore
            return _weather_dataset()

        def convert_names_and_units(self, *args, **kwargs): # type: ignore
            return _weather_dataset()

    def fake_serializer(*args, **kwargs): # type: ignore
        captured["coordinates"] = args[-1]
        return Response(content=b"ok"), None

    monkeypatch.setattr(api_view_common, "controller", FakeController())
    monkeypatch.setattr(api_view_common.serializers, "return_file_or_text_response", fake_serializer) # type: ignore
    explicit_coordinates = [(51.9, 4.9)]

    asyncio.run(
        api_view_common.get_weather_response(
            source_id="knmi",
            model_id="arome",
            cleanup_tasks=BackgroundTasks(),
            ret_args=ret_args,
            fmt_args=fmt_args,
            accept=ResponseFormat.json,
            coords=[[(52.0, 5.0)]],
            response_coords=explicit_coordinates,
        )
    )

    assert captured["coordinates"] == explicit_coordinates


def test_get_weather_response_translates_missing_file_to_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing repository files become a 404 HTTP exception."""
    ret_args, fmt_args = _request_args()
    fake_controller = SimpleNamespace(
        get_weather=lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("missing.nc")) # type: ignore
    )
    monkeypatch.setattr(api_view_common, "controller", fake_controller)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            api_view_common.get_weather_response(
                "knmi", "arome", BackgroundTasks(), ret_args, fmt_args, ResponseFormat.json, [[(52.0, 5.0)]]
            )
        )

    assert error.value.status_code == 404
    assert error.value.detail == "missing.nc"


def test_get_weather_response_returns_404_for_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an empty controller result becomes a 404 HTTP exception."""
    ret_args, fmt_args = _request_args()
    fake_controller = SimpleNamespace(get_weather=lambda *args, **kwargs: None) # type: ignore
    monkeypatch.setattr(api_view_common, "controller", fake_controller)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            api_view_common.get_weather_response(
                "knmi", "arome", BackgroundTasks(), ret_args, fmt_args, ResponseFormat.json, [[(52.0, 5.0)]]
            )
        )

    assert error.value.status_code == 404
    assert error.value.detail == "No data was found for the given period"