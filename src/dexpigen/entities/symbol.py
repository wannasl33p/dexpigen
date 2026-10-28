"""``SymbolEntity``: a detected P&ID symbol such as a valve, nozzle or instrument."""

from dexpigen.entities.base import Entity, QuadCoords


class SymbolEntity(Entity):
    """A detected symbol: its coarse label is ``symbol_class``, its box is ``quad``.

    Nozzles, actuators, valves and the other symbol labels all use this class;
    the label decides the DEXPI class later.
    """

    symbol_class: str
    quad: QuadCoords  # 4 (x, y) corners, image pixels
    confidence: float = 1.0

    @property
    def label(self) -> str:
        return self.symbol_class
