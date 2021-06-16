#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='weather_provider_api',
    version='2.4.1',
    description=long_description,
    author='Raoul Linnenbank',
    author_email='weather.provider@alliander.com',
    url='https://github.com/alliander-opensource/Weather-Provider-API',

    packages=find_packages(include=['weather_provider_api', 'weather_provider_api.*']),
    package_data={'': ['*.json']},
    install_requires=requirements,
    tests_require=['pytest'],

    entry_points={
        'console_scripts': [
            'run-api=weather_provider_api.app.main:main',
            'update-arome-repo=weather_provider_api.scripts.update_arome_repository:main',
            'update-era5sl-repo=weather_provider_api.scripts.update_era5sl_repository:main',
            'erase-arome-repo=weather_provider_api.scripts.erase_arome_repository:main',
            'erase-era5sl-repo=weather_provider_api.scripts.erase_era5sl_repository:main',
        ]
    }

)
