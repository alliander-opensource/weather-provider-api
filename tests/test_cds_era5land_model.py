# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest
import xarray as xr

from weather_provider_api.routers.weather.base_models.repository import RepoDataFetchResult
from weather_provider_api.routers.weather.sources.cds.models import era5land
from weather_provider_api.routers.weather.sources.cds.models.era5land import ERA5LandModel
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class _FakeRepository:
    oldest_date_available = date(2016, 1, 1)
    newest_date_available = date(2026, 9, 17)

    def retrieve_data(self, **kwargs):
        return xr.Dataset({"2m_temperature": ("time", np.array([280.0]))}, coords={"time": [datetime(2026, 9, 1)]}), RepoDataFetchResult.SUCCESS


def _model(monkeypatch: pytest.MonkeyPatch) -> ERA5LandModel:
    monkeypatch.setattr(era5land, "ERA5LandRepository", _FakeRepository)
    return ERA5LandModel()


def test_model_initializes_as_synchronous_era5land_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialize the model with its ERA5-Land metadata and conversions."""
    model = _model(monkeypatch)

    assert model.id == "era5land"
    assert model.name == "CDS: ERA5-Land"
    assert model.is_async() is False
    assert model.to_human["2m_temperature"]["convert"](280.0) == pytest.approx(6.85)


def test_validate_weather_factors_accepts_long_and_short_names() -> None:
    """Normalize supported long and CDS short factor names while dropping invalid values."""
    factors = ERA5LandModel._validate_weather_factors(["2m_dewpoint_temperature", "d2m", "invalid"])

    assert "2m_dewpoint_temperature" in factors
    assert factors.count("2m_dewpoint_temperature") == 2
    assert "invalid" not in factors
    assert ERA5LandModel._validate_weather_factors(None)


def test_request_weather_factors_normalizes_case_and_removes_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Normalize requested factors through the model conversion dictionary."""
    model = _model(monkeypatch)

    result = model._request_weather_factors(["2M_TEMPERATURE", "2m_temperature", "invalid"])

    assert result == ["2m_temperature"]
    assert set(model._request_weather_factors()) == set(model.to_si)


def test_get_weather_delegates_validated_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate dates and factors before returning repository data."""
    model = _model(monkeypatch)
    expected = xr.Dataset({"2m_temperature": ("time", [280.0])}, coords={"time": [datetime(2026, 9, 1)]})
    monkeypatch.setattr(model, "_fill_dataset_with_data", lambda *args: expected)

    result = model.get_weather(
        [GeoPosition(52.0, 5.0)],
        begin=datetime(2026, 9, 1, tzinfo=UTC),
        end=datetime(2026, 9, 2, tzinfo=UTC),
        weather_factors=["2m_temperature"],
    )

    assert result is expected


def test_fill_dataset_raises_when_repository_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise a runtime error when the repository cannot provide data."""
    model = _model(monkeypatch)
    monkeypatch.setattr(
        model.repository,
        "retrieve_data",
        lambda **kwargs: (None, RepoDataFetchResult.FAILURE),
    )

    with pytest.raises(RuntimeError, match="Data retrieval failure"):
        model._fill_dataset_with_data(  # type: ignore[reportPrivateUsage]
            [GeoPosition(52.0, 5.0)],
            datetime(2026, 9, 1),
            datetime(2026, 9, 2),
            ["2m_temperature"],
        )
