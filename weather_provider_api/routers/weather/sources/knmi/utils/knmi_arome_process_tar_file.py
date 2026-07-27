# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import re
import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import cfgrib  # type: ignore[import]
import numpy as np
import pandas as pd
import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.sources.knmi.knmi_factors import arome_factors


def process_knmi_arome_cy43_p1_tar_file_into_netcdf(
    tar_file_path: Path,
    target_netcdf_file_path: Path,
    target_netcdf_file_name: str,
    datetime_tag: str,
) -> Path | None:
    """Process a singular KNMI AROME CY43 P1 prediction tar file into a netCDF file.

    Args:
        tar_file_path (Path): The path to the KNMI AROME CY43 P1 tar file.
        target_netcdf_file_path (Path): The path where the processed netCDF file will be saved.
        datetime_tag (str): A datetime tag associated with the prediction data.

    Returns:
        Path | None: The path to the processed netCDF file, or None if processing failed.

    """
    temporary_directory = tempfile.mkdtemp()

    # The first step is to extract the tar file and find the relevant GRIB files.
    _unpack_tar_file(tar_file_path, temporary_directory)

    # Rename the extracted files to ensure they have a .grib extension
    for file in Path(temporary_directory).glob("*"):
        if file.is_file() and not file.suffix:
            new_file_path = file.with_suffix(".grib")
            file.rename(new_file_path)
            logger.debug(f"Renamed extracted file {file} to {new_file_path}")

    # After unpacking into GRIB files, we convert these GRIB files into netCDF4 files.
    _convert_grib_files_to_netcdf(temporary_directory, datetime_tag)

    # After conversion we should merge the netCDF4 files into a single file
    merged_netcdf_file_path = _merge_netcdf_files_in_directory(
        temporary_directory, target_netcdf_file_name, datetime_tag
    )
    if merged_netcdf_file_path is None:
        logger.error(f"Failed to merge netCDF files in temporary directory: {temporary_directory}")
        return None

    # Finally, we move the merged netCDF file to the target location and return its path.
    merged_netcdf_file_path = _move_merged_netcdf_file_to_target_location(
        merged_netcdf_file_path, target_netcdf_file_path
    )

    # Cleanup the temporary directory and all its contents
    shutil.rmtree(temporary_directory)

    return merged_netcdf_file_path


def _unpack_tar_file(tar_file_path: Path, temporary_directory: str) -> None:
    """Unpack the given tar file into the specified temporary directory.

    Args:
        tar_file_path (Path): The path to the tar file to be unpacked.
        temporary_directory (str): The path to the temporary directory where the files will be extracted.

    """
    logger.info(f"Unpacking tar file: {tar_file_path} to temporary directory: {temporary_directory}")
    try:
        with tarfile.open(tar_file_path, "r") as tar:
            # Extract all files to the temporary directory, ignoring any directory structure in the tar file.
            for member in tar.getmembers():
                if member.isfile():  # Only extract files, ignore directories
                    member.name = Path(member.name).name  # Remove any directory structure
                    logger.debug(f"Extracting file: {member.name}")
                    tar.extract(member, path=temporary_directory)
    except tarfile.TarError as e:
        logger.error(f"Error unpacking tar file: {e}")
        raise FileNotFoundError(f"Could not unpack tar file: {tar_file_path}") from e

    logger.info(f"Successfully unpacked tar file: {tar_file_path} to temporary directory: {temporary_directory}")


def _convert_grib_files_to_netcdf(temporary_directory: str, datetime_tag: str) -> None:
    """Convert all GRIB files in the specified temporary directory to netCDF4 format.

    NetCDF4 files will be save in a /nc subdirectory within the temporary directory.

    Args:
        temporary_directory (str): The path to the temporary directory containing the GRIB files.
        datetime_tag (str): A datetime tag associated with the prediction data.

    """
    logger.info(f"Converting GRIB files in temporary directory: {temporary_directory} to netCDF4 format")

    # Create a subdirectory for the netCDF files
    netcdf_directory = Path(temporary_directory) / "nc"
    netcdf_directory.mkdir(exist_ok=True)

    # Find all GRIB files in the temporary directory
    grib_files = sorted(Path(temporary_directory).glob("*.grib"), key=lambda x: x.name)
    logger.debug(f"Found {len(grib_files)} GRIB files to convert (sorted alphanumerically)")

    for grib_file in grib_files:
        logger.debug(f"Converting GRIB file: {grib_file} to netCDF4 format")
        _convert_grib_file_to_netcdf(grib_file, netcdf_directory, datetime_tag)
        logger.debug(f"Finished converting GRIB file: {grib_file} to netCDF4 format")

    logger.info(f"Finished converting GRIB files in temporary directory: {temporary_directory} to netCDF4 format")


