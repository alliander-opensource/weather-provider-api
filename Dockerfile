#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
# SPDX-License-Identifier: MPL-2.0
#

FROM python:3.10.13-bullseye AS base-image

RUN apt-get update &&  \
    apt-get -y install libeccodes-dev &&  \
    apt-get -y install libeccodes-tools &&  \
    apt-get clean

ENV ECCODES_DIR=/usr/src/eccodes
ENV ECMWFLIBS_ECCODES_DEFINITION_PATH=/usr/src/eccodes/share/eccodes/definitions

ARG APP_HOME=/app
RUN pip install poetry


# Setup WPLA user and switch to WPLA user
ARG APP_USER=wpla-user

RUN groupadd --system "$APP_USER" && \
    useradd --system --gid "$APP_USER" --create-home --home "$APP_HOME" "$APP_USER"

WORKDIR $APP_HOME

USER $APP_USER

COPY --chown=$APP_USER:$APP_USER ./pyproject.toml ./pyproject.toml
COPY --chown=$APP_USER:$APP_USER ./weather_provider_api ./weather_provider_api
COPY --chown=$APP_USER:$APP_USER ./var_maps ./var_maps

RUN poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi -v --no-root

ENV PATH="$APP_HOME/.venv/bin:$PATH"

# --- DEV image --
FROM base-image AS dev-image
# TODO: Hookup SSH interface

USER $APP_USER
CMD ["ls", "-l"]

# --- UVICORN image --
FROM base-image AS uvicorn-image

USER $APP_USER
EXPOSE 8000
CMD ["uvicorn", "--reload", "--host", "0.0.0.0", "--port", "8000", "weather_provider_api.core.application:WPLA_APPLICATION" ]

# --- GUNICORN image --
FROM base-image AS gunicorn-image

USER $APP_USER
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "weather_provider_api.core.application:WPLA_APPLICATION", "--timeout", "180"]
