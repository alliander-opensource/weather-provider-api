# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import io
import tarfile
from pathlib import Path

import numpy as np
import pytest

from weather_provider_api.routers.weather.sources.knmi.utils import knmi_arome_process_tar_file as processor


def _make_tar_file(tar_file_path: Path) -> None:
    with tarfile.open(tar_file_path, "w") as archive:
        member = tarfile.TarInfo("nested/input_file")
        member.size = len(b"fake grib data")
        archive.addfile(member, io.BytesIO(b"fake grib data"))


def test_unpack_tar_file_flattens_nested_files(tmp_path: Path) -> None:
    """Test that archive directories are removed while extracting files."""
    tar_file = tmp_path / "input.tar"
    extraction_dir = tmp_path / "extracted"
    extraction_dir.mkdir()
    _make_tar_file(tar_file)

    processor._unpack_tar_file(tar_file, str(extraction_dir))  # type: ignore[reportPrivateUsage]

    assert (extraction_dir / "input_file").read_bytes() == b"fake grib data"
    assert not (extraction_dir / "nested").exists()


def test_unpack_tar_file_raises_for_invalid_archive(tmp_path: Path) -> None:
    """Test that invalid archives are reported as missing input files."""
    tar_file = tmp_path / "invalid.tar"
    tar_file.write_bytes(b"not a tar archive")

    with pytest.raises(FileNotFoundError, match="Could not unpack tar file"):
        processor._unpack_tar_file(tar_file, str(tmp_path / "extracted"))  # type: ignore[reportPrivateUsage]


def test_build_lat_lon_grid() -> None:
    """Test construction of regular latitude and longitude coordinates."""
    message = {
        "latitudeOfFirstGridPointInDegrees": 50,
        "latitudeOfLastGridPointInDegrees": 51,
        "longitudeOfFirstGridPointInDegrees": 4,
        "longitudeOfLastGridPointInDegrees": 5,
        "jDirectionIncrement": 1000,
        "iDirectionIncrement": 1000,
    }

    latitudes, longitudes = processor._build_lat_lon_grid(message)  # type: ignore[reportPrivateUsage]

    assert latitudes == [50.0, 51.0]
    assert longitudes == [4.0, 5.0]


def test_process_grib_message_to_dataset() -> None:
    """Test conversion of a supported GRIB message into an xarray dataset."""
    message = {
        "typeOfLevel": "heightAboveGround",
        "level": 0,
        "parameterName": "11",
        "stepType": "instant",
        "values": np.array([[280.0, 281.0], [282.0, 283.0]]),
        "latitudeOfFirstGridPointInDegrees": 50,
        "latitudeOfLastGridPointInDegrees": 51,
        "longitudeOfFirstGridPointInDegrees": 4,
        "longitudeOfLastGridPointInDegrees": 5,
        "jDirectionIncrement": 1000,
        "iDirectionIncrement": 1000,
    }

    dataset = processor._process_grib_message_to_dataset(message, "2026092200", 3)  # type: ignore[reportPrivateUsage]

    assert "surface_temperature" in dataset
    assert dataset.surface_temperature.values.tolist() == [[280.0, 281.0], [282.0, 283.0]]
    assert dataset.time.values[0] == np.datetime64("2026-09-22T03:00:00")
    assert np.unique(dataset.lat.values).tolist() == [50.0, 51.0]
    assert np.unique(dataset.lon.values).tolist() == [4.0, 5.0]


def test_process_grib_message_uses_unknown_factor_name() -> None:
    """Keep unmapped GRIB factors available under a stable fallback name."""
    message = {
        "typeOfLevel": "heightAboveGround",
        "level": 10,
        "parameterName": "unmapped-factor",
        "stepType": "accum",
        "values": np.array([[1.0]]),
        "latitudeOfFirstGridPointInDegrees": 50,
        "latitudeOfLastGridPointInDegrees": 50,
        "longitudeOfFirstGridPointInDegrees": 4,
        "longitudeOfLastGridPointInDegrees": 4,
        "jDirectionIncrement": 1000,
        "iDirectionIncrement": 1000,
    }

    dataset = processor._process_grib_message_to_dataset(message, "2026092200", 0)  # type: ignore[reportPrivateUsage]

    assert "10m_above_ground_unknown_code_unmapped-factor" in dataset


def test_process_grib_message_prefixes_step_type_for_underscore_factor() -> None:
    """Prefix mapped underscore factors with their GRIB step type."""
    message = {
        "typeOfLevel": "heightAboveGround",
        "level": 0,
        "parameterName": "181",
        "stepType": "accum",
        "values": np.array([[1.0]]),
        "latitudeOfFirstGridPointInDegrees": 50,
        "latitudeOfLastGridPointInDegrees": 50,
        "longitudeOfFirstGridPointInDegrees": 4,
        "longitudeOfLastGridPointInDegrees": 4,
        "jDirectionIncrement": 1000,
        "iDirectionIncrement": 1000,
    }

    dataset = processor._process_grib_message_to_dataset(message, "2026092200", 0)  # type: ignore[reportPrivateUsage]

    assert "surface_accum_rain_water" in dataset.data_vars


