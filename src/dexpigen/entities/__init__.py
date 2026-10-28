"""Dex extraction input layer: the pipeline's Entities, Dex graph and drawing size.

``check_extraction`` checks one extraction against the input contract;
``dex_to_model`` / ``dex_to_proteus`` convert it into a ``ConceptualModel`` /
Proteus XML with drawing graphics. This is the only package that uses
NetworkX; the ConceptualModel holds none.
"""

from dexpigen.entities.base import Entity
from dexpigen.entities.convert import DexConversion, dex_to_model, dex_to_proteus
from dexpigen.entities.equipment import EquipmentEntity
from dexpigen.entities.extraction import (
    DexExtraction,
    DexExtractionError,
    Direction,
    DrawingSize,
    NodeType,
    check_extraction,
)
from dexpigen.entities.segment import LineKind, SegmentEntity
from dexpigen.entities.symbol import SymbolEntity

__all__ = [
    "DexConversion",
    "DexExtraction",
    "DexExtractionError",
    "Direction",
    "DrawingSize",
    "EquipmentEntity",
    "Entity",
    "LineKind",
    "NodeType",
    "SegmentEntity",
    "SymbolEntity",
    "check_extraction",
    "dex_to_model",
    "dex_to_proteus",
]
