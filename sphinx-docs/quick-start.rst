.. coding=utf-8

***************************************************
Getting Started with the Weather Provider Libraries
***************************************************

====================
Package installation
====================
To install the Weather Provider Libraries package you only need to install it using PyPi::

>  pip install weather-provider-libraries

*Please note that when building your own model(s) and source(s) you will need to use the base classes declared
within the package to allow them to be recognized and used by the API.*

==========================
Default Sources and Models
==========================
The Weather Provider Libraries (WPL) package will automatically install a number of sources and models natively
supported by the project. For a information on these sources, their models and their specific usage, please read the
documentation available at:

    `https://github.com/alliander-opensource/ <https://github.com/alliander-opensource/>`_

===========================================
Your first request using the WPL Controller
===========================================
When using WPL directly, rather than through the API, you'll be able to contact all configured and set models by using
the Controller. The controller can be either instantiated by using Python or called upon via one of the available
scripts.

.. code-block::
   :caption: **Python instantiation of the Controller:**

       from weather_provider_libraries.wpl_controller import WPLController

       controller = WPLController()

*Usually your IDE should be able to pick up on the possible requests and options available to this object. If unsure or
if you wish for more information, please check the module documentation as well.*


.. code-block::
   :caption: **Script activation of the controller:**

       python run wpl_controller_commands

*This script should retrieve a list of known WPL Controller commands that can be executed directly from the command line
and their accepted parameters*
