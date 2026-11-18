# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
FROM --platform=linux/amd64 ghcr.io/astral-sh/uv:0.11.21@sha256:6f1fa8fc4040ad7197d7e652057219871e5f6640abfe2b790f1419fdb2319e6b AS uv-image
FROM --platform=linux/amd64 python:3.13-slim-trixie@sha256:48d884813cf44e927cf64c5529dd630dd3b18338c6dc727991eef9b71e934a20 AS base-image

RUN apt-get update && \
    apt-get -y install --no-install-recommends libeccodes-dev libeccodes-tools && \
    rm -rf /var/lib/apt/lists/*

ENV ECCODES_DIR=/usr/src/eccodes
ENV ECMWFLIBS_ECCODES_DEFINITION_PATH=/usr/src/eccodes/share/eccodes/definitions

ARG APP_HOME=/app
COPY --from=uv-image /uv /uvx /bin/


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

COPY --chown=65532:65532 ./pyproject.toml ./uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --no-build

COPY --chown=65532:65532 ./weather_provider_api ./weather_provider_api
COPY --chown=65532:65532 ./var_maps ./var_maps

ENV PATH="$APP_HOME/.venv/bin:$PATH"
ENV FORWARDED_ALLOW_IPS="127.0.0.1,::1"

# --- DEV image --
FROM base-image AS dev-image

USER $APP_USER
CMD ["ls", "-l"]

# --- UVICORN image --
FROM base-image AS uvicorn-image

USER $APP_USER
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "weather_provider_api.core.application:WPLA_APPLICATION" ]

# --- GUNICORN image --
FROM base-image AS gunicorn-image

ENV WEB_CONCURRENCY=1

USER $APP_USER
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]
CMD ["gunicorn", "-k", "uvicorn_worker.UvicornWorker", "-b", "0.0.0.0:8000", "weather_provider_api.core.application:WPLA_APPLICATION", "--timeout", "180"]
