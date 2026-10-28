"""Shared base of the Dex extraction Entities: the ``Entity`` root and its coordinate types.

Every coordinate is in image (PNG) pixels with the y axis down, as the pipeline
produced it. Field names follow the pipeline's own (dexlib2-based) Entities, so
one of those converts with ``OurClass.model_validate(obj.model_dump())``.
"""

import math
from abc import ABC, abstractmethod
from typing import Annotated, Any
from uuid import uuid4

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer
from shapely import LineString, Polygon

XY = tuple[float, float]


def _points(value: Any) -> list[XY]:
    """Read a sequence of ``(x, y)`` points (lists, tuples or a numpy array).

    Raises ``ValueError`` (which pydantic reports as a ``ValidationError``) for
    anything that is not a sequence of finite number pairs.
    """
    if hasattr(value, "tolist"):  # a numpy array
        value = value.tolist()
    if not isinstance(value, list | tuple):
        raise ValueError(f"expected a sequence of (x, y) points, got {type(value).__name__}")
    points: list[XY] = []
    for point in value:
        if hasattr(point, "tolist"):  # a numpy row
            point = point.tolist()
        if not isinstance(point, list | tuple) or len(point) != 2:
            raise ValueError(f"a point must be an (x, y) pair, got {point!r}")
        try:
            x, y = float(point[0]), float(point[1])
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"a coordinate must be a number, got {point!r}") from None
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError(f"a coordinate must be finite, got {point!r}")
        points.append((x, y))
    return points


def _dump_points(coords: Any) -> list[list[float]]:
    return [[float(x), float(y)] for x, y in coords]


def _quad(value: Any) -> tuple[XY, ...]:
    points = _points(value)
    if len(points) != 4:
        raise ValueError(f"a quad has exactly 4 points, got {len(points)}")
    return tuple(points)


def _polygon(value: Any) -> Polygon:
    is_polygon = isinstance(value, Polygon)
    points = _points(list(value.exterior.coords)) if is_polygon else _points(value)
    if len(set(points)) < 3:
        raise ValueError("a polygon needs at least 3 distinct points")
    return value if is_polygon else Polygon(points)


def _line_string(value: Any) -> LineString:
    is_line = isinstance(value, LineString)
    points = _points(list(value.coords)) if is_line else _points(value)
    if len(points) < 2:
        raise ValueError("a line needs at least 2 points")
    return value if is_line else LineString(points)


# The 4 corners of a symbol box, dumped as a list of [x, y] like the pipeline's numpy quad.
QuadCoords = Annotated[
    tuple[XY, XY, XY, XY],
    BeforeValidator(_quad),
    PlainSerializer(_dump_points, return_type=list[list[float]]),
]
# A shapely Polygon, read from a ring of points (closing point optional) and dumped as its exterior ring.
PolygonCoords = Annotated[
    Polygon,
    BeforeValidator(_polygon),
    PlainSerializer(lambda polygon: _dump_points(polygon.exterior.coords), return_type=list[list[float]]),
]
# A shapely LineString, read from and dumped as a list of points.
LineStringCoords = Annotated[
    LineString,
    BeforeValidator(_line_string),
    PlainSerializer(lambda line: _dump_points(line.coords), return_type=list[list[float]]),
]


class Entity(ABC, BaseModel):
    """One extraction-time object of a Dex extraction (see **Entity** in ``CONTEXT.md``).

    ``id`` is the id of its node in the Dex graph or, for a ``SegmentEntity``,
    the ``id`` attribute of its edge. It defaults to a fresh UUID string, like
    the pipeline's, and is frozen. ``attributes`` is carried as the pipeline
    filled it and is not interpreted, except for a segment's line kind.
    Fields this class does not know (pipeline-only ones such as ``anchor`` or
    ``source_image``) are ignored.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True, extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    attributes: dict[str, Any] = Field(default_factory=dict)

    @property
    @abstractmethod
    def label(self) -> str:
        """The coarse label, e.g. ``equipment``, ``valve`` or ``segment``."""
