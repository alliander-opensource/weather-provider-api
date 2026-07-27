# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0


from typing import Any

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase


class WeatherSourceBase:  # pragma: no cover
    """Base class that contains the basic functionality for all sources.

    Any new sources should implement this as their base class!
    """

    def __init__(
        self, source_id: str, name: str, url: str, model_instances: list[WeatherModelBase], *args: Any, **kwargs: Any
    ) -> None:
        """Initialize the WeatherSourceBase with an ID and set up the models."""
        self.id = source_id
        self.name = name
        self.url = url
        self._models: dict[str, WeatherModelBase] = {
            model.id: model for model in model_instances if not model.async_model
        }
        self._async_models: dict[str, WeatherModelBase] = {
            model.id: model for model in model_instances if model.async_model
        }
        super().__init__(*args, **kwargs)

    def get_model(self, model_id: str, fetch_async: bool = False) -> WeatherModelBase | None:
        """Get a specific model from the source based on the provided model ID and whether it is an asynchronous request or not."""
        if fetch_async:
            return self._async_models.get(model_id, None)
        return self._models.get(model_id, None)

    def get_models(self, fetch_async: bool = False) -> list[WeatherModelBase]:
        """Get all models from the source based on whether it is an asynchronous request or not."""
        if fetch_async:
            return list(self._async_models.values())
        return list(self._models.values())

    @property
    def models(self) -> list[WeatherModelBase]:
        """Get all synchronous models from the source."""
        return self.get_models(fetch_async=False)

    @property
    def async_models(self) -> list[WeatherModelBase]:
        """Get all asynchronous models from the source."""
        return self.get_models(fetch_async=True)
