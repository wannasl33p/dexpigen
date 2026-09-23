"""Shared base layer for the DEXPI 1.3 in-memory conceptual model."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class DexpiBaseModel(BaseModel):
    """Root of every object in the in-memory DEXPI 1.3 conceptual model.

    Carries the two project-level identity fields every object has:

    - ``id``: the DEXPI wire identity, auto-generated as a frozen string UUID
      (same wire shape as pyDEXPI ``id``).
    - ``dex_id``: the required extraction identifier; it is traceable to the
      extraction source and must not be used as ``id``.

    Assignment is re-validated so the model stays valid as it changes.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    dex_id: str
