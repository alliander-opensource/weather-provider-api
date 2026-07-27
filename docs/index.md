<!--
SPDX-FileCopyrightText: 2021-2026 Alliander N.V.

SPDX-License-Identifier: MPL-2.0
-->
# Weather Provider Libraries & API Documentation

<img src="./assets/wpas_logo.svg" alt="Weather Provider Access Suite" width="320"/>

> **Note:** A successor to this project — **MeteoForge** — is currently under active development.
> See the MeteoForge section of this documentation for more information.

## Overview

The Weather Provider Libraries & API project provides a unified interface for accessing meteorological data across a wide range of datasets — requiring no prior knowledge of their structure or content.

## Primary Goals

The project enables users to:

- **Query** meteorological datasets for specific time periods and weather variables.
- **Normalise** retrieved data into a common, uniform format, enabling direct comparison across datasets where fields are equivalent.
- **Export** results in a wide variety of commonly used file formats, automatically flattening multi-dimensional data where required.
- **Translate** existing dataset output directly into the uniform data format and export it accordingly.

## Secondary Goals

Beyond core data access, the project aims to:

- **Lower the barrier for contributors** — developers with knowledge of unsupported datasets can implement their own compatible models and sources, guided entirely by the base classes, without prior familiarity with the WPL internals.
- **Support modular adoption** — users can install and use only the specific sources and models they need, while retaining the ability to scale up to multiple sources and connect to the Weather Provider API for a fully functional, customisable API deployment.
