"""Shared base layer for the DEXPI 1.3 in-memory conceptual model."""

from typing import Annotated, Any, ClassVar, Final, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Relation:
    """Marker for the relation a model-typed field expresses.

    Used as ``Annotated`` metadata on every field typed with a
    ``DexpiBaseModel`` subclass (bare, in ``list[...]`` or ``| None``):

    - ``Composed``: the field owns its value (a **Composition**); the serializer
      nests it as a child element.
    - ``Ref``: the field points at an object owned elsewhere (a **Reference**);
      the serializer writes an ``Association`` or an ID attribute.

    The markers carry no runtime behaviour of their own; they make the relation
    explicit for readers, the generated class index and the model checks.
    """

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name


Composed: Final = Relation("Composed")
Ref: Final = Relation("Ref")


def relation_of(metadata: list[Any]) -> Relation | None:
    """Return the ``Composed``/``Ref`` marker in a field's metadata, if any."""
    for item in metadata:
        if isinstance(item, Relation):
            return item
    return None


class CustomAttribute(BaseModel):
    """A generic name/value entry in the DEXPI customization bag.

    Mirrors a Proteus ``<GenericAttribute>``: an arbitrary RDL attribute whose
    first-class field does not exist in the model. Every ``DexpiBaseModel``
    carries a ``custom_attributes`` bag, matching DEXPI's ``CustomAttributeOwner``.
    """

    model_config = ConfigDict(validate_assignment=True)

    name: str
    value: str | None = None
    format: str = "string"  # "string" | "double" | "anyURI" | "integer"
    attribute_uri: str | None = None  # defaults to sandbox/<name>
    units: str | None = None
    units_uri: str | None = None
    value_uri: str | None = None
    language: str | None = None


class DexpiBaseModel(BaseModel):
    """Root of every object in the in-memory DEXPI 1.3 conceptual model.

    Carries the two project-level identity fields every object has:

    - ``id``: the in-memory key, auto-generated as a frozen string UUID (same
      shape as pyDEXPI ``id``). It never appears on the wire.
    - ``dex_id``: the required extraction identifier. It is the object's wire
      identity (the Proteus ``ID``), so it must be unique within a model.

    Assignment is re-validated so the model stays valid as it changes.

    A subclass that must not be instantiated directly (an abstract DEXPI base
    such as ``Equipment``) sets ``_abstract = True`` in its own body. Every
    subclass defaults back to concrete, so only the marked base is rejected.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    dex_id: str

    custom_attributes: Annotated[list[CustomAttribute], Composed] = Field(
        default_factory=list
    )
    # Proteus ``ComponentName`` wire attribute (e.g. a shape-library name). It is
    # not a DEXPI data field; the serializer emits it only when set.
    component_name: str | None = None

    _abstract: ClassVar[bool] = False

    # RDL discriminator, filled in by each concrete DEXPI class. Empty on the
    # shared base and on the few concrete classes that map to elements without a
    # ``ComponentClass`` (``Pipe`` -> ``<Connection>``, ``PipingNode`` -> ``<Node>``).
    component_class: ClassVar[str] = ""
    component_class_uri: ClassVar[str] = ""

    def add_custom_attribute(self, attribute: CustomAttribute) -> Self:
        """Add a generic ``attribute`` to this object's customization bag."""
        self.custom_attributes.append(attribute)
        return self

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # A class body that sets ``_abstract`` has already recorded it in
        # ``__dict__`` by the time this hook runs; only fill in the concrete
        # default when the body did not set the flag itself.
        if "_abstract" not in cls.__dict__:
            cls._abstract = False

    @model_validator(mode="before")
    @classmethod
    def _reject_abstract_instantiation(cls, data: Any) -> Any:
        if cls._abstract:
            raise ValueError(f"{cls.__name__} is abstract and cannot be instantiated")
        return data
