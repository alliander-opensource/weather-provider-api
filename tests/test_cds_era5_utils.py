# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest
import xarray as xr

import weather_provider_api.routers.weather.sources.cds.client.era5_utils as era5_utils
from weather_provider_api.routers.weather.sources.cds.client.cds_api_tools import CDSDataSets, CDSRequest


def test_file_requires_update_for_supported_file_states(tmp_path: Path) -> None:
    """Test update decisions for missing, incomplete, temporary, and finalized files."""
    file_path = tmp_path / "era5_2026_09"
    verification_date = date(2026, 9, 22)

    assert era5_utils.file_requires_update(file_path, date(2026, 9, 1), verification_date)

    file_path.with_suffix(era5_utils.Era5FileSuffixes.FORMATTED).touch()
    assert era5_utils.file_requires_update(file_path, date(2026, 9, 1), verification_date)
    file_path.with_suffix(era5_utils.Era5FileSuffixes.FORMATTED).unlink()

    file_path.with_suffix(era5_utils.Era5FileSuffixes.TEMP).touch()
    assert not era5_utils.file_requires_update(file_path, date(2026, 8, 1), verification_date)
    assert era5_utils.file_requires_update(file_path, date(2026, 5, 1), verification_date)
    file_path.with_suffix(era5_utils.Era5FileSuffixes.TEMP).unlink()

    file_path.with_suffix(era5_utils.Era5FileSuffixes.INCOMPLETE).touch()
    assert era5_utils.file_requires_update(file_path, date(2026, 9, 1), verification_date)
    file_path.with_suffix(era5_utils.Era5FileSuffixes.INCOMPLETE).unlink()

    file_path.with_suffix(".nc").touch()
    assert not era5_utils.file_requires_update(file_path, date(2026, 9, 1), verification_date)


@pytest.mark.parametrize(
    ("current_moment", "verification_date", "expected_suffix"),
    [
        (date(2026, 9, 1), date(2026, 9, 22), era5_utils.Era5FileSuffixes.INCOMPLETE),
        (date(2026, 7, 1), date(2026, 9, 22), era5_utils.Era5FileSuffixes.TEMP),
        (date(2025, 1, 1), date(2026, 9, 22), ".nc"),
    ],
)
def test_finalize_formatted_file_renames_by_retention_state(
    tmp_path: Path, current_moment: date, verification_date: date, expected_suffix: str
) -> None:
    """Test finalization into incomplete, temporary, and permanent filenames."""
    file_path = tmp_path / "era5_2026_09"
    formatted_file = file_path.with_suffix(era5_utils.Era5FileSuffixes.FORMATTED)
    formatted_file.touch()

    era5_utils._finalize_formatted_file(file_path, current_moment, verification_date)  # type: ignore[reportPrivateUsage]

    assert file_path.with_suffix(expected_suffix).exists()


def test_load_file_reads_existing_netcdf_and_rejects_missing_file(tmp_path: Path) -> None:
    """Test loading a NetCDF file and the missing-file error path."""
    file_path = tmp_path / "data.nc"
    xr.Dataset({"temperature": ("time", [280.0])}, coords={"time": [datetime(2026, 9, 22)]}).to_netcdf(file_path)

    loaded = era5_utils.load_file(file_path)

    assert loaded.temperature.values.tolist() == [280.0]
    with pytest.raises(FileNotFoundError):
        era5_utils.load_file(tmp_path / "missing.nc")


def test_format_downloaded_file_renames_factors_and_coordinates(tmp_path: Path) -> None:
    """Test formatting of a downloaded ERA5 dataset without an expver dimension."""
    file_path = tmp_path / "download.nc"
    dataset = xr.Dataset(
        {"temperature": (("valid_time", "latitude", "longitude"), np.ones((1, 1, 1)))},
        coords={
            "valid_time": [datetime(2026, 9, 22)],
            "latitude": [52.0],
            "longitude": [5.0],
        },
    )
    dataset.to_netcdf(file_path)

    era5_utils._format_downloaded_file(file_path, {"temperature": "air_temperature"})  # type: ignore[reportPrivateUsage]

    formatted = era5_utils.load_file(file_path)
    assert "air_temperature" in formatted
    assert "is_permanent_data" in formatted
    assert "lat" in formatted.coords
    assert "lon" in formatted.coords
    assert "time" in formatted.coords
    assert formatted.is_permanent_data.item() is True


