#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import tempfile
from typing import Any

import xarray as xr
from loguru import logger
from starlette.responses import FileResponse

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    ScientificJSONResponse,
    WeatherContentRequestMultiLocationQuery,
    WeatherContentRequestQuery,
)


def return_file_or_text_response(
    unserialized_data: xr.Dataset,
    response_format: ResponseFormat,
    source_id: str,
    model_id: str,
    request: WeatherContentRequestQuery | WeatherContentRequestMultiLocationQuery,
    coords: list[tuple[float, float]],
) -> tuple[ScientificJSONResponse | FileResponse, str | None]:
    """Return a file or text response based on the provided response format and data.

    Args:
        unserialized_data (xr.Dataset):
            The data to be returned in the response.
        response_format (ResponseFormat):
            The format in which the response should be returned.
        source_id (str):
            The ID of the source for which the data is being returned.
        model_id (str):
            The ID of the model for which the data is being returned.
        request (WeatherContentRequestQuery | WeatherContentRequestMultiLocationQuery):
            The original request object containing query parameters.
        coords (list[tuple[float, float]]):
            A list of coordinates for which the data is being returned.
    """
    patched_unserialized_data = patch_unserialized_data(unserialized_data)

    match response_format:
        case ResponseFormat.csv:
            # Implement CSV response or call the appropriate function
            file_path = to_csv(patched_unserialized_data, coords)
            mime = "text/csv"
            extension = ".csv"
            return file_response(file_path, mime, source_id, model_id, request, extension), file_path
        case ResponseFormat.json:
            return json_response(patched_unserialized_data, coords)
        case ResponseFormat.json_dataset:
            return json_dataset_response(patched_unserialized_data)
        case ResponseFormat.netcdf4 | ResponseFormat.netcdf3:
            file_path = to_netcdf(patched_unserialized_data, response_format)
            mime = "application/x-netcdf4"
            extension = ".v4.nc"
            return file_response(file_path, mime, source_id, model_id, request, extension), file_path
        case _:
            raise NotImplementedError(f"Cannot create response for the {response_format.name} response format")


def file_response(
    file_path: str,
    mime: str,
    source_id: str,
    model_id: str,
    request: WeatherContentRequestQuery | WeatherContentRequestMultiLocationQuery,
    extension: str,
) -> FileResponse:
    """Create a FileResponse for the given file path, MIME type, and file name."""
    file_name = f"weather_{source_id}_{model_id}_{request.begin}-{request.end}{extension}".replace(" ", "T").replace(
        ":", ""
    )
    return FileResponse(file_path, media_type=mime, filename=file_name)


def patch_unserialized_data(unserialized_data: xr.Dataset) -> xr.Dataset:
    """Patch the unserialized data to ensure it is in the correct format for response generation."""
    # Ensure 'lat' and 'lon' are set as xindexes for selection
    if (
        "lat" in unserialized_data.coords
        and unserialized_data.coords["lat"].ndim > 0
        and not unserialized_data.xindexes.get("lat")  # type: ignore
    ):
        unserialized_data = unserialized_data.set_xindex("lat")  # type: ignore
    if (
        "lon" in unserialized_data.coords
        and unserialized_data.coords["lon"].ndim > 0
        and not unserialized_data.xindexes.get("lon")  # type: ignore
    ):
        unserialized_data = unserialized_data.set_xindex("lon")  # type: ignore

    return unserialized_data


def json_response(
    unserialized_data: xr.Dataset, coords: list[tuple[float, float]]
) -> tuple[ScientificJSONResponse, None]:
    """Convert the unserialized data to a JSON response format."""
    serialized_data: list[dict[str, Any]] = []
    for lat, lon in coords:
        data_point = unserialized_data.sel(lat=lat, lon=lon, method="nearest").to_dict()
        serialized_data.append(data_point)
    return ScientificJSONResponse(content=serialized_data), None


def json_dataset_response(unserialized_data: xr.Dataset) -> tuple[ScientificJSONResponse, None]:
    """Convert the unserialized data to a JSON dataset response format."""
    serialized_data: dict[str, Any] = unserialized_data.to_dict()
    return ScientificJSONResponse(content=serialized_data), None


def to_netcdf(unserialized_data: xr.Dataset, response_format: ResponseFormat) -> str:
    """Convert the unserialized data to a NetCDF file and return the file path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    file_path = temp_file.name
    if response_format == ResponseFormat.netcdf4:
        unserialized_data.to_netcdf(file_path, mode="w", format="NETCDF4", engine="netcdf4")  # type: ignore
    elif response_format == ResponseFormat.netcdf3:
        unserialized_data.to_netcdf(file_path, mode="w", format="NETCDF3_64BIT", engine="netcdf4")  # type: ignore
    else:
        raise NotImplementedError(f"Unsupported NetCDF format: {response_format.name}")
    return file_path


def to_csv(unserialized_data: xr.Dataset, coords: list[tuple[float, float]]) -> str:
    """Convert the unserialized data to a CSV file and return the file path."""
    csv_data: dict[str, Any] = {}
    columns: list[str] = []

    for i, coordinate in enumerate(coords):
        sliced_data = unserialized_data.sel(lat=coordinate[0], lon=coordinate[1], method="nearest")

        # Convert to DataFrame and then to CSV string (without header)
        df = sliced_data.to_dataframe().reset_index()
        # Add lat/lon columns if not present
        if "lat" not in df.columns:
            df["lat"] = coordinate[0]
        if "lon" not in df.columns:
            df["lon"] = coordinate[1]
        # Ensure 'time' is included if present
        if i == 0:
            # Start with all columns in the DataFrame
            columns = list(df.columns)
            # Ensure 'time', 'lat', 'lon' are at the front in order
            for col in ["time", "lat", "lon"]:
                if col in columns:
                    columns.remove(col)
            # Attach 'time', 'lat', 'lon' to the front
            columns = [col for col in ["time", "lat", "lon"] if col in df.columns] + columns

        # Reorder columns
        df = df[[col for col in columns if col in df.columns]]
        coordinate_data_as_csv = df.to_csv(index=False, header=False, float_format="%.4f")
        csv_data[serialize_coords(coordinate)] = coordinate_data_as_csv.strip()

    # Construct the CSV content
    header = ",".join(columns)
    body = "\n".join(csv_data.values())
    csv_content = f"{header}\n{body}"

    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write(csv_content)
        file_path = temp_file.name

    return file_path


def serialize_coords(coord: tuple[float, float]) -> str:
    """Serialize the coordinates into a string format for use as a key in the CSV data dictionary."""
    coord_str = ",".join([str(x) for x in coord])
    return coord_str
