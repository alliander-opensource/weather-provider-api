# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0 AND CC-BY-2.5

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models import actuele_waarnemingen_register as model_module
from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen_register import (
    ActueleWaarnemingenRegisterModel,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class _FakeRepository:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_24_hour_registry_for_station(self, station: int) -> xr.Dataset:
        self.calls.append("24")
        return _station_dataset()

    def get_48_hour_registry_for_station(self, station: int) -> xr.Dataset:
        self.calls.append("48")
        return _station_dataset()


def _station_dataset() -> xr.Dataset:
    return xr.Dataset(
        {"temperature": (("time", "coord"), np.array([[10.0]]))},
        coords={"time": [datetime(2026, 9, 22, 10, 0)], "coord": [0]},
    )


def _model(monkeypatch: pytest.MonkeyPatch) -> tuple[ActueleWaarnemingenRegisterModel, _FakeRepository]:
    repository = _FakeRepository()
    monkeypatch.setattr(model_module, "ActueleWaarnemingenRegisterRepository", lambda: repository)
    monkeypatch.setattr(model_module, "find_closest_stn_list", lambda stations, coords: ([8], None, None))
    return ActueleWaarnemingenRegisterModel(), repository


def test_model_initializes_and_normalizes_requested_factors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialize the register model and normalize supported factor names."""
    model, _ = _model(monkeypatch)

    assert model.id == "waarnemingen_register"
    assert model.is_async() is False
    assert model._request_weather_factors(["TEMPERATURE", "invalid", "temperature"]) == ["temperature"]
    assert set(model._request_weather_factors()) == set(model.to_si)


@pytest.mark.parametrize("begin, expected_call", [(None, "24"), (datetime.now(UTC) - timedelta(days=2), "48")])
def test_get_weather_selects_registry_window_and_shapes_output(
    monkeypatch: pytest.MonkeyPatch, begin: datetime | None, expected_call: str
) -> None:
    """Select the appropriate registry window and return requested variables."""
    model, repository = _model(monkeypatch)
    coords = [GeoPosition(52.0, 5.0)]

    result = model.get_weather(coords, begin=begin, weather_factors=["temperature"])

    assert repository.calls == [expected_call]
    assert "temperature" in result
    assert result.temperature.values.tolist() == [[[10.0]]]


def test_get_weather_rejects_empty_station_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise when no station data is returned for the requested coordinates."""
    model, _ = _model(monkeypatch)
    monkeypatch.setattr(model_module, "find_closest_stn_list", lambda stations, coords: ([], None, None))

    with pytest.raises(ValueError, match="No data was returned"):
        model.get_weather([GeoPosition(52.0, 5.0)])
