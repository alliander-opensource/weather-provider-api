#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""Base Model class.

An expansion of the PydanticBaseModel used to build each Weather Provider Base class.
"""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Minimal PydanticBaseMode expansion used in all base classes."""
    model_config = ConfigDict(from_attributes=True)
