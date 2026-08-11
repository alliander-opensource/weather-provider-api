# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# Tests for the FastAPI initializers in weather_provider_api.core.initializers.
#
# To keep these tests scoped to the `core` package only, they never build or import the real application (which would
# mount the v1/v2 sub-APIs and thereby exercise other packages). Instead each test creates a throwaway FastAPI app and
# either inspects the middleware/handlers that were attached, or invokes the attached middleware dispatch directly.

import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount
from starlette_prometheus import PrometheusMiddleware

from weather_provider_api.app_version import APP_VERSION
from weather_provider_api.core.initializers import cors, headers, validation
from weather_provider_api.core.initializers.cors import (
    _normalize_origin_regex,
    initialize_cors_middleware,
)
from weather_provider_api.core.initializers.exception_handling import (
    handle_http_exception,
    initialize_exception_handler,
)
from weather_provider_api.core.initializers.headers import initialize_header_metadata
from weather_provider_api.core.initializers.mounting import mount_api_version
from weather_provider_api.core.initializers.prometheus import (
    initialize_prometheus_interface,
)
from weather_provider_api.core.initializers.rate_limiter import API_RATE_LIMITER
from weather_provider_api.core.initializers.validation import initialize_api_validation


def _make_request(path: str = "/") -> Request:
    """Build a minimal Starlette Request suitable for driving the middleware dispatch functions."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
        "root_path": "",
    }
    return Request(scope)


def _dispatch_of(app: FastAPI):
    """Return the dispatch callable of the last BaseHTTPMiddleware attached to the app."""
    return app.user_middleware[0].kwargs["dispatch"]


# --------------------------------------------------------------------------------------------------------------------
# headers.py
# --------------------------------------------------------------------------------------------------------------------
def test_initialize_header_metadata_adds_version_and_expiry_headers():
    """The metadata middleware should stamp the app version and validity headers onto responses."""
    app = FastAPI(title="test")
    initialize_header_metadata(app)

    async def call_next(_request):
        return Response("ok")

    response = asyncio.run(_dispatch_of(app)(_make_request(), call_next))

    assert response.headers["X-App-Version"] == APP_VERSION
    assert response.headers["X-App-Valid-Till"] == headers.APP_CONFIG["base"]["expiration_date"]


def test_initialize_header_metadata_adds_maintainer_headers_when_enabled(monkeypatch):
    """When maintainer info is enabled the maintainer headers should be added."""
    monkeypatch.setitem(headers.APP_CONFIG["maintainer"], "show_info", True)
    monkeypatch.setitem(headers.APP_CONFIG["maintainer"], "name", "Test Maintainer")
    monkeypatch.setitem(headers.APP_CONFIG["maintainer"], "email_address", "maintainer@example.com")

    app = FastAPI(title="test")
    initialize_header_metadata(app)

    async def call_next(_request):
        return Response("ok")

    response = asyncio.run(_dispatch_of(app)(_make_request(), call_next))

    assert response.headers["X-Maintainer"] == "Test Maintainer"
    assert response.headers["X-Maintainer-Email"] == "maintainer@example.com"


def test_initialize_header_metadata_omits_maintainer_headers_when_disabled(monkeypatch):
    """When maintainer info is disabled the maintainer headers should be absent."""
    monkeypatch.setitem(headers.APP_CONFIG["maintainer"], "show_info", False)

    app = FastAPI(title="test")
    initialize_header_metadata(app)

    async def call_next(_request):
        return Response("ok")

    response = asyncio.run(_dispatch_of(app)(_make_request(), call_next))

    assert "X-Maintainer" not in response.headers
    assert "X-Maintainer-Email" not in response.headers


# --------------------------------------------------------------------------------------------------------------------
# exception_handling.py
# --------------------------------------------------------------------------------------------------------------------
def test_initialize_exception_handler_registers_handler():
    """The initializer should register the custom handler for Starlette HTTP exceptions."""
    app = FastAPI(title="test")
    initialize_exception_handler(app)

    assert app.exception_handlers[StarletteHTTPException] is handle_http_exception


def test_handle_http_exception_builds_json_response_with_detail_and_url():
    """The handler should return a JSONResponse echoing the detail, status code and request URL."""
    exc = StarletteHTTPException(status_code=418, detail="teapot")

    response = asyncio.run(handle_http_exception(_make_request("/brew"), exc))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 418

    body = json.loads(response.body)
    assert body["detail"] == "teapot"
    assert body["request"] == "http://testserver/brew"


def test_handle_http_exception_includes_maintainer_when_enabled(monkeypatch):
    """When maintainer info is enabled the response body should include maintainer details."""
    import weather_provider_api.core.initializers.exception_handling as exception_handling

    monkeypatch.setitem(exception_handling.APP_CONFIG["maintainer"], "show_info", True)
    monkeypatch.setitem(exception_handling.APP_CONFIG["maintainer"], "name", "Test Maintainer")
    monkeypatch.setitem(exception_handling.APP_CONFIG["maintainer"], "email_address", "maintainer@example.com")

    response = asyncio.run(
        handle_http_exception(_make_request("/x"), StarletteHTTPException(status_code=404, detail="gone"))
    )
    body = json.loads(response.body)

    assert body["maintainer"] == "Test Maintainer"
    assert body["maintainer_email"] == "maintainer@example.com"


def test_handle_http_exception_omits_maintainer_when_disabled(monkeypatch):
    """When maintainer info is disabled the response body should not include maintainer details."""
    import weather_provider_api.core.initializers.exception_handling as exception_handling

    monkeypatch.setitem(exception_handling.APP_CONFIG["maintainer"], "show_info", False)

    response = asyncio.run(
        handle_http_exception(_make_request("/x"), StarletteHTTPException(status_code=404, detail="gone"))
    )
    body = json.loads(response.body)

    assert "maintainer" not in body
    assert "maintainer_email" not in body


# --------------------------------------------------------------------------------------------------------------------
# cors.py
# --------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("  https://example.com  ", "https://example.com"),
        ([], None),
        (["", "   "], None),
        ([1, 2, 3], None),
        (["https://a.com"], "(?:https://a.com)"),
        (["https://a.com", "https://b.com"], "(?:https://a.com)|(?:https://b.com)"),
        (["https://a.com", "", 5, "https://b.com"], "(?:https://a.com)|(?:https://b.com)"),
        (42, None),
    ],
)
def test_normalize_origin_regex(value, expected):
    """The regex normalizer should collapse config values into a single regex string (or None)."""
    assert _normalize_origin_regex(value) == expected


def test_initialize_cors_middleware_adds_middleware_for_explicit_origins(monkeypatch):
    """With explicit allowed origins the CORS middleware should be attached with those origins."""
    monkeypatch.setitem(cors.APP_CONFIG["components"], "cors_allowed_origins", ["https://example.com"])
    monkeypatch.setitem(cors.APP_CONFIG["components"], "cors_allowed_origins_regex", [])

    app = FastAPI(title="test")
    initialize_cors_middleware(app)

    cors_middleware = [m for m in app.user_middleware if m.cls is CORSMiddleware]
    assert len(cors_middleware) == 1
    assert cors_middleware[0].kwargs["allow_origins"] == ["https://example.com"]


def test_initialize_cors_middleware_adds_middleware_for_regex_only(monkeypatch):
    """With only a regex configured the CORS middleware should be attached using allow_origin_regex."""
    monkeypatch.setitem(cors.APP_CONFIG["components"], "cors_allowed_origins", [])
    monkeypatch.setitem(cors.APP_CONFIG["components"], "cors_allowed_origins_regex", ["https://.*\\.example\\.com"])

    app = FastAPI(title="test")
    initialize_cors_middleware(app)

    cors_middleware = [m for m in app.user_middleware if m.cls is CORSMiddleware]
    assert len(cors_middleware) == 1
    assert cors_middleware[0].kwargs["allow_origin_regex"] == "(?:https://.*\\.example\\.com)"
    assert "allow_origins" not in cors_middleware[0].kwargs


def test_initialize_cors_middleware_skips_when_nothing_configured(monkeypatch):
    """With neither origins nor a regex configured no middleware should be attached."""
    monkeypatch.setitem(cors.APP_CONFIG["components"], "cors_allowed_origins", [])
    monkeypatch.setitem(cors.APP_CONFIG["components"], "cors_allowed_origins_regex", [])

    app = FastAPI(title="test")
    initialize_cors_middleware(app)

    assert not any(m.cls is CORSMiddleware for m in app.user_middleware)


# --------------------------------------------------------------------------------------------------------------------
# mounting.py
# --------------------------------------------------------------------------------------------------------------------
def test_mount_api_version_mounts_child_and_attaches_exception_handler():
    """Mounting should add the child at its root_path and give the child the custom exception handler."""
    parent = FastAPI(title="parent")
    child = FastAPI(title="child", root_path="/api/vchild")

    mount_api_version(parent, child)

    mounts = [route for route in parent.routes if isinstance(route, Mount)]
    assert any(mount.path == "/api/vchild" for mount in mounts)
    assert child.exception_handlers[StarletteHTTPException] is handle_http_exception


# --------------------------------------------------------------------------------------------------------------------
# prometheus.py
# --------------------------------------------------------------------------------------------------------------------
def test_initialize_prometheus_interface_adds_default_metrics_route():
    """The Prometheus initializer should add its middleware and a default /metrics route."""
    app = FastAPI(title="test")
    initialize_prometheus_interface(app)

    assert any(m.cls is PrometheusMiddleware for m in app.user_middleware)
    assert "/metrics" in [route.path for route in app.routes]


def test_initialize_prometheus_interface_honours_custom_endpoint():
    """A custom metrics endpoint should be used for the exposed route."""
    app = FastAPI(title="test")
    initialize_prometheus_interface(app, metrics_endpoint="/custom-metrics")

    assert "/custom-metrics" in [route.path for route in app.routes]


# --------------------------------------------------------------------------------------------------------------------
# rate_limiter.py
# --------------------------------------------------------------------------------------------------------------------
def test_rate_limiter_is_a_configured_limiter():
    """The module should expose a ready-to-use slowapi Limiter instance."""
    assert isinstance(API_RATE_LIMITER, Limiter)


# --------------------------------------------------------------------------------------------------------------------
# validation.py
# --------------------------------------------------------------------------------------------------------------------
_PASSTHROUGH = Response("passthrough", status_code=299)


async def _passthrough_call_next(_request):
    return _PASSTHROUGH


def _validation_dispatch() -> object:
    app = FastAPI(title="test")
    initialize_api_validation(app)
    return _dispatch_of(app)


def test_validation_passes_through_non_api_requests():
    """Requests that do not target a versioned weather endpoint should pass through untouched."""
    dispatch = _validation_dispatch()

    response = asyncio.run(dispatch(_make_request("/"), _passthrough_call_next))

    assert response is _PASSTHROUGH


def test_validation_passes_through_valid_api_requests(monkeypatch):
    """A versioned weather request should pass through while both expiry dates are in the future."""
    monkeypatch.setitem(validation.APP_CONFIG["base"], "expiration_date", "2999-12-31")
    monkeypatch.setitem(validation.APP_CONFIG["api_v1"], "expiration_date", "2999-12-31")

    dispatch = _validation_dispatch()
    response = asyncio.run(dispatch(_make_request("/api/v1/weather"), _passthrough_call_next))

    assert response is _PASSTHROUGH


def test_validation_blocks_when_base_project_expired(monkeypatch):
    """An expired base project should yield a 404 mentioning the main project."""
    monkeypatch.setitem(validation.APP_CONFIG["base"], "expiration_date", "2000-01-01")
    monkeypatch.setitem(validation.APP_CONFIG["api_v1"], "expiration_date", "2999-12-31")

    dispatch = _validation_dispatch()
    response = asyncio.run(dispatch(_make_request("/api/v1/weather"), _passthrough_call_next))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert "main project" in json.loads(response.body)["detail"]


def test_validation_blocks_when_version_expired(monkeypatch):
    """An expired API version (with a valid base) should yield a 404 mentioning that version."""
    monkeypatch.setitem(validation.APP_CONFIG["base"], "expiration_date", "2999-12-31")
    monkeypatch.setitem(validation.APP_CONFIG["api_v1"], "expiration_date", "2000-01-01")

    dispatch = _validation_dispatch()
    response = asyncio.run(dispatch(_make_request("/api/v1/weather"), _passthrough_call_next))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    assert "v1 interface" in json.loads(response.body)["detail"]


def test_validation_blocks_when_both_expired(monkeypatch):
    """When both the base and the version are expired the message should mention both."""
    monkeypatch.setitem(validation.APP_CONFIG["base"], "expiration_date", "2000-01-01")
    monkeypatch.setitem(validation.APP_CONFIG["api_v1"], "expiration_date", "2000-01-01")

    dispatch = _validation_dispatch()
    response = asyncio.run(dispatch(_make_request("/api/v1/weather"), _passthrough_call_next))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 404
    detail = json.loads(response.body)["detail"]
    assert "main project" in detail
    assert "v1 interface" in detail
