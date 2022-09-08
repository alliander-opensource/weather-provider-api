from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = """
# Weather Provider Library and API

This API is intended to help you fetch weather data from different data sources in an efficient and uniform way.
By just supplying a list of locations and a time window you can get data for a specific source immediately.

This project can currently be found on the following location:
https://github.com/alliander-opensource/Weather-Provider-API
"""

setup(
    name='weather_provider_api',
    version='v2.12.20',
    packages=find_packages(include=['weather_provider_api', 'weather_provider_api.*']),
    data_files=[('var_maps', ['var_maps/arome_var_map.json']),
                ('var_maps', ['var_maps/era5sl_var_map.json'])],
    scripts=[
        'weather_provider_api/scripts/erase_arome_repository.py',
        'weather_provider_api/scripts/erase_era5sl_repository.py',
        'weather_provider_api/scripts/update_arome_repository.py',
        'weather_provider_api/scripts/update_era5sl_repository.py',
        'weather_provider_api/main.py'
    ],
    install_requires=['accept_types==0.4.1',
                      'aiofiles~=0.7.0',
                      'beautifulsoup4~=4.9.3',
                      'cfgrib~=0.9.9.0',
                      'fastapi~=0.65.2',
                      'geopy~=2.1.0',
                      'lxml==4.9.1',
                      'netcdf4~=1.5.6',
                      'numpy~=1.21.5',
                      'pandas~=1.2.4',
                      'pydantic~=1.8.2',
                      'pytest==6.2.4',
                      'python-dateutil~=2.8.1',
                      'pytz~=2021.1',
                      'requests~=2.25.1',
                      'setuptools~=60.7.1',
                      'starlette~=0.14.2',
                      'starlette_prometheus~=0.7.0',
                      'structlog~=21.1.0',
                      'urllib3~=1.26.5',
                      'uvicorn~=0.14.0',
                      'xarray~=0.18.2'],
    url='https://github.com/alliander-opensource/Weather-Provider-API',
    license='Mozilla Public License 2.0',
    author='Raoul Linnenbank',
    author_email='weather.provider@alliander.com',
    description='Weather Provider API',
    long_description=long_description,
)
