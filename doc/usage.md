<!--
SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
SPDX-License-Identifier: MPL-2.0
-->

# Weather API
The weather API provides historical and current weather measurements, and weather predictions. The data comes from various sources and models, such as KNMI Daggegevens, KNMI Harmonie, and CDS ERA5.

Since there are many differences between the sources and models, regarding both naming and the units in which features are described, this API aims to provide a uniform way to access and represent the weather features. In order to do so, where possible, weather factors are given the same label across sources and models. Additionaly, the user of the API can choose between the original variable units, SI units, and units which are easier to read and grasp for humans. Finally, the output format can be chosen and ranges from basic types such as JSON, to more advanced and specialized models like NetCDF.

## Usage
### Online client and specifications
The easiest way to try out the API and browse all available operations, is by using the [interactive online documentation](https://weather.appx.cloud/api/v1/docs). It contains a built-in client, which gives access to the full functionality of the API.

Naturally, the operations can be called from any HTTP-compatible client as well. This allows you to programmatically use the API in your applications. The API's [OpenAPI specification (v3)](https://weather.appx.cloud/api/v1/openapi.json) may come in handy to establish this connection.

### Retrieving weather data
To retrieve weather data, whether historical or predictive, a few parameters need to be provided to the API.

The `source_id` and `model_id` tell the API which dataset you want to query. The available sources and models can be retrieved using [this API call](https://weather.appx.cloud/api/v1/weather/sources). Possible values are, for instance, *knmi* as the `source_id` and *daggegevens* as the `model_id`.

A measurement or prediction time window must be provided as well. This is done by setting the `begin` and `end` values. Both need to be in the following date time format: `%m-%d-%Y %H:%M`. For example, `2019-01-31 04:00`, `2017-12-25 14:45`, and `2020-02-28 00:00` are valid values.

The location is needed as well and is described in *WGS84* format, by specifying latitude `lat` and longitude `lon`. The API selects the closest weather station or grid in a model for which data is available. The [interactive online documentation](https://weather.appx.cloud/api/v1/docs) is pre-filled with the latitude and longitude for *De Bilt*. In future versions of the API it will be possible to retrieve weather data for multiple locations in a single call.

The units and names of the various weather variables can be changed. SI units are returned by default but if preferred the original units and labels can be returned, or units which are easier to read for humans.

The format of the output can be chosen as well. The default is NetCDF4, which is great for weather data and can be read using e.g. the [Xarray](http://xarray.pydata.org/en/stable/generated/xarray.open_dataset.html) Python package and NASA's [Panoply](https://www.giss.nasa.gov/tools/panoply/).

Other formats are NetCDF3, JSON, and CSV. For JSON the default structure is a list of records, with a record of all weather factors for a given date and time. A second flavor is available is well, namely *json_dataset*, which stores all measurements in a list for each factor.

Finally, you have to option to specify a subset of the available features for retrieval, using the `factors` attribute. If you don't specify a list of features, all available ones are returned. Both the original feature names and their aliases can be used (and mixed) to describe which factors have to be selected. Additionally, for the KNMI Daggegevens and Uurgegevens the aliases listed [here](https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-een-script) can be used, to retrieve e.g. all temperature related factors, by specifying a single label.


## Sources

The list of sources and models accessible through the API can be retrieved by calling the `/sources` endpoint. This endpoint is always up-to-date, since it attains the list of models from the API itself.

The sources and models are listed below as well, but this list may be out of date.

All factors which can be retrieved by the API are listed in the *Weather factors* section.

### KNMI

Several [KNMI](https://knmi.nl/home) models are available, for both historical data and predictions.

#### Daggegevens
KNMI [Daggegevens](https://projects.knmi.nl/klimatologie/daggegevens/) contains historical weather data on a 1-day resolution. The data from 35 KNMI weather stations is availble. Measurements from the current day are not present in this data set.

#### Uurgegevens
KNMI [Uurgegevens](https://projects.knmi.nl/klimatologie/uurgegevens/) is similar to *Daggegevens*, but on a 1-hour resolution. Again, data from the current day isn't present in the data set. This is a limitation on the side of the KNMI.

#### Harmonie
KNMI [Harmonie](https://data.knmi.nl/datasets/harmonie_p1/0.2) contains predictions for the coming 48 hours. Only the current predictions can be retrieved at this time. In the future, we may store predictions, to be able to provide historical predictions.

The predictions are updated every 6 hours (at 00, 06, 12, and 18 o'clock UTC+00).

Geographical resolution is 0.037 grades west-east and 0.023 grades north-south.


#### Pluim
KNMI [Pluim](https://www.knmi.nl/nederland-nu/weer/waarschuwingen-en-verwachtingen/weer-en-klimaatpluim) contains predictions for the coming 14 days. For each day, four predictions are made, one for every 6 hours (00, 06, 12, and 18 o'clock). The data comes from 8 KNMI stations located in The Netherlands. It contains fewer variables than the other KNMI datasets.


### CDS

### ERA5 (coming soon!)

ERA5 is the fifth generation [ECMWF](https://www.ecmwf.int/) (European Centre for Medium Range Weather Forecast) atmospheric reanalysis of the global climate. ERA5 data released so far covers the period from 1979 to 2-3 months before the present. ERA5 provides worldwide data for temperature and pressure, wind (at 100 meter height), radiation and heat, clouds, evaporation and runoff, precipitation and rain, snow, soil (temperature and moisture at four depths), etc. The spatial resolution of the data set is approximately 80 km.

Details on the exact dataset used can be found [here](https://cds.climate.copernicus.eu/portfolio/dataset/reanalysis-era5-single-levels).


## Weather factors

### KNMI
#### Daggegevens
| Factor | Alias                                        | Original unit    | SI unit          | Human readable unit | Description                                                                     |
|--------|----------------------------------------------|------------------|------------------|---------------------|---------------------------------------------------------------------------------|
| TG     | temperature                                  | 0.1 °C           | K                | °C                  | 24-hour average temperature                                                     |
| TN     | temperature_min                              | 0.1 °C           | K                | °C                  | minimum temperature                                                             |
| TNH    | temperature_min_hour                         | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| TX     | temperature_max                              | 0.1 °C           | K                | °C                  | maximum temperature                                                             |
| TXH    | temperature_max_hour                         | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| T10N   | -                                            | 0.1 °C           | K                | °C                  | minimum temperature at 10 cm                                                    |
| T10NH  | -                                            | hour [1-4]       | hour [1-4]       | hour [1-4]          | 6 hour window in which respective factor was measured (e.g. 1 = 00:00-06:00 AM) |
| FG     | wind_speed                                   | 0.1 m/s          | m/s              | m/s                 | 24-hour average wind speed                                                      |
| FHN    | wind_speed_min                               | 0.1 m/s          | m/s              | m/s                 | minimum wind speed                                                              |
| FHNH   | wind_speed_min_hour                          | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| FHX    | wind_speed_max                               | 0.1 m/s          | m/s              | m/s                 | maximum wind speed                                                              |
| FHXH   | wind_speed_max_hour                          | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| FXX    | wind_gust_max                                | 0.1 m/s          | m/s              | m/s                 | maximum wind gust speed                                                         |
| FXXH   | wind_gust_max_hour                           | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| DDVEC  | wind_direction                               | °                | °                | °                   | vector mean wind direction (360=N, 270=W, 180=S, 90=E)                          |
| FHVEC  | -                                            | 0.1 m/s          | m/s              | m/s                 | vector mean wind speed                                                          |
| RH     | precipitation                                | 0.1 mm           | m                | mm                  | 24-hour precipitation sum                                                       |
| RHX    | precipitation_max                            | 0.1 mm           | m                | mm                  | maximum precipitation in one hour                                               |
| RHXH   | precipitation_max_hour                       | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| DR     | precipitation_duration                       | 0.1 h            | h                | h                   | precipitation duration                                                          |
| EV24   | -                                            | 0.1 mm           | m                | mm                  | referentiegewasverdamping (Makkink)                                             |
| UG     | humidity                                     | %                | fraction         | fraction            | 24-hour average air humidity                                                    |
| UN     | humidity_min                                 | %                | fraction         | fraction            | minimum air humidity                                                            |
| UNH    | humidity_min_hour                            | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| UX     | humidity_max                                 | %                | fraction         | fraction            | maximum air humidity                                                            |
| UXH    | humidity_max_hour                            | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| PG     | air_pressure                                 | 0.1 hPa          | Pa               | Pa                  | 24-hour average air pressure at sea-level                                       |
| PN     | air_pressure_min                             | 0.1 hPa          | Pa               | Pa                  | minimum air pressure at sea-level                                               |
| PNH    | air_pressure_min_hour                        | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| PX     | air_pressure_max                             | 0.1 hPa          | Pa               | Pa                  | maximum air pressure at sea-level                                               |
| PXH    | air_pressure_max_hour                        | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| VVN    | -                                            | class, see below | m                | m                   | minimum visibility                                                              |
| VVNH   | -                                            | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| VVX    | -                                            | class, see below | m                | m                   | maximum visibility                                                              |
| VVXH   | -                                            | hour [1-24]      | hour [1-24]      | hour [1-24]         | 1 hour window in which respective factor was measured (e.g. 1 = 00:00-01:00 AM) |
| NG     | cloud_cover                                  | class, see below | class, see below | class, see below    | 24-hour average cloud cover                                                     |
| Q      | global_radiation                             | J/cm^2           | J/m^2            | J/m^2               | global radiation                                                                |
| SQ     | sunlight_duration                            | 0.1 hour         | hour             | hour                | sunlight duration                                                               |
| SP     | percentage_of_max_possible_sunlight_duration | %                | fraction         | fraction            | percentage of the longest possible sunlight duration                            |


#### Uurgegevens
| Factor | Alias                  | Original unit    | SI unit          | Human readable unit | Description                                            |
|--------|------------------------|------------------|------------------|---------------------|--------------------------------------------------------|
| T      | temperature            | 0.1 °C           | K                | °C                  | 1-hour average temperature                             |
| T10N   | -                      | 0.1 °C           | K                | °C                  | minimum temperature at 10 cm                           |
| TD     | -                      | 0.1 °C           | K                | °C                  | dew point temperature at 1.5 m                         |
| FH     | wind_speed             | 0.1 m/s          | m/s              | m/s                 | 1-hour average wind speed                              |
| FF     | -                      | 0.1 m/s          | m/s              | m/s                 | average wind speed over last 10 minutes of past hour   |
| FX     | wind_speed_max         | 0.1 m/s          | m/s              | m/s                 | maximum wind speed in past hour                        |
| DD     | wind_direction         | °                | °                | °                   | vector mean wind direction (360=N, 270=W, 180=S, 90=E) |
| RH     | precipitation          | 0.1 mm           | m                | mm                  | 1-hour precipitation sum                               |
| DR     | precipitation_duration | 0.1 h            | h                | h                   | precipitation duration                                 |
| R      | rain_occurred          | bool             | bool             | bool                | 1 if rain has occurred                                 |
| S      | snow_occurred          | bool             | bool             | bool                | 1 if snow has occurred                                 |
| M      | fog_occurred           | bool             | bool             | bool                | 1 if fog has occurred                                  |
| O      | lightning_occurred     | bool             | bool             | bool                | 1 if lightning has occurred                            |
| Y      | icing_occurred         | bool             | bool             | bool                | 1 if icing has occurred                                |
| U      | humidity               | %                | fraction         | fraction            | 1-hour average air humidity                            |
| P      | air_pressure           | 0.1 hPa          | Pa               | Pa                  | 1-hour average air pressure at sea-level               |
| VV     | visibility             | class, see below | m                | m                   | visibility                                             |
| N      | cloud_cover            | class, see below | class, see below | class, see below    | 1-hour average cloud cover                             |
| Q      | global_radiation       | J/cm^2           | J/m^2            | J/m^2               | global radiation                                       |
| SQ     | sunlight_duration      | 0.1 hour         | hour             | hour                | sunlight duration                                      |
| WW     | -                      | class, see below | class, see below | class, see below    | weather code                                           |
| IX     | -                      | class, see below | class, see below | class, see below    | measurement method for the weather code                |



#### Harmonie
| Factor | Alias                  | Original unit    | SI unit          | Human readable unit | Description                                            |
|--------|------------------------|------------------|------------------|---------------------|--------------------------------------------------------|
| T      | temperature            | 0.1 °C           | K                | °C                  | 1-hour average temperature                             |
| T10N   | -                      | 0.1 °C           | K                | °C                  | minimum temperature at 10 cm                           |
| TD     | -                      | 0.1 °C           | K                | °C                  | dew point temperature at 1.5 m                         |
| FH     | wind_speed             | 0.1 m/s          | m/s              | m/s                 | 1-hour average wind speed                              |
| FF     | -                      | 0.1 m/s          | m/s              | m/s                 | average wind speed over last 10 minutes of past hour   |
| FX     | wind_speed_max         | 0.1 m/s          | m/s              | m/s                 | maximum wind speed in past hour                        |
| DD     | wind_direction         | °                | °                | °                   | vector mean wind direction (360=N, 270=W, 180=S, 90=E) |
| RH     | precipitation          | 0.1 mm           | m                | mm                  | 1-hour precipitation sum                               |
| DR     | precipitation_duration | 0.1 h            | h                | h                   | precipitation duration                                 |
| R      | rain_occurred          | bool             | bool             | bool                | 1 if rain has occurred                                 |
| S      | snow_occurred          | bool             | bool             | bool                | 1 if snow has occurred                                 |
| M      | fog_occurred           | bool             | bool             | bool                | 1 if fog has occurred                                  |
| O      | lightning_occurred     | bool             | bool             | bool                | 1 if lightning has occurred                            |
| Y      | icing_occurred         | bool             | bool             | bool                | 1 if icing has occurred                                |
| U      | humidity               | %                | fraction         | fraction            | 1-hour average air humidity                            |
| P      | air_pressure           | 0.1 hPa          | Pa               | Pa                  | 1-hour average air pressure at sea-level               |
| VV     | visibility             | class, see below | m                | m                   | visibility                                             |
| N      | cloud_cover            | class, see below | class, see below | class, see below    | 1-hour average cloud cover                             |
| Q      | global_radiation       | J/cm^2           | J/m^2            | J/m^2               | global radiation                                       |
| SQ     | sunlight_duration      | 0.1 hour         | hour             | hour                | sunlight duration                                      |
| WW     | -                      | class, see below | class, see below | class, see below    | weather code                                           |
| IX     | -                      | class, see below | class, see below | class, see below    | measurement method for the weather code                |



#### Pluim
| Factor                | Alias             | Original unit | SI unit | Human readable unit | Description                                                         |
|-----------------------|-------------------|---------------|---------|---------------------|---------------------------------------------------------------------|
| temperature           | temperature       | °C            | K       | °C                  | predicted temperature                                               |
| wind_speed            | wind_speed        | km/h          | m/s     | m/s                 | predicted wind speed                                                |
| wind_direction        | wind_direction    | °             | °       | °                   | predicted vector wind direction (360=N, 270=W, 180=S, 90=E)         |
| short_time_wind_speed | wind_speed_max    | km/h          | m/s     | m/s                 | predicted maximum wind speed                                        |
| precipitation         | precipitation     | mm            | m       | mm                  | predicted precipitation                                             |
| precipitation_sum     | precipitation_sum | mm            | m       | mm                  | predicted precipitation sum from the start of the prediction window |
| cape                  | cape              | J/kg          | kJ/kg   | kJ/kg               | convective available potential energy                               |



### KNMI weather factor classes

#### KNMI visibility classes
0: <100 m, 1:100-200 m, 2:200-300 m,..., 49:4900-5000 m, 50:5-6 km, 56:6-7 km, 57:7-8 km,..., 79:29-30 km, 80:30-35 km, 81:35-40 km,..., 89: >70 km)

#### KNMI cloud cover classes
Cloud cover in 1/8 parts. 9: the sky cannot be seen.

#### KNMI weather code
See this page for more information on KNMI weather codes: http://bibliotheek.knmi.nl/scholierenpdf/weercodes_Nederland

### CDS
#### ERA5
| Factor | Alias            | Original unit | SI unit  | Human readable unit | Description         |
|--------|------------------|---------------|----------|---------------------|---------------------|
| t2m    | temperature      | K             | K        | °C                  | temperature         |
| wind   | wind_speed       | m/s           | m/s      | m/s                 | wind speed          |
| tp     | precipitation    | m             | m        | mm                  | total precipitation |
| sp     | air_pressure     | Pa            | Pa       | Pa                  | air pressure        |
| tcc    | cloud_cover      | fraction      | fraction | fraction            | total cloud cover   |
| cdir   | global_radiation | J/m^2         | J/m^2    | J/m^2               | global radiation    |

## Authors
- Tongyou Gu
- Bas Niesink
- Jeroen van de Logt

## License
This project is licensed under the Mozilla Public License, version 2.0 - see the LICENSE directory for details

## Acknowledgments
Thanks to team Inzicht & Analytics and Strategie & Innovatie to make this project possible.

Big thanks to guys of IT New Business & R&D to provide such an easy-to-use Python environment in the cloud.
