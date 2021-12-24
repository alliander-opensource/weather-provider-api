<!--
SPDX-FileCopyrightText: 2019-2021 Alliander N.V.

SPDX-License-Identifier: MPL-2.0
-->
[![License: MIT](https://img.shields.io/badge/License-MPL2.0-informational.svg)](https://github.com/alliander-opensource/Weather-Provider-API/blob/master/LICENSE)
<!--
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=alert_status)](https://sonarcloud.io/dashboard?id=alliander-opensource_Weather-Provider-API)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=alliander-opensource_Weather-Provider-API)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=security_rating)](https://sonarcloud.io/dashboard?id=alliander-opensource_Weather-Provider-API)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=vulnerabilities)](https://sonarcloud.io/dashboard?id=alliander-opensource_Weather-Provider-API)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=bugs)](https://sonarcloud.io/dashboard?id=alliander-opensource_Weather-Provider-API)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=alliander-opensource_Weather-Provider-API&metric=coverage)](https://sonarcloud.io/dashboard?id=alliander-opensource_Weather-Provider-API)
-->
# Weather Provider Libraries and API (WPLA)

The Weather Provider Library and API (or WPLA when abbreviated) is a modular system intended to help you fetch 
meteorological data from a multitude of different sources. It uses standardized input and output to help you get the 
information you need in the format you need, even when you know only the bare minimum of the source you want it from.

###**Notable Features:**
1. **The used modular design means you can access one or multiple sources from any level.**  
You can use a specific meteorological model directly from its WeatherModel class, a whole set of models from a single  
source from its WeatherSource class, and the full set of models from the WeatherController class. If you want to use  
all of this from multiple projects or interfaces, you can fully deploy the system as a fully functional API. 
2. **The standardization method used means you can gather data from a source with as little as a geographical location  
and a time frame.**  
WPLA will fill in the rest of the required data for you and even without a specific request for meteorological factors  
it will gather data for the most commonly used data from the requested model.
3. **Output as required**  
Regardless of the original format the model may return, WPLA will reformat that data to the file system and scientific  
system you want. The output file will even contain meta-data allowing you to feed a file back to WPLA to reformat it  
into another format, should you need to.

### **More information:**
If you wish to learn more about the Weather Provider Library and API (WPLA), this Open Source project can be found at:  
https://github.com/alliander-opensource/Weather-Provider-API

More information about the way WPLA works and how and why it was made, check out the recordings of our webinar:
[![Webinar Weather Provider API](https://img.youtube.com/vi/pjE0DZmSphQ/0.jpg)](https://www.youtube.com/watch?v=pjE0DZmSphQ)  
_Note about the webinar: The webinar was about version 2 of the Weather Provider Library and API, at the time still known as 
the Weather Provider API or WPA for short._





## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Contact
To contact the project owners directly please e-mail us at [weather.provider@alliander.com](mailto://weather.provider@alliander.com)
            
## Authors

This project was initially created by:

* **Tongyou Gu** - *Original API development*
* **Jeroen van de Logt** - *Functions in utilities*
* **Bas Niesink** - *Implementation weather REST API*
* **Raoul Linnenbank** - *Active API Development, Geo positioning, CDS ERA5, caching, remodeling, Harmonie Arome and optimisation*

Currently, this project is governed in an open source fashion, this is documented in [PROJECT_GOVERNANCE](PROJECT_GOVERNANCE.md).

## License

This project is licensed under the Mozilla Public License, version 2.0 - see LICENSE for details

## Licenses third-party code

This project includes third-party code, which is licensed under their own respective Open-Source licenses. SPDX-License-Identifier headers are used to show which license is applicable. The concerning license files can be found in the LICENSES directory. 

## Acknowledgments

Thanks to team Inzicht & Analytics and Strategie & Innovatie to
make this project possible.

A big thanks as well to Alliander for being the main sponsor for this open source project.  

And of course a big thanks to the guys of IT New Business & R&D to provide
such an easy-to-use Python environment in the cloud.
