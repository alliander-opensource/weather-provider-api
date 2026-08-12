# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Tests for the KNMIDataPlatFormDownloadClient, focused on Data Platform quota handling."""

from datetime import UTC, datetime, timedelta

import pytest
import requests  # type: ignore

from weather_provider_api.routers.weather.sources.knmi.client.knmi_data_platform_downloader import (
    KNMIDataPlatFormDownloadClient,
)


class _MockResponse:
    """A minimal stand-in for a requests.Response object."""

    def __init__(
        self,
        status_code: int,
        text: str = "",
        json_data: dict | None = None,
        headers: dict[str, str] | None = None,
    ):  # type: ignore
        self.status_code = status_code
        self.text = text
        self._json_data = json_data if json_data is not None else {}
        self.headers: dict[str, str] = headers if headers is not None else {}

    def json(self):  # type: ignore
        return self._json_data


def _build_downloader(monkeypatch: pytest.MonkeyPatch) -> KNMIDataPlatFormDownloadClient:
    """Create a downloader instance with a mocked, successful validation request."""
    monkeypatch.setenv("KNMI_DATA_PLATFORM_KEY", "dummy-access-key")

    def _mock_get_ok(*args, **kwargs):  # type: ignore
        return _MockResponse(200, json_data={"files": [], "nextPageToken": None})

    monkeypatch.setattr(requests, "get", _mock_get_ok)
    return KNMIDataPlatFormDownloadClient()


def test_quota_exceeded_429_enters_timeout(monkeypatch: pytest.MonkeyPatch):
    """A 429 response should advance the quota timeout into the future and short-circuit the call."""
    downloader = _build_downloader(monkeypatch)
    # After construction the client is not in a quota timeout (timeout is set to 'now').
    assert downloader.on_quota_timeout is False

    def _mock_get_too_many(*args, **kwargs):  # type: ignore
        return _MockResponse(429, text="Too Many Requests", headers={"Retry-After": "3600"})

    monkeypatch.setattr(requests, "get", _mock_get_too_many)

    before = datetime.now(tz=UTC)
    result = downloader.retrieve_file_and_size_list_for_dataset("some_dataset", "1.0", max_files=1)

    # The call is aborted (returns None) and the client enters a quota timeout roughly one hour out.
    assert result is None
    assert downloader.on_quota_timeout is True
    assert downloader.data_platform_quota_timeout > before + timedelta(minutes=59)


def test_calls_skipped_while_in_quota_timeout(monkeypatch: pytest.MonkeyPatch):
    """While a quota timeout is active, requests must be skipped without hitting the network."""
    downloader = _build_downloader(monkeypatch)
    downloader.data_platform_quota_timeout = datetime.now(tz=UTC) + timedelta(hours=1)
    assert downloader.on_quota_timeout is True

    def _fail_if_called(*args, **kwargs):  # type: ignore
        raise AssertionError("No network request should be made while in a quota timeout.")

    monkeypatch.setattr(requests, "get", _fail_if_called)

    assert downloader.retrieve_file_and_size_list_for_dataset("some_dataset", "1.0", max_files=1) is None


def test_quota_exceeded_403_enters_timeout(monkeypatch: pytest.MonkeyPatch):
    """A 403 whose body reports 'Quota exceeded' should advance the quota timeout into the future."""
    downloader = _build_downloader(monkeypatch)
    assert downloader.on_quota_timeout is False

    def _mock_get_quota(*args, **kwargs):  # type: ignore
        return _MockResponse(
            403, text="Quota exceeded for this API key", headers={"Retry-After": "3600"}
        )

    monkeypatch.setattr(requests, "get", _mock_get_quota)

    before = datetime.now(tz=UTC)
    result = downloader.retrieve_file_and_size_list_for_dataset("some_dataset", "1.0", max_files=1)

    assert result is None
    assert downloader.on_quota_timeout is True
    assert downloader.data_platform_quota_timeout > before + timedelta(minutes=59)


def test_forbidden_403_does_not_enter_quota_timeout(monkeypatch: pytest.MonkeyPatch):
    """A 403 response should abort the call but must NOT advance the quota timeout."""
    downloader = _build_downloader(monkeypatch)
    original_timeout = downloader.data_platform_quota_timeout

    def _mock_get_forbidden(*args, **kwargs):  # type: ignore
        return _MockResponse(403, text="Access to this API has been disallowed")

    monkeypatch.setattr(requests, "get", _mock_get_forbidden)

    result = downloader.retrieve_file_and_size_list_for_dataset("some_dataset", "1.0", max_files=1)

    assert result is None
    assert downloader.data_platform_quota_timeout == original_timeout
    assert downloader.on_quota_timeout is False
