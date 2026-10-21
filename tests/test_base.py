"""Tests for the shared base layer."""

import pytest
from pydantic import ValidationError

from dexpigen import DexpiBaseModel


def test_id_is_auto_generated_uuid_string():
    model = DexpiBaseModel(dex_id="E-101")
    assert isinstance(model.id, str)
    assert len(model.id) == 36
    assert model.id.count("-") == 4


def test_ids_are_unique_across_instances():
    a = DexpiBaseModel(dex_id="E-101")
    b = DexpiBaseModel(dex_id="E-102")
    assert a.id != b.id


def test_dex_id_is_required():
    with pytest.raises(ValidationError):
        DexpiBaseModel()


def test_id_is_frozen_after_construction():
    model = DexpiBaseModel(dex_id="E-101")
    original = model.id
    with pytest.raises(ValidationError):
        model.id = "forged"
    assert model.id == original


def test_explicit_id_can_be_supplied_at_construction():
    model = DexpiBaseModel(
        dex_id="E-101", id="00000000-0000-4000-8000-000000000000"
    )
    assert model.id == "00000000-0000-4000-8000-000000000000"


def test_validate_assignment_revalidates_mutation():
    model = DexpiBaseModel(dex_id="E-101")
    with pytest.raises(ValidationError):
        model.dex_id = None  # required str, not optional
    assert model.dex_id == "E-101"


def test_component_name_defaults_to_none_and_is_an_instance_field():
    model = DexpiBaseModel(dex_id="E-101")
    assert model.component_name is None
    named = DexpiBaseModel(dex_id="E-102", component_name="T_TYPE_CONNECTION_SHAPE")
    assert named.component_name == "T_TYPE_CONNECTION_SHAPE"
    assert "component_name" in DexpiBaseModel.model_fields