def test_convert_grib_files_in_alphabetical_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that GRIB files are converted in deterministic filename order."""
    for filename in ["b.grib", "a.grib"]:
        (tmp_path / filename).write_bytes(b"fake grib data")
    converted: list[str] = []

    def record_conversion(grib_file: Path, netcdf_directory: Path, datetime_tag: str) -> None:
        converted.append(grib_file.name)

    monkeypatch.setattr(processor, "_convert_grib_file_to_netcdf", record_conversion)

    processor._convert_grib_files_to_netcdf(str(tmp_path), "2026092200")  # type: ignore[reportPrivateUsage]

    assert converted == ["a.grib", "b.grib"]
    assert (tmp_path / "nc").is_dir()


def test_merge_netcdf_files_returns_none_when_directory_is_empty(tmp_path: Path) -> None:
    """Test that merging has an explicit empty-input result."""
    (tmp_path / "nc").mkdir()

    result = processor._merge_netcdf_files_in_directory(  # type: ignore[reportPrivateUsage]
        str(tmp_path), "merged.nc", "2026092200"
    )

    assert result is None


def test_convert_grib_file_skips_unsupported_grid_messages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ignore GRIB messages whose grid type cannot be represented."""
    grib_file = tmp_path / "forecast_003000_GB.grib"
    grib_file.touch()
    netcdf_directory = tmp_path / "nc"
    netcdf_directory.mkdir()

    class FakeStream:
        def items(self):
            return [("ignored", {"gridType": "reduced_gg"})]

    monkeypatch.setattr(processor.cfgrib, "FileStream", lambda path: FakeStream())

    processor._convert_grib_file_to_netcdf(grib_file, netcdf_directory, "2026092200")  # type: ignore[reportPrivateUsage]

    assert list(netcdf_directory.iterdir()) == []


def test_process_tar_file_returns_none_when_merge_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Return no output when conversion produces no mergeable files."""
    tar_file = tmp_path / "input.tar"
    target_directory = tmp_path / "target"
    target_directory.mkdir()
    _make_tar_file(tar_file)
    monkeypatch.setattr(processor, "_convert_grib_files_to_netcdf", lambda *args: None)
    monkeypatch.setattr(processor, "_merge_netcdf_files_in_directory", lambda *args: None)

    result = processor.process_knmi_arome_cy43_p1_tar_file_into_netcdf(
        tar_file, target_directory, "result.nc", "2026092200"
    )

    assert result is None


@pytest.mark.parametrize("error", [FileExistsError(), PermissionError(), FileNotFoundError(), OSError("failed")])
def test_move_merged_netcdf_file_returns_none_for_os_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: OSError
) -> None:
    """Convert move failures into an explicit no-result value."""
    source = tmp_path / "source.nc"
    source.touch()
    monkeypatch.setattr(processor.shutil, "move", lambda *args: (_ for _ in ()).throw(error))

    assert processor._move_merged_netcdf_file_to_target_location(source, tmp_path) is None  # type: ignore[reportPrivateUsage]


def test_process_tar_file_orchestrates_extraction_conversion_and_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test the top-level processor with GRIB conversion and merge isolated."""
    tar_file = tmp_path / "input.tar"
    target_directory = tmp_path / "target"
    target_directory.mkdir()
    _make_tar_file(tar_file)
    observed_grib_files: list[Path] = []

    def fake_conversion(temporary_directory: str, datetime_tag: str) -> None:
        observed_grib_files.extend(Path(temporary_directory).glob("*.grib"))

    def fake_merge(temporary_directory: str, target_name: str, datetime_tag: str) -> Path:
        merged_file = Path(temporary_directory) / "nc" / target_name
        merged_file.parent.mkdir(exist_ok=True)
        merged_file.write_bytes(b"merged netcdf")
        return merged_file

    monkeypatch.setattr(processor, "_convert_grib_files_to_netcdf", fake_conversion)
    monkeypatch.setattr(processor, "_merge_netcdf_files_in_directory", fake_merge)

    result = processor.process_knmi_arome_cy43_p1_tar_file_into_netcdf(
        tar_file, target_directory, "result.nc", "2026092200"
    )

    assert result == target_directory / "result.nc"
    assert result.read_bytes() == b"merged netcdf"
    assert [file.name for file in observed_grib_files] == ["input_file.grib"]