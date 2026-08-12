# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for the KNMIDataPlatformDownloader, focused on Data Platform quota handling."""

import pytest
import requests  # type: ignore

from weather_provider_api.routers.weather.sources.knmi.client.knmi_data_platform_downloader import (
    KNMIDataPlatformDownloader,
)


class _MockResponse:
    """A minimal stand-in for a requests.Response object."""

    def __init__(self, status_code: int, text: str = "", json_data: dict | None = None):  # type: ignore
        self.status_code = status_code
        self.text = text
        self._json_data = json_data if json_data is not None else {}
        self.headers: dict[str, str] = {}

    def json(self):  # type: ignore
        return self._json_data


def _build_downloader(monkeypatch: pytest.MonkeyPatch) -> KNMIDataPlatformDownloader:
    """Create a downloader instance with a mocked, successful validation request."""
    monkeypatch.setenv("KNMI_DATA_PLATFORM_KEY", "dummy-access-key")

    def _mock_get_ok(*args, **kwargs):  # type: ignore
        return _MockResponse(200, json_data={"files": [], "nextPageToken": None})

    monkeypatch.setattr(requests, "get", _mock_get_ok)
    return KNMIDataPlatformDownloader()


def test_quota_exceeded_403_sets_timeout_and_raises(monkeypatch: pytest.MonkeyPatch):
    """A 403 'Quota exceeded' response should raise a ValueError and set a quota timeout."""
    downloader = _build_downloader(monkeypatch)
    assert downloader.data_platform_quota_timeout is None

    def _mock_get_quota(*args, **kwargs):  # type: ignore
        return _MockResponse(403, text="Quota exceeded for this API key")

    monkeypatch.setattr(requests, "get", _mock_get_quota)

    with pytest.raises(ValueError) as exception_info:
        downloader.retrieve_file_and_size_list_for_dataset("some_dataset", "1.0", max_files=1)

    assert "Quota exceeded" in str(exception_info.value)
    assert downloader.data_platform_quota_timeout is not None


def test_quota_exceeded_429_sets_timeout_and_raises(monkeypatch: pytest.MonkeyPatch):
    """A 429 'Too many requests' response should raise a ValueError and set a quota timeout."""
    downloader = _build_downloader(monkeypatch)
    assert downloader.data_platform_quota_timeout is None

    def _mock_get_too_many(*args, **kwargs):  # type: ignore
        return _MockResponse(429, text="Too Many Requests")

    monkeypatch.setattr(requests, "get", _mock_get_too_many)

    with pytest.raises(ValueError) as exception_info:
        downloader.retrieve_file_and_size_list_for_dataset("some_dataset", "1.0", max_files=1)

    assert "exceeded your quota" in str(exception_info.value)
    assert downloader.data_platform_quota_timeout is not None


def test_init_continues_when_quota_exceeded(monkeypatch: pytest.MonkeyPatch):
    """Initialization should not fail when the validation request hits a quota-exceeded error."""
    monkeypatch.setenv("KNMI_DATA_PLATFORM_KEY", "dummy-access-key")

    def _mock_get_quota(*args, **kwargs):  # type: ignore
        return _MockResponse(403, text="Quota exceeded for this API key")

    monkeypatch.setattr(requests, "get", _mock_get_quota)

    downloader = KNMIDataPlatformDownloader()

    assert downloader is not None
    assert downloader.data_platform_quota_timeout is not None
