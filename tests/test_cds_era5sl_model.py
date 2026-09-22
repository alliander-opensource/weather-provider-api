# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, date, datetime

import numpy as np
import pytest
import xarray as xr

from weather_provider_api.routers.weather.base_models.repository import RepoDataFetchResult
from weather_provider_api.routers.weather.sources.cds.models import era5sl
from weather_provider_api.routers.weather.sources.cds.models.era5sl import ERA5SLModel
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class _FakeRepository:
    oldest_date_available = date(2016, 1, 1)
    newest_date_available = date(2026, 9, 17)

    def retrieve_data(self, **kwargs):
        return xr.Dataset({"2m_temperature": ("time", np.array([280.0]))}, coords={"time": [datetime(2026, 9, 1)]}), RepoDataFetchResult.SUCCESS


def _model(monkeypatch: pytest.MonkeyPatch) -> ERA5SLModel:
    monkeypatch.setattr(era5sl, "ERA5SLRepository", _FakeRepository)
    return ERA5SLModel()


def test_model_initializes_as_synchronous_era5sl_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialize the model with its ERA5-SL metadata and conversions."""
    model = _model(monkeypatch)

    assert model.id == "era5sl"
    assert model.is_async() is False
    assert model.to_human["2m_temperature"]["convert"](280.0) == pytest.approx(6.85)


def test_validate_and_request_weather_factors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Accept configured long and short names while dropping unsupported values."""
    model = _model(monkeypatch)
    assert ERA5SLModel._validate_weather_factors(["2m_dewpoint_temperature", "d2m", "invalid"]) == [
        "2m_dewpoint_temperature",
        "2m_dewpoint_temperature",
    ]
    assert model._request_weather_factors(["2M_TEMPERATURE", "2m_temperature", "invalid"]) == ["2m_temperature"]
    assert set(model._request_weather_factors()) == set(model.to_si)


def test_get_weather_delegates_to_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate request dates and return the repository dataset."""
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
    monkeypatch.setattr(model.repository, "retrieve_data", lambda **kwargs: (None, RepoDataFetchResult.FAILURE))

    with pytest.raises(RuntimeError, match="Data retrieval failure"):
        model._fill_dataset_with_data(  # type: ignore[reportPrivateUsage]
            [GeoPosition(52.0, 5.0)],
            datetime(2026, 9, 1),
            datetime(2026, 9, 2),
            ["2m_temperature"],
        )
