#!/usr/bin/env python
import cdsapi

dataset = "reanalysis-era5-single-levels"
request = {
    "product_type": ["reanalysis"],
    "variable": [
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "2m_dewpoint_temperature",
        "2m_temperature",
        "mean_sea_level_pressure",
        "mean_wave_direction",
        "mean_wave_period",
        "sea_surface_temperature",
        "significant_height_of_combined_wind_waves_and_swell",
        "surface_pressure",
        "total_precipitation"
    ],
    "year": ["2024"],
    "month": ["10"],
    "day": [
        "01", "02", "03",
        "04", "05", "06",
        "07", "08", "09"
    ],
    "time": [
        "00:00", "01:00", "02:00",
        "03:00", "04:00", "05:00",
        "06:00", "07:00", "08:00",
        "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00",
        "15:00", "16:00", "17:00",
        "18:00", "19:00", "20:00",
        "21:00", "22:00", "23:00"
    ],
    "data_format": "netcdf",
    "download_format": "unarchived",
    "area": [7.22, 50.75, 3.2, 53.7]
}

client = cdsapi.Client()
client.retrieve(dataset, request).download()