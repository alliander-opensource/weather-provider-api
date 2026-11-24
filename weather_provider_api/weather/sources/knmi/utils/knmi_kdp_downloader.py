# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import os
from pathlib import Path
from typing import Final

from loguru import logger
from weather_provider_api.config import APP_CONFIG


class _Unset:
    """Sentinel type for constructor overrides that were not provided."""


_UNSET: Final = _Unset()
_SOURCE_CONSTRUCTOR_OVERRIDE: Final = "constructor override"
_SOURCE_ENVIRONMENT: Final = "environment"
_SOURCE_CLASS_CONFIGURATION: Final = "class configuration"


class KNMIDownloaderForKDP:
    """Class to handle KNMI Data Platform data downloads.

    ...
    """

    def __init__(
        self,
        *,
        _data_platform_url: str | None | _Unset = _UNSET,
        _data_platform_key: str | None | _Unset = _UNSET,
        _download_folder: str | Path | None | _Unset = _UNSET,
    ) -> None:
        """Initialize the downloader."""
        self.data_platform_url, self.data_platform_key, self.download_folder = self._read_parameters(
            _data_platform_url,
            _data_platform_key,
            _download_folder,
        )
        self.current_data_product_name: str | None = None
        self.current_data_product_version: str | None = None
        self.current_data_platform_key = self.data_platform_key
        self.current_download_folder = self.download_folder
        logger.info("KNMI Data Platform downloader initialized.")

    def change_current_data_product(
        self,
        dataset_name: str,
        dataset_version: str,
        *,
        data_platform_key: str | None | _Unset = _UNSET,
        download_folder: str | Path | None | _Unset = _UNSET,
    ) -> None:
        """Change the currently configured KNMI data product.

        This allows the downloader to switch between different data products without needing to create a new instance.
        """
        if data_platform_key is _UNSET:
            current_key = self.data_platform_key
            key_source = _SOURCE_CLASS_CONFIGURATION
        elif data_platform_key is None or isinstance(data_platform_key, str):
            current_key = data_platform_key
            key_source = _SOURCE_CONSTRUCTOR_OVERRIDE
        else:
            raise TypeError("data_platform_key must be a string or None.")

        if download_folder is _UNSET or download_folder is None:
            current_folder = self.download_folder
            folder_source = _SOURCE_CLASS_CONFIGURATION
        elif isinstance(download_folder, (str, Path)):
            current_folder = Path(download_folder)
            folder_source = _SOURCE_CONSTRUCTOR_OVERRIDE
        else:
            raise TypeError("download_folder must be a string, Path, or None.")

        self.current_data_product_name = dataset_name
        self.current_data_product_version = dataset_version
        self.current_data_platform_key = current_key
        self.current_download_folder = current_folder

        logger.info(
            "Current KNMI data product set to {}/{}; API key {} from {}; download folder {} from {}.",
            dataset_name,
            dataset_version,
            "configured" if current_key is not None else "not configured",
            key_source,
            current_folder,
            folder_source,
        )

    def download_data_product(self) -> None:
        """Download the data based on the given parameters for the currently configured KNMI data product.

        ...
        """
        ...

    @staticmethod
    def _read_parameters(
        data_platform_url_override: str | None | _Unset,
        data_platform_key_override: str | None | _Unset,
        download_folder_override: str | Path | None | _Unset,
    ) -> tuple[str, str | None, Path]:
        """Resolve constructor overrides, environment variables, and defaults."""
        data_platform_url = KNMIDownloaderForKDP._read_data_platform_url(data_platform_url_override)
        data_platform_key = KNMIDownloaderForKDP._read_data_platform_key(data_platform_key_override)
        download_folder = KNMIDownloaderForKDP._read_download_folder(download_folder_override)
        return data_platform_url, data_platform_key, download_folder

    @staticmethod
    def _read_data_platform_url(override: str | None | _Unset) -> str:
        """Resolve the required KNMI Data Platform URL."""
        source = _SOURCE_CONSTRUCTOR_OVERRIDE if override is not _UNSET else _SOURCE_ENVIRONMENT
        data_platform_url = os.environ.get("KNMI_DATA_PLATFORM_URL") if override is _UNSET else override

        if not isinstance(data_platform_url, str) or not data_platform_url:
            raise ValueError("KNMI_DATA_PLATFORM_URL must be set or provided as _data_platform_url.")
        logger.debug("KNMI Data Platform URL read from {}.", source)
        return data_platform_url

    @staticmethod
    def _read_data_platform_key(override: str | None | _Unset) -> str | None:
        """Resolve the optional KNMI Data Platform key."""
        source = _SOURCE_CONSTRUCTOR_OVERRIDE if override is not _UNSET else _SOURCE_ENVIRONMENT
        if override is _UNSET:
            data_platform_key = os.environ.get("KNMI_DATA_PLATFORM_KEY")
        elif override is None or isinstance(override, str):
            data_platform_key = override
        else:
            raise TypeError("_data_platform_key must be a string or None.")
        logger.debug(
            "KNMI Data Platform key {} from {}.",
            "configured" if data_platform_key is not None else "not configured",
            source,
        )
        return data_platform_key

    @staticmethod
    def _read_download_folder(override: str | Path | None | _Unset) -> Path:
        """Resolve the KNMI download folder."""
        download_folder = os.environ.get("KNMI_DATA_PLATFORM_DOWNLOAD_FOLDER") if override is _UNSET else override

        if download_folder is None:
            download_folder = APP_CONFIG.APP_DATA_STORAGE_FOLDER / "knmi"
            folder_source = "application storage default"
        elif isinstance(download_folder, (str, Path)):
            download_folder = Path(download_folder)
            folder_source = _SOURCE_CONSTRUCTOR_OVERRIDE if override is not _UNSET else _SOURCE_ENVIRONMENT
        else:
            raise TypeError("_download_folder must be a string, Path, or None.")

        logger.debug("KNMI download folder set to {} from {}.", download_folder, folder_source)
        return download_folder

    def configure_data_product(self) -> None:
        """Configure a KNMI data product."""
        raise NotImplementedError