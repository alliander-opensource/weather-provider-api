#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import tempfile
from typing import List, Tuple, Union

import pandas as pd
import xarray
from starlette.responses import FileResponse

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    ScientificJSONResponse,
    WeatherContentRequestMultiLocationQuery,
    WeatherContentRequestQuery,
)


def file_or_text_response(
    unserialized_data: xarray.Dataset,
    response_format: ResponseFormat,
    source_id: str,
    model_id: str,
    request: Union[WeatherContentRequestQuery, WeatherContentRequestMultiLocationQuery],
    coords: List[Tuple[float, float]],
):
    if response_format == ResponseFormat.json:
        return json_response(unserialized_data, coords)
    elif response_format == ResponseFormat.json_dataset:
        return json_dataset_response(unserialized_data)
    else:
        return file_response(unserialized_data, response_format, source_id, model_id, request, coords)


def file_response(
    unserialized_data: xarray.Dataset,
    response_format: ResponseFormat,
    source_id: str,
    model_id: str,
    request: WeatherContentRequestQuery,
    coords: List[Tuple[float, float]],
):
    if response_format == ResponseFormat.netcdf4:
        file_path = to_netcdf4(unserialized_data)
        mime = "application/x-netcdf4"
        extension = ".v4.nc"
    elif response_format == ResponseFormat.netcdf3:
        file_path = to_netcdf3(unserialized_data)
        mime = "application/x-netcdf3"
        extension = ".v3.nc"
    elif response_format == ResponseFormat.csv:
        file_path = to_csv(unserialized_data, coords)
        mime = "text/csv"
        extension = ".csv"
    else:
        raise NotImplementedError(f"Cannot create file response for the {response_format.name} response format")

    file_name = generate_filename(source_id, model_id, request, extension)
    response = FileResponse(file_path, media_type=mime, filename=file_name)
    return response, file_path


def generate_filename(source_id: str, model_id: str, request: WeatherContentRequestQuery, extension: str):
    file_name = f"weather_{source_id}_{model_id}_{request.begin}-{request.end}{extension}".replace(" ", "T")
    return file_name


def to_netcdf4(unserialized_data: xarray.Dataset):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_path = temp_file.name
    unserialized_data.to_netcdf(path=temp_file_path, mode="w", format="NETCDF4", engine="netcdf4")
    return temp_file_path


def to_netcdf3(unserialized_data: xarray.Dataset):
    # SciPy handler used by Xarray for direct serialization to binary doesn't support v3. File-based one does.
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file_path = temp_file.name
    unserialized_data.to_netcdf(path=temp_file_path, format="NETCDF3_64BIT", engine="netcdf4")
    return temp_file_path


def to_csv(unserialized_data: xarray.Dataset, coords):
    csv_strings = {}
    cols = []

    for i, c in enumerate(coords):
        df = get_weather_slice_for_coords(c, unserialized_data)

        if i == 0:
            cols = list(df.columns.values)
            cols.remove("lat")
            cols.remove("lon")
            cols = ["lat", "lon"] + cols

        csv_str = df.to_csv(columns=cols, header=False, float_format="%.4f")
        csv_strings[serialize_coords(c)] = csv_str

    cols = ["time"] + cols

    header = ",".join(cols)
    body = "\n".join(csv_strings.values())
    payload = (header + "\n" + body).encode("utf-8")

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(payload)
    temp_file.close()

    return temp_file.name


def get_weather_slice_for_coords(coord, unserialized_data) -> pd.DataFrame:
    # We use .sel to create slices from the unserialized dataset
    # We then switch to a Pandas dataframe
    if isinstance(coord, list):
        coord = coord[0]
    weather = unserialized_data.sel(lat=coord[0], lon=coord[1], method="nearest")
    if weather.dims["time"] == 1:
        # Because a single moment in time can't be squeezed...
        df = weather.to_dataframe()
    else:
        # ... and multiple times need to be.
        df = weather.squeeze().to_dataframe()
    return df


def json_response(unserialized_data: xarray.Dataset, coords):
    serialized_data = []
    for coordinate in coords:
        df = get_weather_slice_for_coords(coordinate, unserialized_data)
        serialized_data.append(df.reset_index().to_dict(orient="records"))
    return ScientificJSONResponse(serialized_data), None


def json_dataset_response(unserialized_data: xarray.Dataset):
    data_dict = unserialized_data.to_dict()
    return ScientificJSONResponse(data_dict), None


def serialize_coords(coord):
    coord_str = ",".join([str(x) for x in coord])
    return coord_str
