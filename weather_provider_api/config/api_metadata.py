import tomllib
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ApiVersionMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    implementation: str
    expiration_date: date


class ApiMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    base_expiration_date: date
    api_v1: ApiVersionMetadata
    api_v2: ApiVersionMetadata


def load_api_metadata(path: Path) -> ApiMetadata:
    with path.open("rb") as file:
        raw = tomllib.load(file)

    return ApiMetadata(
        base_expiration_date=raw["base"]["expiration_date"],
        api_v1=raw["api_v1"],
        api_v2=raw["api_v2"],
    )


ApiRouteVersion = Literal["v1", "v2"]