def test_recombine_multiple_files_merges_required_zip_members(tmp_path: Path) -> None:
    """Test recombination of the required instantaneous and accumulated files."""
    archive_path = tmp_path / "era5.zip"
    instant_path = tmp_path / "instant.nc"
    accumulated_path = tmp_path / "accumulated.nc"
    coordinates = {"time": [datetime(2026, 9, 22)], "latitude": [52.0], "longitude": [5.0]}
    xr.Dataset(
        {
            "temperature": (("time", "latitude", "longitude"), np.ones((1, 1, 1))),
            "expver": ("time", [1]),
        },
        coords=coordinates,
    ).to_netcdf(instant_path)
    xr.Dataset(
        {
            "pressure": (("time", "latitude", "longitude"), np.ones((1, 1, 1))),
            "expver": ("time", [1]),
        },
        coords=coordinates,
    ).to_netcdf(accumulated_path)
    with ZipFile(archive_path, "w") as archive:
        archive.write(instant_path, "data_stream-oper_stepType-instant.nc")
        archive.write(accumulated_path, "data_stream-oper_stepType-accum.nc")

    era5_utils._recombine_multiple_files(archive_path)  # type: ignore[reportPrivateUsage]

    recombined = era5_utils.load_file(archive_path)
    assert "temperature" in recombined
    assert "pressure" in recombined
    assert "expver" not in recombined


def test_download_era5_data_delegates_to_cds_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test CDS download delegation and request serialization."""
    calls: list[dict] = []

    class FakeClient:
        def retrieve(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(era5_utils, "get_cds_client", lambda: FakeClient())
    request = CDSRequest(variables=["temperature"], year=["2026"], month=["09"], day=["22"], time=["00:00"])
    target_path = tmp_path / "era5.nc"

    era5_utils.download_era5_data(CDSDataSets.ERA5SL, request, str(target_path))

    assert calls == [
        {
            "name": CDSDataSets.ERA5SL.value,
            "request": request.request_parameters,
            "target": str(target_path),
        }
    ]


def test_download_era5_data_reraises_client_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that CDS client failures are logged and propagated."""
    class FailingClient:
        def retrieve(self, **kwargs):
            raise RuntimeError("download failed")

    monkeypatch.setattr(era5_utils, "get_cds_client", lambda: FailingClient())
    target_path = tmp_path / "era5.nc"

    with pytest.raises(RuntimeError, match="download failed"):
        era5_utils.download_era5_data(CDSDataSets.ERA5LAND, CDSRequest(variables=["temperature"]), str(target_path))


