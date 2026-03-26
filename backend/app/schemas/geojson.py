from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel


class Geometry(BaseModel):
    type: str
    coordinates: list[Any]


class Feature(BaseModel):
    type: str = "Feature"
    geometry: Geometry
    properties: dict[str, Any]


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[Feature]
