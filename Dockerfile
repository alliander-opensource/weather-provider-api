# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# FROM python:3.9-slim  # For now we use the old one:
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

EXPOSE 8080

RUN apt-get update && apt-get install -y --no-install-recommends locales && rm -rf /var/lib/apt/lists/*
RUN sed -i -e 's/# en_US/en_US/' /etc/locale.gen && \
    sed -i -e 's/# nl_NL/nl_NL/' /etc/locale.gen && \
    locale-gen

ENV POETRY_VERSION=1.0.8

RUN pip install poetry==${POETRY_VERSION}

# Copy both relevant poetry files to the appropriate folder
WORKDIR /wpla
COPY poetry.lock pyproject.toml /wpla/

# Disable Poetry's virtualenv for the image as we only need the one environment
RUN poetry config virtualenvs.create false

# Install everything depending on the environment. If env variable PRODUCTION_ENV carries the value 1,
# we don't install dev items.
RUN poetry install --no-interaction --no-ansi $(test "$PRODUCTION_ENV" == 1 && echo "--no-dev")

COPY . /wpla

ENV GUNICORN_CMD_ARGS="--timeout=300"
ENV WEB_CONCURRENCY=3
ENV BIND="0.0.0.0:8080"
ENV PORT=8080
ENV LOG_LEVEL=INFO
ENV DEBUG=0
ENV DEPLOYED=1
