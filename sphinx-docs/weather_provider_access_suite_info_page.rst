.. coding=utf-8
.. SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
.. SPDX-License-Identifier: MPL-2.0

.. _Weather Provider Access Suite Info Page:

************************************************
Information on the Weather Provider Access Suite
************************************************

    "NOTE: The WPAS project is the successor to the Weather Provider API V2 project, and currently under development.
     Upon release to the public, the WPAS project components will all start versioning at 3.0.0 to reflect this."


======================================================================
The current status of development on the Weather Provider Access Suite
======================================================================

.. list-table:: Weather Provider Access Suite Development Status
   :widths: 10 20
   :header-rows: 1

   * - Project component
     - Development status
   * - weather-provider-api
     - Mostly complete, awaiting release of the libraries component for integration
   * - weather-provider-libraries
     - Core components complete and being re-integrated, ZARR file formatting and controller class redesign in progress.
       Data transformation and output formatting components are mostly complete.
   * - weather-provider-sources
     - Awaiting completion of the libraries component for integration. The sources component will be the last to be
       integrated into the WPAS project. Backwards compatibility with the Weather Provider API V2 project will be
       generated via the rebuilding of the old weather sources and models that existed there. These models will be
       callable from both their old V2 and new V3 endpoints, with the newer endpoints providing more functionality.


===================================================================================
How does the Weather Provider Access Suite differ from the Weather Provider API V2?
===================================================================================

The Weather Provider Access Suite (or WPAS) is a project that is built from scratch, based on the finding from users of
the original Weather Provider API V2 project, and a reevaluation of the project goals.

In its new form the WPAS project will be built with the same goals als the original project, but with a few key
differences in its execution:

* **The WPAS project will be built with a more transparent modular structure and far better code.**

  This will allow for easier integration of new sources and models, and will allow for the easy addition of new
  functionality to the project. Because the project is rebuilt from scratch with the "one function, one purpose"
  principle in mind, the code will be far easier to read and understand.

  This will also allow for easier debugging and testing of the project, while allowing external developers to more
  easily contribute to the project, either by adding new sources and models, or by adding new functionality to the
  project.

* **The WPAS project will be built with a more transparent and user-friendly API.**

  The API will be built with the same goals as the original project, but with a more user-friendly interface that will
  allow for easier access to the data that the project provides.

  Several new endpoint groups will also be added to the API with the purpose of allowing for easier access to stored
  data, and if activated, an endpoint group with the sole purpose of self-evaluation can also be activated.


* **The WPAS project will be built with a more transparent and user-friendly documentation.**

  The documentation will be built with the same goals as the original project, but with a more user-friendly interface
  that will allow for easier access to the data that the project provides.

  Several new articles will also be added to allow external developers to easily understand the project, and to allow
  them to more easily contribute to the project.

* **The WPAS project will be built with more efficiency in mind.**

  The project will be built with a more efficient codebase that will allow for easier integration of new sources and
  models, and will allow for the easy addition of new functionality to the project. Base reusable code and classes will
  also be developed with an eye on speed and memory efficiency.

  This will also allow external developers to contribute to the project more easily, as they wont need to guard memory
  usage or processing speed as much as they would have to with the original project.