def _convert_grib_file_to_netcdf(grib_file: Path, netcdf_directory: Path, datetime_tag: str) -> None:
    """Convert a single GRIB file to netCDF4 format and save it in the specified netCDF directory.

    Args:
        grib_file (Path): The path to the GRIB file to be converted.
        netcdf_directory (Path): The path to the directory where the converted netCDF file will be saved.
        datetime_tag (str): A datetime tag associated with the prediction data.

    """
    # The filenames end with _0HH00_GB where HH is the hour of the prediction, so we can extract it from the filename.
    hour_predicted_by_file = int(grib_file.stem[-7:-5])

    grib_file_stream = cfgrib.FileStream(str(grib_file))

    netcdf_file_path = netcdf_directory / f"{grib_file.stem}_{datetime_tag}.nc"
    first_var = True

    for item in grib_file_stream.items():
        grib_message = item[1]  # Get the GRIB message from the stream item

        if grib_message["gridType"] != "regular_ll":
            logger.warning(f"Skipping GRIB message with unsupported grid type: {grib_message['gridType']}")
            continue

        # Convert the GRIB message to an xarray Dataset and merge it with the combined dataset
        message_dataset = _process_grib_message_to_dataset(
            grib_message,  # type: ignore[call-arg]
            datetime_tag,
            hour_predicted_by_file,
        )

        # Unstack if needed
        message_dataset = message_dataset.unstack("coord")
        # Write to netCDF: "w" for first, "a" for others
        mode = "w" if first_var else "a"
        message_dataset.to_netcdf(netcdf_file_path, format="NETCDF4", engine="netcdf4", mode=mode)  # type: ignore
        first_var = False

    logger.debug(f"Saved converted netCDF file: {netcdf_file_path}")


def _process_grib_message_to_dataset(
    grib_message: dict[str, Any], datetime_tag: str, hour_predicted_by_file: int
) -> xr.Dataset:
    """Process a single GRIB message and convert it to an xarray Dataset.

    Args:
        grib_message (dict): The GRIB message to be processed.
        datetime_tag (str): A datetime tag associated with the prediction data.
        hour_predicted_by_file (int): The hour of the prediction extracted from the GRIB file name.

    Returns:
        str:
            The field name for the data in the GRIB message, constructed based on the message's metadata.
        xr.Dataset:
            An xarray Dataset containing the data from the GRIB message, with appropriate coordinates and metadata.

    """
    # Establish the message's measurement level
    message_level_type = "_".join(re.findall("[A-Z][^A-Z]*", str(grib_message["typeOfLevel"]))).lower()  # type: ignore[union-attr]
    message_level_value = str(grib_message["level"])  # type: ignore[union-attr]

    # Process the messages weather factor
    weather_factor = str(grib_message["parameterName"])  # type: ignore[union-attr]
    if weather_factor in arome_factors:
        factor_field_name = arome_factors[weather_factor].strip()

        # If the factor field name starts with an underscore, we need to add the step type to it
        if factor_field_name.startswith("_"):
            factor_field_name = f"{grib_message['stepType']}{factor_field_name}"
    else:
        factor_field_name = f"unknown_code_{weather_factor}"

    # Add level information
    if message_level_value == "0" and message_level_type == "above_ground":
        field_name = f"surface_{factor_field_name}"
    else:
        field_name = f"{message_level_value}m_{message_level_type}_{factor_field_name}"

    # Calculate the predicted hour of the data by adding the hour predicted by the file to the date from the datetime
    # tag, which represents the time of prediction.
    predicted_hour: datetime = datetime.strptime(datetime_tag, "%Y%m%d%H") + pd.Timedelta(hours=hour_predicted_by_file)

    # Create the data for the dataset from the GRIB message
    lats, lons = _build_lat_lon_grid(grib_message)  # type: ignore[assignment]
    value_field_grid: np.ndarray = np.reshape(grib_message["values"], (len(lats), len(lons)))  # type: ignore[assignment]

    dataset_data_dict = {field_name: (["lat", "lon"], value_field_grid)}
    dataset_coords: dict[str, Any] = {
        "time_of_prediction": [datetime_tag],
        "time": [predicted_hour],
        "coord": pd.MultiIndex.from_product([lats, lons], names=["lat", "lon"]),
    }

    mindex_coords: xr.Coordinates = xr.Coordinates.from_pandas_multiindex(dataset_coords["coord"], "coord")
    dataset_coords.pop("coord")  # Remove the MultiIndex from coords
    message_dataset = xr.Dataset(data_vars=dataset_data_dict, coords=dataset_coords)
    message_dataset = message_dataset.assign_coords(coords=mindex_coords)
    message_dataset.time.encoding["units"] = "seconds since 1970-01-01T00:00:00Z"

    return message_dataset


