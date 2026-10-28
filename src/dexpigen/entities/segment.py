"""``SegmentEntity``: one drawn line segment, and its ``LineKind``."""

from enum import StrEnum

from dexpigen.entities.base import Entity, LineStringCoords


class LineKind(StrEnum):
    """The drawn style of a Dex graph line (see **Line kind** in ``CONTEXT.md``)."""

    PIPING = "piping"  # a process line; becomes piping
    SIGNAL_LINE = "signal-line"  # an instrument signal line
    DATA_LINE = "data-line"  # a data or software link, drawn with small circles


class SegmentEntity(Entity):
    """One drawn line segment; its ``id`` is the ``id`` attribute of its Dex graph edge.

    The pipeline puts the line kind into ``attributes["line_attributes"]["kind"]``;
    ``kind`` reads it from there.
    """

    geometry: LineStringCoords  # image pixels

    @property
    def label(self) -> str:
        return "segment"

    @property
    def kind(self) -> LineKind:
        """The segment's line kind; ``ValueError`` when it is missing or unknown."""
        line_attributes = self.attributes.get("line_attributes")
        value = line_attributes.get("kind") if isinstance(line_attributes, dict) else None
        if value is None:
            raise ValueError(f"SegmentEntity {self.id!r} has no line kind")
        try:
            return LineKind(value)
        except ValueError:
            raise ValueError(f"SegmentEntity {self.id!r} has unknown line kind {value!r}") from None
