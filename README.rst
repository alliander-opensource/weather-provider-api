.. coding=utf-8
.. SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
.. SPDX-License-Identifier: MPL-2.0

.. image:: https://img.shields.io/badge/License-MPL2.0-informational.svg
   :target: https://github.com/alliander-opensource/weather-provider-libraries/LICENSE.md
   :alt: License: MIT
.. image:: https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_weather-provider-libraries&metric=alert_status
   :target: https://sonarcloud.io/summary/new_code?id=alliander-opensource_weather-provider-libraries
   :alt: Quality Gate Status
.. image:: https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_weather-provider-libraries&metric=sqale_rating
   :target: https://sonarcloud.io/summary/new_code?id=alliander-opensource_weather-provider-libraries
   :alt: Maintainability Rating
.. image:: https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_weather-provider-libraries&metric=security_rating
   :target: https://sonarcloud.io/summary/new_code?id=alliander-opensource_weather-provider-libraries
   :alt: Security Rating
.. image:: https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_weather-provider-libraries&metric=vulnerabilities
   :target: https://sonarcloud.io/summary/new_code?id=alliander-opensource_weather-provider-libraries
   :alt: Vulnerabilities
.. image:: https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_weather-provider-libraries&metric=bugs
   :target: https://sonarcloud.io/summary/new_code?id=alliander-opensource_weather-provider-libraries
   :alt: Bugs
.. image:: https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_weather-provider-libraries&metric=coverage
   :target: https://sonarcloud.io/summary/new_code?id=alliander-opensource_weather-provider-libraries
   :alt: Coverage

#############################
Weather Provider Access Suite
#############################

=================================================
An introduction to the Weather Provider Libraries
=================================================
.. image:: /docs/images/wpas_logo.svg
    :alt: Weather Provider Access Suite
    :align: center
    :width: 50%

---------------------------------------------
What is the Weather Provider Libraries (WPL)?
---------------------------------------------

^^^^^^^^^^^^
Project Goal
^^^^^^^^^^^^
The Weather Provider Libraries project is a project with a singular goal in mind::

    Easily accessing any data for a multitude of meteorological datasets and meteorological site-pages
    without any prior knowledge of those datasets or even their specific content.

That is right. Without any prior knowledge of a supported dataset itself, we want you to be able to achieve the
following:

* *Make requests for specific periods and meteorological factors.*
* *Transform the received data into one of several supported uniform formats, allowing for comparison of data between
  datasets if the fields are identical in nature.*
* *Transform the output for those requests into a wide number of commonly used file formats, flattening the output from
  multi-dimensional data as needed.*
* *Translate existing dataset output directly into the aforementioned supported uniform data and allow for outputting
  that result in the supported output file formats as well.*

**As a secondary goal, we also wish to achieve the following:**

*   For motivated people that have knowledge or affinity with unsupported datasets to build their own compatible model(s)
    and source(s) without prior knowledge of the WPL system by being guided by the base classes themselves.

*   Allow for the easy access and plugging of sources and models as desired. You can access the data you want to use
    without any need for installing more than just a singular source and calling more than just the model you need if
    that is what you need, while also retaining the possibility to upscale to a multitude of sources and models and
    even connect those to the `Weather Provider API`_ project for a fully functional API based on your wishes.

---------------
Project Origins
---------------
The Weather Provider Libraries Project, or WPL, as it will be abbreviated a lot in the documentation of this project,
is a project based on the original "**weather_provider_api**" project found at:

 `https://github.com/alliander-opensource/weather-provider-api/ <https://github.com/alliander-opensource/weather-provider-api/>`_

Until version 3.0 of this project, every component thereof was considered a part of a singular whole, but to allow for
easier usage and the easier building of new models and sources, the project was split up into three components:

**1. Weather Provider Libraries**

   This project and the part that holds all of the common components and tools responsible for formatting, processing
   and transforming meteorological data, as well as all of the base classes for creating Models and Sources for the
   project. Finally the project also houses the Controller which allows for easy configuration and acquisition of data
   over multiple sources and models.

**2. Weather Provider API**

   This project houses the API implementation of this project. It uses the Weather Provider Libraries project to
   transform any connected source and model into appropriate endpoints. This fully functional FastAPI implementation is
   fully supportive of the OpenAPI standard and can easily be scaled according to your wishes. The project repository
   even comes with a number of example deployment folders. The project can be used via custom deployment through its
   package or deployment using the readily available Docker images.
   For more information on this project please check the Project's repository page at: `Weather Provider API`_

**3. Weather Provider Sources**

   This project actually consists of multiple repositories. Each repository houses one or multiple Sources that can be
   installed as packages used separately or from a Weather Provider Libraries system. Each Source can house one or
   multiple Models, each representing a specific meteorological dataset, site-page with meteorological data, or fusion
   thereof.
   For a default set of Weather Provider Sources and a list of other known popular Sources

.. _Weather Provider API: https://github.com/alliander-opensource/weather-provider-api

-----------------
More information?
-----------------

for more information, please visit the GitHub Pages at:

https://alliander-opensource.github.io/weather-provider-libraries/