def _build_lat_lon_grid(grib_message: dict[str, Any]) -> tuple[list[float], list[float]]:
    """Construct the latitude and longitude grid for a GRIB message with a 'regular_ll' grid type.

    This function uses an existing GRIB file to extract the dimensions of the 'regular_ll' grid and format
     those into a list of latitudes and a list of longitudes that together make up the grid.

    Args:
        grib_message:  The GRIB file to use to extract the grid dimensions from.
                        (This should be a GRIB message with a 'regular_ll' grid type)

    Returns:
        Tuple[list[float], list[float]]:
                Two lists, the first holding latitudes, and the second longitudes

    """
    # Try to import cfgrib and raise an error if it isn't properly installed.
    # Set the boundaries
    minimum_latitude = float(grib_message["latitudeOfFirstGridPointInDegrees"])
    maximum_latitude = float(grib_message["latitudeOfLastGridPointInDegrees"])

    minimum_longitude = float(grib_message["longitudeOfFirstGridPointInDegrees"])
    maximum_longitude = float(grib_message["longitudeOfLastGridPointInDegrees"])

    # And the step value needed to get all the inbetween values
    step_for_latitude = int(grib_message["jDirectionIncrement"])
    step_for_longitude = int(grib_message["iDirectionIncrement"])

    # Build the lists
    base_latitudes = list(
        range(  # We add the step-value to the max-value to include it itself.
            int(minimum_latitude * 1_000),
            int(maximum_latitude * 1_000 + step_for_latitude),
            step_for_latitude,
        )
    )
    base_longitudes = list(
        range(  # We add the step-value to the max-value to include it itself.
            int(minimum_longitude * 1_000),
            int(maximum_longitude * 1_000 + step_for_longitude),
            step_for_longitude,
        )
    )

    latitudes: list[float] = [x / 1_000 for x in base_latitudes]
    longitudes: list[float] = [y / 1_000 for y in base_longitudes]

    return latitudes, longitudes


def _merge_netcdf_files_in_directory(
    temporary_directory: str, target_netcdf_file_name: str, datetime_tag: str
) -> Path | None:
    """Merge all netCDF files in the specified temporary directory into a single netCDF file.

    The merged file will be saved in the same directory with a name based on the datetime tag.

    Args:
        temporary_directory (str):
                The path to the temporary directory containing the netCDF files (in a /nc subdirectory).
        target_netcdf_file_name (str):
                The name of the target netCDF file.
        datetime_tag (str):
                A datetime tag associated with the prediction data, used for naming the merged file.

    Returns:
        Path | None: The path to the merged netCDF file, or None if no files were found.

    """
    logger.info(f"Merging netCDF files in temporary directory: {temporary_directory} into a single file")

    netcdf_directory = Path(temporary_directory) / "nc"
    netcdf_files = list(netcdf_directory.glob("*.nc"))
    logger.debug(f"Found {len(netcdf_files)} netCDF files to merge")

    if not netcdf_files:
        logger.warning(f"No netCDF files found in directory: {netcdf_directory} to merge")
        return None

    combined_dataset = xr.open_mfdataset(  # type: ignore
        netcdf_files, combine="by_coords", engine="netcdf4", chunks={"time": 8}, data_vars="all"
    )

    encoding = {}
    for var in combined_dataset.data_vars:
        encoding[var] = {
            "zlib": True,
            "complevel": 4,  # 1-9, higher is more compression but slower
            "chunksizes": (1, 50, 50),  # (time, lat, lon) or adjust as needed
        }

    merged_netcdf_file_path = netcdf_directory / target_netcdf_file_name
    combined_dataset.to_netcdf(merged_netcdf_file_path, format="NETCDF4", engine="netcdf4", encoding=encoding)  # type: ignore

    logger.info(f"Finished merging netCDF files into: {merged_netcdf_file_path}")
    return merged_netcdf_file_path


def _move_merged_netcdf_file_to_target_location(temporary_file: Path, target_netcdf_file_path: Path) -> Path | None:
    """Move the merged netCDF file from the temporary directory to the target location.

    Args:
        temporary_file (Path):
                The path to the temporary merged netCDF file.

        target_netcdf_file_path (Path):
                The path including filename where the merged netCDF file should be moved to.

    Returns:
        Path | None: The path to the moved netCDF file, or None if the move was unsuccessful.
    """
    target_file_name: Path = target_netcdf_file_path / temporary_file.name

    try:
        shutil.move(str(temporary_file), str(target_file_name))
        logger.info(f"Moved merged netCDF file from {temporary_file} to {target_file_name}")
        return target_file_name
    except FileExistsError:
        logger.error(f"Target file already exists: {target_file_name}. Not overwriting.")
        return None
    except PermissionError:
        logger.error(f"Permission denied when moving file to: {target_file_name}")
        return None
    except FileNotFoundError:
        logger.error(f"Source or target file not found during move: {temporary_file} -> {target_file_name}")
        return None
    except OSError as e:
        logger.error(f"OS error when moving merged netCDF file: {e}")
        return None
