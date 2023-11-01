#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
# SPDX-License-Identifier: MPL-2.0
#

# *** BASE IMAGE ***
FROM rflinnenbank/wpla-eccodes-ubuntu:latest as base-image

    # Copy the project requirements file to the proper location
WORKDIR $PYSETUP_PATH
COPY pyproject.toml ./

    # Install the runtime environment dependencies (The $POETRY_VIRTUALENVS_IN_PROJECT value ensures an environment)
RUN poetry install --no-interaction --no-ansi -vvv --without dev

WORKDIR /
COPY ./weather_provider_api ./weather_provider_api
COPY ./var_maps ./var_maps
COPY ./pyproject.toml ./pyproject.toml

# *** DEV IMAGE ***
# The purpose of this image is to supply the project as an interpreter / testing ground
FROM base-image as dev-image

    # Set working directory
WORKDIR /

# TODO: Add SSL interpreter interface

# *** GUNICORN IMAGE ***
# The purpose of this image is to supply the project with a gunicorn-run API
FROM base-image as uvicorn-image

WORKDIR /

EXPOSE 8000

CMD ["uvicorn", "--reload", "--host", "0.0.0.0", "--port", "8000", "weather_provider_api.__main__:app" ]

# *** UVICORN IMAGE ***
# The purpose of this image is to supply the project with a uvicorn-run API
FROM base-image as gunicorn-image

WORKDIR /

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "weather_provider_api.__main__:app", "--timeout", "180"]
