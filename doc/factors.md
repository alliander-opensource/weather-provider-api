<!--
SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
SPDX-License-Identifier: MPL-2.0
-->

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
Cloud cover in 1/8 parts. 9: the sky is not possible.

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
