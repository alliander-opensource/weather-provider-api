import json

from weather_provider_api.core.application import WPLA_APPLICATION
from weather_provider_api.versions.v2 import app as v2_app



def generate_openapi_spec():
    """Generate OpenAPI specification and save it to a file."""
    spec = v2_app.openapi()
    with open("openapi.json", "w") as f:
        f.write(json.dumps(spec))


if __name__ == "__main__":
    generate_openapi_spec()
