"""Shared base layer for the DEXPI 1.3 in-memory conceptual model."""

from typing import Any, ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DexpiBaseModel(BaseModel):
    """Root of every object in the in-memory DEXPI 1.3 conceptual model.

    Carries the two project-level identity fields every object has:

    - ``id``: the DEXPI wire identity, auto-generated as a frozen string UUID
      (same wire shape as pyDEXPI ``id``).
    - ``dex_id``: the required extraction identifier; it is traceable to the
      extraction source and must not be used as ``id``.

    Assignment is re-validated so the model stays valid as it changes.

    A subclass that must not be instantiated directly (an abstract DEXPI base
    such as ``Equipment``) sets ``_abstract = True`` in its own body. Every
    subclass defaults back to concrete, so only the marked base is rejected.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    dex_id: str

    _abstract: ClassVar[bool] = False

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
