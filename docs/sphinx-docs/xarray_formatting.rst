.. coding=utf-8
.. SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
.. SPDX-License-Identifier: MPL-2.0

***************************************
Xarray formatting your data for a model
***************************************

============
Introduction
============
The hardest thing to do when creating your own data for a model, will likely be the formatting into a proper Xarray
Dataset format. The reason for this is that a single meteorological dataset can often have multiple indexes, allowing
for one weather factor to be dependant on a lat/lon location and time alone, whereas another may also be dependant on
for instance height/depth or a prediction moment.

The reason we use Xarray for handling these datasets is exactly because a singular dataset can be so divided, and
because it is heavily based on the NetCDF file format, which was designed to deal with exactly this issue.

Having said that, we still have to lay the groundwork for proper storage of these different indexes.

This document wil show you how to load the most common meteorological dataset formats into a xarray dataset and how to
properly create the needed index settings to allow the WPL project to automatically handle harmonisation and formatting.

====================================
Loading your source data into Xarray
====================================
So you have downloaded meteorological from a dataset and wish to load it into Xarray for further handling by WPL.
What now?

That depends on the format you have ready to go. One of the reasons the WPL project was initiated was because of the
wide range of formatting and file systems used to stored and request meteorological data. Sometimes even from within a
singular source.

Fortunately this first step of loading data into Xarray can be easily handled:

If your data currently is already stored as a file or exists in memory as a Pandas Dataframe, GRIB, NetCDF or
similarly formatted multidimensional format, you can simply load your data by using the Xarray **load_dataset()** and
**load_dataarray()** methods or the xarray.Dataset methods **from_dict()** or **from_dataframe**.

This means that most properly formatted GRIB and NetCDF files can be loaded directly into Xarray after retrieving them,
while most more two-dimensional formats like for example CSV or JSON can easily be loaded by transforming them into
either dictionaries, or Pandas Dataframes, and them loading them into Xarray.

**Problems**
In this stage, there usually shouldn't be many problems, but the following problematic situations may arise:

- **A custom GRIB format was used and can't be loaded directly into Xarray.**
  GRIB isn't as much of a file format as it is a loose guideline for how you could store meteorological data inside of
  a file. As such, if the used format moves away too far from the regular usage, it can end up becoming unreadable for
  the xarray supported GRIB engine and possibly even most GRIB tools.
  This is basically a worst case scenario, as this usually means you will have to manually sift through GRIB lines and
  reformat them into another more readable format (like a Pandas Dataframe, a custom build Xarray Dataset, or even a
  properly formatted GRIB file.
- **Multi-dimensional complexity arises.**
  Sometimes having a lot of data with each its own settings and possibly its own dimensions can result in Xarray not
  being able to properly evaluate which indexes apply when, or how. Usually Xarray will inform you of the issue as best
  as possible, possibly even with suggested solutions, but at times you may have to resort to either initially
  separating the data and adjusting it for use in a single dataset, or flattening the data outright and fixing it from
  there.

==========
Indexation
==========
With your data now well and loaded into a Xarray Dataset, we're not quite there yet. To allow for easy use in the WPL
project, we 'll need to address indexation.

Each Xarray Dataset usable by the WPL project will have the following base indexation set:

**coord**
An indexation field consisting of the two field values "lat" and "lon", which represent the latitude and longitude
WGS84 grid references accordingly. Each measurement, prediction or value needs to be attached to a **coord**.

**time**
An indexation field representing the moment of time a measurement, prediction or value applies to. For clarity, in the
case of a prediction made at 2023-05-01 22:00 for the moment of 2023-06-01 00:00, the **time** field should hold the
2023-06-01 00:00 moment.

*<optional>* **prediction**
An optional indexation field used to hold the moment at which predictive data was conceived. For clarity, in the case
of a prediction made at 2023-05-01 22:00 for the moment of 2023-06-01 00:00, the **prediction** field should hold
the 2023-05-01 22:00 moment.

*<optional>* **height/depth/level**
A series of optional indexation fields used to hold an indication of level where multiple measurements apply for a
factor but at different heights, intensities or data-types. For instance, if air temperature is measured not only
at 2 meter above ground, but also at 10 meter above ground and 100 meter above ground, the same field would have three
"height" levels.
Please note that while we only name "height", "depth" and "level" here, other indexation names may apply depending on
the nature of the level indicated. Also please note that in the case mentioned just now in practice that the 2m above
ground temperature, while technically of the same type and unit as the 10m and 100m above ground temperatures, has its
own designation within the ECCODES parameter system,due to the 2m version being the standard for "temperature" in
general. As such make sure to check if multiple levels should apply for your situation.