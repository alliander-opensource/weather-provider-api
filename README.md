<!--
SPDX-FileCopyrightText: 2021 Alliander N.V.
SPDX-License-Identifier: MPL-2.0
-->

[![WPLA: version](https://img.shields.io/badge/version-3.0.0a-blue)](https://github.com/alliander-opensource/Weather-Provider-API) [![License: MIT](https://img.shields.io/badge/License-MPL2.0-informational.svg)](https://github.com/alliander-opensource/Weather-Provider-API/blob/master/LICENSE) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=alliander-opensource_Weather-Provider-API) [![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=alliander-opensource_Weather-Provider-API) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=coverage)](https://sonarcloud.io/summary/new_code?id=alliander-opensource_Weather-Provider-API) ![Python Version](https://img.shields.io/pypi/pyversions/wpla) 

Weather Provider Libraries and API
==================================

_______________________________________________________________________

## Introduction

The Weather Provider Libraries and API is a set of libraries and an API shell that can be run as a whole or separately to gather and reformat meteorological data into an harmonized state, from which it can then be outputted in a multitude of file formats, coordinate systems and unit systems.

For the supported weather datasets and sources it becomes possible to gather specific data and change it into a desired format, even without prior knowledge of contents and formatting of the dataset itself..

## Table of contents

1. [What is the Weather Provider Libraries and API exactly?](#what-is-the weather-provider-libraries-and-api-exactly)
__________________________________________________________________________________________________
## What is the Weather Provider Libraries and API exactly?

As we stated in the introduction, the Weather Provider Libraries and API (or WPLA for short) is a set of libraries and an API shell that can be run as a whole or separately to gather and reformat meteorological data into an harmonized state, from which it can then be outputted in a multitude of file formats, coordinate systems and unit systems.

### ***But what does that mean?***

This means that the WPLA can be used and installed to match your specific needs. Depending on your intended use you can use what you need based on the situation:

| **Situation**                                                | **Installation suggested**                                   |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| You want to gather a lot of date from multiple meteorological sources, or set up an environment from which this can be done at any given time. | The full API (separately) or the controller (built into other code)*(certain sources may need to be installed separately)* |
| You want to incidentally gather data from multiple datasets created by a single source. | Install the package for that source and use it directly using its MeteoSource class. |
| You want to incidentally gather data from a single dataset.  | Install the package for that dataset and use it directly using its MeteoModel class. |

Regardless of the installation, there are no differences in the required input or methods.

### ***What is the required input?***

At minimum this models for this project can work with as little as:

- A geographical location or zone to gather data for
- A frame of time to gather the data for
- If multiple models or sources are available to the installation you are using, a specific model and source.

As a default the model will then return all of the meteorological factors that were set as default for the model in question and return them in a harmonized NetCDF4 file or Xarray dataset, depending on the method used for the request.

However, when you want more control this can easily be achieved by using the following other (optional) parameters:

- The desired meteorological factors
  *(These can be requested by using either their harmonized names or the original names used in the source data)*
- The desired unit system for the output
  *(currently this project supports the originally used unit system, the metric system (or 'human' system), the imperial system, and The International System of Units (or SI))*
- The desired file format for the output
  *(currently this project supports NetCDF4, NetCDF3, JSON, JSON dataset and CSV. Planned for the near future is support for HDF5)*

Finally, for more professional control, you can use the following parameters:

- The desired interpolation method (or lack thereof) to be used for value calculations when requesting locations in stead of zones.
- The returned locations can also be switched to match the nearest found data locations instead. This will overwrite the setting for the desired interpolation method, however.
- The used coordinate system for input if not the WGS84 standard. 
  *(any EPSG registered grid system can be used by referencing its numeric code. The data requested still needs to be available for the requested locations of course..)*
- The desired coordinate system to be used for the output.
  *(once again, any EPSG registered grid system can be used. The requested locations still need to be translatable to the new system of course..)*

## Installation as a package

#### Installing the full project:

**pip install wpla**

As with most packages on PyPI, it is possible to install a specific version if that is needed for some reason.

#### Installing a specific package of datasets

Go to the page that houses that package (likely a GitHub page) and follow the instructions provided there. 

Most of the time installations will be along the lines of:

**pip install wpla-<package-name>**

## Installation as a fully fledged API

There are three ways to install this project as a fully fledged API:

1. By installing the project package.
2. By cloning this repository and starting a FastAPI app with the project in it.
   *(for an example on this, check out the **api_main.py** file in the projects main folder)*
3. By launching this project's Docker image in an appropriate environment.

## Installing separate sources and models

Simply install the sources and models by installing their respective project packages and mount the models you wish to use by putting them into the modelconfig file.

Every MeteoModel should have  a base configuration from which it can run without any customization, so 

**TODO:** #################################################

## Meteorological factors per model

As each model has its own factors that can be requested every properly build model should have its own **MODEL_FACTORS.md** or **MODEL_FACTORS.rst** information file that comes with both its installation and repository.

This file should contain every available factor to the model, as well as its harmonized name and source unit.
___________________
## Contributing to this project

This project is Open Source and as such we welcome anyone willing to work on this project. If you wish to contribute, please read the [CONTRIBUTING.md](CONTRIBUTING.md) file in the root of this project for our code of conduct and the process of submitting pull requests to us.
___________________
## Contact

If you wish to contact the project owners directly, please e-mail us at:

[weather.provider@alliander.com](mailto://weather.provider@alliander.com).

___________________
## Notable Authors

This project made notable progress thanks to:

- Tongyou Gu - Who did the original API development
- Jeroen van de Logt - Who wrote a lot of the initial utility functions for the project
- Bas Niesink - Who implemented the initial REST API functionality, brought a lot of the code and data to its 1.0 release status and helped out deciphering the KNMI Harmonie Arome model.
- Raoul Linnenbank - Who has done most of the development for version 2.0 and is the current lead developer for the project.
___________________
## License

This project is licensed under the Mozilla Public License, version 2.0 - see [LICENSE.md](LICENSE.MD) for the details
___________________
## Third-party Code Licenses

This project includes third-party code, which is licensed under their own respective Open-Source licenses. SPDX-License-Identifier headers are used to show which license is applicable. The concerning license files can be found in the LICENSES directory.
___________________
## Acknowledgements

Thanks to teams "Inzicht & Analytics" and "Strategie & Innovatie" to make this project possible.

A big thanks as well to [Alliander](https://www.alliander.com) for being the main sponsor for this open source project.

And of course a big thanks to the guys of "IT New Business & R&D" to provide such an easy-to-use Python environment in the cloud.
