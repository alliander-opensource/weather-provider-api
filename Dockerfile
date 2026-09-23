# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
FROM python:3.13-slim-bookworm AS base-image

RUN apt-get update && \
    apt-get -y install --no-install-recommends libeccodes-dev libeccodes-tools && \
    rm -rf /var/lib/apt/lists/*

ENV ECCODES_DIR=/usr/src/eccodes
ENV ECMWFLIBS_ECCODES_DEFINITION_PATH=/usr/src/eccodes/share/eccodes/definitions

ARG APP_HOME=/app
RUN pip install poetry


# Setup WPLA user and switch to WPLA user
ARG APP_USER=wpla-user
ARG APP_UID=65532
ARG APP_GID=65532

RUN groupadd --system --gid "$APP_GID" "$APP_USER" && \
    useradd --system \
      --uid "$APP_UID" \
      --gid "$APP_GID" \
      --create-home \
      --home-dir "$APP_HOME" \
      "$APP_USER"
WORKDIR $APP_HOME

USER $APP_USER

COPY --chown=65532:65532 ./pyproject.toml ./pyproject.toml
COPY --chown=65532:65532 ./weather_provider_api ./weather_provider_api
COPY --chown=65532:65532 ./var_maps ./var_maps

RUN poetry config virtualenvs.in-project true && \
    poetry install --no-interaction --no-ansi -v --no-root

ENV PATH="$APP_HOME/.venv/bin:$PATH"

# --- DEV image --
FROM base-image AS dev-image

USER $APP_USER
CMD ["ls", "-l"]

# --- UVICORN image --
FROM base-image AS uvicorn-image

USER $APP_USER
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/metrics || exit 1
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "weather_provider_api.core.application:WPLA_APPLICATION" ]

# --- GUNICORN image --
FROM base-image AS gunicorn-image

USER $APP_USER
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/metrics || exit 1
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "weather_provider_api.core.application:WPLA_APPLICATION", "--timeout", "180"]
