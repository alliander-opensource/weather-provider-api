#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""A class to retrieve the current Weather Alert status according to the KNMI site."""

from enum import Enum
from html.parser import HTMLParser

from requests.exceptions import ProxyError, Timeout, TooManyRedirects
from requests.sessions import HTTPAdapter, Session
from urllib3 import Retry


class WeatherAlertCode(Enum):
    """Enum class with valid Weather Alert Codes."""
    green = "green"
    yellow = "yellow"
    orange = "orange"
    red = "red"


class WeatherAlert:
    """A class (not a Weather Model!) that parses the Weather Alert status from the KNMI site (Weeralarm)."""

    def __init__(self):
        """Initialize the WeatherAlert class with the necessary information and settings."""
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

    def get_alarm(self) -> list[tuple[str, str]]:
        """A function that retrieves the current weather alarm stage for each of the Dutch provinces and puts those together into a formatted list of results (string-based).

        Returns:
            A list of tuples holding all the provinces and their retrieved current alarm stages according to KNMI
        """
        alarm_list: list[tuple[str, str]] = []
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
        """Parse the weather alert page for a province and retrieve its current alarm stage.

        It does so by looking for a div with the class "alert" and "alert--<color>" (where color is the code of the alarm stage). 
        If it finds such a div, it returns the color as the alarm stage. If it doesn't find such a div, it returns an error message based on the status code.

        Args:
            page_text:      The response content retrieved while trying to download the page
            status_code:    The status code retrieved while trying to download the page.
            province:       The province associated with the url, status code and alarm stage.

        Returns:
            A tuple holding the province and a result-string for that province.
        """
        if status_code == 200 and len(page_text) > 0:
            color = extract_alert_color(page_text)
            if color in {item.value for item in WeatherAlertCode}:
                return province, color
            
            # If no valid code was found return an invalid data message
            return province, "No weather alert code could be found on the page"
        elif status_code == 408:
            return province, "There was a timeout while loading the page"
        elif status_code == 407:
            return province, "There was a proxy error while loading the page"
        else:
            return province, "page proved inaccessible"

    @staticmethod
    def _requests_retry_session(
        # A function for basic retrying of an url when it isn't accessible immediately.
        retries: int = 8,
        backoff_factor: float = 0.01,
        status_forcelist: tuple[int, ...] = (500, 502, 504),
        session: Session | None = None,
    ) -> Session:
        session = session or Session()
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


class AlertDivParser(HTMLParser):
    """A simple HTML parser to extract the alert color from the KNMI weather alert page."""
    def __init__(self):
        """Initialize the AlertDivParser class."""
        super().__init__()
        self.found_color = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle the start tag of HTML elements and look for a div with the class 'alert' and 'alert--<color>'.
        
        If it is, extract the color and store it in the found_color attribute.
        """
        if tag == "div":
            attrs_dict = dict(attrs)
            class_attr = str(attrs_dict.get("class", ""))
            classes = class_attr.split()
            if any("alert" in cls for cls in classes):
                for cls in classes:
                    if cls.startswith("alert--"):
                        color = cls[len("alert--") :]
                        self.found_color = color

def extract_alert_color(page_text: str) -> str | None:
    """Extract the alert color from the KNMI weather alert page using the AlertDivParser."""
    parser = AlertDivParser()
    parser.feed(page_text)
    return parser.found_color