def test_download_month_builds_test_mode_request(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Request only the first day in test mode and all calendar days otherwise."""
    requests: list[CDSRequest] = []

    def fake_download(dataset: CDSDataSets, cds_request: CDSRequest, target_location: str) -> None:
        requests.append(cds_request)

    monkeypatch.setattr(era5_utils, "download_era5_data", fake_download)
    settings = era5_utils.Era5UpdateSettings(
        era5_dataset_to_update_from=CDSDataSets.ERA5LAND,
        era5_product_type="reanalysis",
        filename_prefix="era5land",
        target_storage_location=tmp_path,
        repository_time_range=(date(2026, 1, 1), date(2026, 9, 1)),
        factors_to_process=["temperature"],
        factor_dictionary={},
    )

    era5_utils._download_month(settings, date(2026, 9, 1), True, tmp_path / "month.nc")  # type: ignore[reportPrivateUsage]
    era5_utils._download_month(settings, date(2026, 9, 1), False, tmp_path / "month.nc")  # type: ignore[reportPrivateUsage]

    assert requests[0].day == ["1"]
    assert requests[1].day == [str(day) for day in range(1, 32)]


def test_prepare_downloaded_month_extracts_era5land_archive(tmp_path: Path) -> None:
    """Extract the data file from an ERA5-Land download archive."""
    archive_path = tmp_path / "month.nc"
    source_path = tmp_path / "data_0.nc"
    xr.Dataset({"temperature": ("time", [280.0])}, coords={"time": [datetime(2026, 9, 1)]}).to_netcdf(source_path)
    with ZipFile(archive_path, "w") as archive:
        archive.write(source_path, "data_0.nc")

    settings = era5_utils.Era5UpdateSettings(
        era5_dataset_to_update_from=CDSDataSets.ERA5LAND,
        era5_product_type=None,
        filename_prefix="era5land",
        target_storage_location=tmp_path,
        repository_time_range=(date(2026, 1, 1), date(2026, 9, 1)),
        factors_to_process=["temperature"],
        factor_dictionary={},
    )

    era5_utils._prepare_downloaded_month(settings, archive_path)  # type: ignore[reportPrivateUsage]

    assert era5_utils.load_file(archive_path).temperature.values.tolist() == [280.0]


def test_prepare_downloaded_month_delegates_era5sl_recombination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the ERA5-Single-Level recombination path for ERA5-SL downloads."""
    calls: list[Path] = []
    monkeypatch.setattr(era5_utils, "_recombine_multiple_files", lambda file: calls.append(file))
    settings = era5_utils.Era5UpdateSettings(
        era5_dataset_to_update_from=CDSDataSets.ERA5SL,
        era5_product_type=None,
        filename_prefix="era5sl",
        target_storage_location=tmp_path,
        repository_time_range=(date(2026, 1, 1), date(2026, 9, 1)),
        factors_to_process=["temperature"],
        factor_dictionary={},
    )

    era5_utils._prepare_downloaded_month(settings, tmp_path / "month.zip")  # type: ignore[reportPrivateUsage]

    assert calls == [tmp_path / "month.zip"]


def test_finalize_formatted_file_rejects_missing_formatted_file(tmp_path: Path) -> None:
    """Fail finalization when formatting did not produce the expected file."""
    with pytest.raises(FileNotFoundError):
        era5_utils._finalize_formatted_file(  # type: ignore[reportPrivateUsage]
            tmp_path / "era5_2026_09", date(2026, 9, 1), date(2026, 9, 22)
        )


def test_era5_update_month_skips_current_file_and_handles_update_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Skip finalized files and return failure when monthly processing raises."""
    settings = era5_utils.Era5UpdateSettings(
        era5_dataset_to_update_from=CDSDataSets.ERA5SL,
        era5_product_type=None,
        filename_prefix="era5sl",
        target_storage_location=tmp_path,
        repository_time_range=(date(2026, 1, 1), date(2026, 9, 1)),
        factors_to_process=["temperature"],
        factor_dictionary={},
    )
    (tmp_path / "era5sl_2026_09.nc").touch()
    assert era5_utils._era5_update_month(settings, date(2026, 9, 1), False) == era5_utils.RepoUpdateResult.SUCCESS  # type: ignore[reportPrivateUsage]

    (tmp_path / "era5sl_2026_09.nc").unlink()
    monkeypatch.setattr(era5_utils, "_download_month", lambda *args: (_ for _ in ()).throw(RuntimeError("failed")))
    assert era5_utils._era5_update_month(settings, date(2026, 9, 1), False) == era5_utils.RepoUpdateResult.FAILURE  # type: ignore[reportPrivateUsage]


def test_era5_update_month_by_month_includes_lower_bound_month(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Process the repository's oldest configured month when it is the current update month."""
    target_month = date(2026, 1, 1)
    settings = era5_utils.Era5UpdateSettings(
        era5_dataset_to_update_from=CDSDataSets.ERA5SL,
        era5_product_type=None,
        filename_prefix="era5sl",
        target_storage_location=tmp_path,
        repository_time_range=(target_month, date(2026, 9, 1)),
        factors_to_process=["temperature"],
        factor_dictionary={},
    )
    processed_months: list[date] = []
    monkeypatch.setattr(era5_utils, "_get_update_month", lambda _: target_month)
    monkeypatch.setattr(
        era5_utils,
        "_era5_update_month",
        lambda _settings, update_month, _test_mode: processed_months.append(update_month)
        or era5_utils.RepoUpdateResult.SUCCESS,
    )
    starting_moment = datetime.now(UTC)

    era5_utils._era5_update_month_by_month(  # type: ignore[reportPrivateUsage]
        settings,
        starting_moment,
        starting_moment + timedelta(hours=1),
        False,
    )

    assert processed_months == [target_month]