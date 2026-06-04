#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import json

from weather_provider_api.versions.v2 import app as v2_app


def generate_openapi_spec() -> None:
    """Generate OpenAPI specification and save it to a file."""
    spec = v2_app.openapi()
    with open("openapi.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(spec, ensure_ascii=False, indent=2))
