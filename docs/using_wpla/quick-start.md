<!--
SPDX-FileCopyrightText: 2021-2026 Alliander N.V.

SPDX-License-Identifier: MPL-2.0
-->
# Getting Started with the Weather Provider Libraries and API

## Package Installation

To install the Weather Provider Libraries and API package, simply install it via PyPI:

```bash
pip install weather-provider-api
```

> *Please note that when building your own model(s) and source(s) you will need to use the base classes declared within the package to allow them to be recognised and used by the API.*

## Default Sources and Models

The Weather Provider Libraries (WPL) package automatically installs a number of natively supported sources and models. For information on these sources, their models, and their specific usage, please refer to the documentation at:

[https://github.com/alliander-opensource/](https://github.com/alliander-opensource/)

## Your First Request Using the WPL Controller

When using WPL directly — rather than through the API — all configured models can be accessed via the Controller. The Controller can be instantiated in Python or invoked via one of the available scripts.

**Python instantiation of the Controller:**

```python
from weather_provider_api.routers.weather.controller import WeatherController
from weather_provider_api.routers.weather.base_models.model import OutputUnit

controller = WeatherController()
sources = controller.get_sources()  # get a list of supported sources
models = controller.get_models(source_id='knmi') # get a list of supported models for the source 'knmi'
weather_data = controller.get_weather(
    source_id='knmi',  # source
    model_id='daggegevens',  # model
    coords=[(52.0, 5.0), (51, 4.8)],  # coordinates (at least one)
    begin='2024-01-01',  # start date
    end='2024-01-02',  # end date
    factors=['temperature', 'precipitation']  # (optional) weather factors to retrieve
)  # get weather data for the specified source and model

# Conversion to other unit systems:
weather_data_converted_to_si = controller.convert_names_and_units(
    source_id='knmi',  # source
    model_id='daggegevens',  # model
    data=weather_data,  # the data to convert
    unit=OutputUnit.si  # the unit system to convert to
)

# Saving as your preferred file type:
from weather_provider_api.routers.weather.api_models import WeatherContentRequestMultiLocationQuery
from weather_provider_api.routers.weather.utils.serializers import return_file_or_text_response, ResponseFormat

return_file_or_text_response(
    unserialized_data=weather_data_converted_to_si,
    response_format=ResponseFormat.json_dataset,
    source_id='knmi',
    model_id='daggegevens',
    request=WeatherContentRequestMultiLocationQuery(
        begin='2024-01-01',
        end='2024-01-02',
        locations=str([(52.0, 5.0), (51, 4.8)]),
        factors=['temperature', 'precipitation']
    ),
    coords=[(52.0, 5.0), (51, 4.8)]
)

```
> *Your IDE should be able to suggest the available requests and options on this object. For more detail, see the module documentation.*

The system is entirely modular, so the get_weather method can be called with any combination of source, model or
coordinates and the system will return the requested data in a structured format.
