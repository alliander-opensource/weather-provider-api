#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""Class to retrieve the current Weather Alert status according to the KNMI site"""

from enum import Enum

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import ProxyError, Timeout, TooManyRedirects
from urllib3 import Retry


class WeatherAlertCode(Enum):
    # Enum class with valid Weather Alert Codes
    green = "green"
    yellow = "yellow"
    orange = "orange"
    red = "red"


class WeatherAlert:
    """A class (not a Weather Model!) that parses the Weather Alert status from the KNMI site (Weeralarm)"""

    def __init__(self):
        self.id = "weatheralert"
        self.name = "KNMI Weather Alert"
        self.version = "0.8"
        self.url = "https://www.knmi.nl/nederland-nu/weer/waarschuwingen/"
        self.predictive = True
        self.provinces = (
            "drenthe",
            "friesland",
            "gelderland",
            "groningen",
            "flevoland",
            "limburg",
            "noord-brabant",
            "noord-holland",
            "overijssel",
            "utrecht",
            "zeeland",
            "zuid-holland",
        )  # The Dutch Provinces. Every province has its own page.

    def get_alarm(self):
        """A function that retrieves the current weather alarm stage for each of the Dutch provinces and puts those together into a formatted list of results (string-based).

        Returns:
            A list of strings holding all the provinces and their retrieved current alarm stages according to KNMI
        """
        alarm_list = []
        for province in self.provinces:
            # Every province is available from a different page, so we have to request all of them separately
            page_text = ""
            try:
                page = self._requests_retry_session().get(self.url + province)
                status_code = page.status_code
                page_text = page.text
            except Timeout:
                status_code = 408
            except ProxyError:
                status_code = 407
            except TooManyRedirects:
                status_code = 999

            append_string = self.process_page(page_text, status_code, province)
            alarm_list.append(append_string)
        return alarm_list

    @staticmethod
    def process_page(page_text: str, status_code: int, province: str) -> tuple[str, str]:
        """
        Parses the weather alert page for a province and retrieves its current alarm stage by finding the first div with class 'alert' and 'alert--<color>'.

        Args:
            page_text:      The response content retrieved while trying to download the page
            status_code:    The status code retrieved while trying to download the page.
            province:       The province associated with the url, status code and alarm stage.

        Returns:
            A tuple holding the province and a result-string for that province.
        """
        if status_code == 200 and page_text is not None:
            soup = BeautifulSoup(page_text, features="lxml")
            # Find the first div with class 'alert' and 'alert--<color>'
            alert_div = None
            for div in soup.find_all("div", class_=lambda c: c and "alert" in c):
                for class_name in div.get("class", []):
                    if class_name.startswith("alert--"):
                        color = class_name[len("alert--") :]
                        # Only accept valid colors
                        if color in set(item.value for item in WeatherAlertCode):
                            return province, color
                # If found a div with 'alert' but no valid color, continue searching
            # If no valid code was found return an invalid data message
            return province, "could not find expected data on page"
        elif status_code == 408:
            return province, "time out op loading page"
        elif status_code == 407:
            return province, "proxy error on loading page"
        else:
            return province, "page proved inaccessible"

    @staticmethod
    def _requests_retry_session(
        # A function for basic retrying of an url when it isn't accessible immediately.
        retries=8,
        backoff_factor=0.01,
        status_forcelist=(500, 502, 504),
        session=None,
    ) -> requests.Session:
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        return session
