"""Tests for the equipment module."""

import pytest
from pydantic import ValidationError

import dexpigen.equipment as eq
from dexpigen.equipment import (
    Chamber,
    CustomEquipment,
    DryingChamber,
    Equipment,
    Nozzle,
    Pump,
    Tank,
    Vessel,
)


# Expected concrete tree, transcribed from
# .scratch/dexpi-13-inmemory-model/research/01-dexpi-13-class-mapping.md.
EXPECTED_TREE: dict[str, tuple[str, ...]] = {
    "Agglomerator": (
        "ReciprocatingPressureAgglomerator",
        "RotatingGrowthAgglomerator",
        "RotatingPressureAgglomerator",
    ),
    "Agitator": (),
    "Blower": ("AxialBlower", "CentrifugalBlower"),
    "Burner": (),
    "Centrifuge": ("FilteringCentrifuge", "SedimentalCentrifuge"),
    "Compressor": (
        "AirEjector",
        "AxialCompressor",
        "CentrifugalCompressor",
        "ReciprocatingCompressor",
        "RotaryCompressor",
    ),
    "CoolingTower": ("DryCoolingTower", "SprayCooler", "WetCoolingTower"),
    "Dryer": ("ConvectionDryer", "HeatedSurfaceDryer"),
    "ElectricGenerator": ("AlternatingCurrentGenerator", "DirectCurrentGenerator"),
    "Extruder": ("ReciprocatingExtruder", "RotatingExtruder"),
    "Fan": ("AxialFan", "RadialFan"),
    "Feeder": (),
    "Filter": (),
    "HeatExchanger": (
        "AirCoolingSystem",
        "ElectricHeater",
        "PlateHeatExchanger",
        "SpiralHeatExchanger",
        "ThinFilmEvaporator",
        "TubularHeatExchanger",
    ),
    "Heater": ("Boiler", "Furnace", "SteamGenerator"),
    "Mill": ("Crusher", "Grinder"),
    "Mixer": ("Kneader", "RotaryMixer", "StaticMixer"),
    "MobileTransportSystem": (
        "ForkliftTruck",
        "RailWaggon",
        "Ship",
        "TransportableContainer",
        "Truck",
    ),
    "Motor": ("AlternatingCurrentMotor", "CombustionEngine", "DirectCurrentMotor"),
    "PackagingSystem": (),
    "ProcessColumn": (),
    "Pump": ("CentrifugalPump", "EjectorPump", "ReciprocatingPump", "RotaryPump"),
    "Separator": (
        "ElectricalSeparator",
        "GravitationalSeparator",
        "MechanicalSeparator",
        "ScrubbingSeparator",
    ),
    "Sieve": ("RevolvingSieve", "StationarySieve", "VibratingSieve"),
    "StationaryTransportSystem": ("Conveyor", "Lift", "LoadingUnloadingSystem"),
    "Turbine": ("GasTurbine", "SteamTurbine"),
    "Vessel": ("PressureVessel", "Silo", "Tank"),
    "WasteGasEmitter": ("Chimney", "Flare"),
    "Weigher": ("BatchWeigher", "ContinuousWeigher"),
}


def test_equipment_is_abstract():
    with pytest.raises(ValidationError):
        Equipment(dex_id="E-1")


def test_chamber_is_abstract():
    with pytest.raises(ValidationError):
        Chamber(dex_id="C-1")


def test_concrete_equipment_is_instantiable():
    pump = Pump(dex_id="P-101")
    assert pump.dex_id == "P-101"
    assert isinstance(pump, Equipment)
    assert isinstance(pump.id, str)


def test_deep_leaf_inherits_its_parent():
    tank = Tank(dex_id="T-1")
    assert isinstance(tank, Vessel)
    assert isinstance(tank, Equipment)


def test_custom_equipment_carries_source_type_label():
    custom = CustomEquipment(dex_id="X-1", source_type_label="weird-thing")
    assert custom.source_type_label == "weird-thing"


def test_equipment_composes_nozzles_via_constructor():
    nozzle = Nozzle(dex_id="N-1")
    pump = Pump(dex_id="P-1", nozzles=[nozzle])
    assert pump.nozzles[0] is nozzle


def test_add_nozzle_composes_under_equipment():
    pump = Pump(dex_id="P-1")
    nozzle = Nozzle(dex_id="N-1")
    result = pump.add_nozzle(nozzle)
    assert result is pump
    assert nozzle in pump.nozzles


def test_nozzle_cannot_have_two_owners():
    pump_a = Pump(dex_id="P-1")
    pump_b = Pump(dex_id="P-2")
    nozzle = Nozzle(dex_id="N-1")
    pump_a.add_nozzle(nozzle)
    with pytest.raises(ValueError):
        pump_b.add_nozzle(nozzle)


def test_nozzle_cannot_have_two_owners_via_constructor():
    nozzle = Nozzle(dex_id="N-1")
    Pump(dex_id="P-1", nozzles=[nozzle])
    with pytest.raises(ValidationError):
        Pump(dex_id="P-2", nozzles=[nozzle])


def test_nozzle_chamber_must_belong_to_same_equipment():
    pump_a = Pump(dex_id="P-1")
    pump_b = Pump(dex_id="P-2")
    chamber = DryingChamber(dex_id="C-1")
    pump_a.add_drying_chamber(chamber)
    nozzle = Nozzle(dex_id="N-1", chamber=chamber)
    with pytest.raises(ValueError):
        pump_b.add_nozzle(nozzle)


def test_nozzle_chamber_same_equipment_is_allowed():
    pump = Pump(dex_id="P-1")
    chamber = DryingChamber(dex_id="C-1")
    pump.add_drying_chamber(chamber)
    nozzle = Nozzle(dex_id="N-1", chamber=chamber)
    pump.add_nozzle(nozzle)
    assert nozzle in pump.nozzles


def test_concrete_equipment_tree_matches_detailed_mapping():
    for parent_name, leaf_names in EXPECTED_TREE.items():
        parent = getattr(eq, parent_name)
        assert issubclass(parent, Equipment)
        assert parent.__bases__ == (Equipment,)
        for leaf_name in leaf_names:
            leaf = getattr(eq, leaf_name)
            assert issubclass(leaf, parent)
            assert leaf.__bases__ == (parent,)


def test_custom_leaves_are_not_generated():
    assert not hasattr(eq, "CustomPump")
    assert not hasattr(eq, "CustomVessel")
    assert not hasattr(eq, "CustomTank")


def test_every_concrete_equipment_is_instantiable():
    for parent_name, leaf_names in EXPECTED_TREE.items():
        getattr(eq, parent_name)(dex_id=f"{parent_name}-1")
        for leaf_name in leaf_names:
            getattr(eq, leaf_name)(dex_id=f"{leaf_name}-1")
