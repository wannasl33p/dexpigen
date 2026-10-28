"""``EquipmentEntity``: a detected equipment outline."""

from dexpigen.entities.base import Entity, PolygonCoords


class EquipmentEntity(Entity):
    """A detected equipment outline; its coarse label is always ``equipment``."""

    polygon: PolygonCoords  # the outline, image pixels; self-intersection is not checked

    @property
    def label(self) -> str:
        return "equipment"
