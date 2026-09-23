"""Tests for the ``component_class`` / ``component_class_uri`` ClassVars."""

import dexpigen.equipment as eq
import dexpigen.instrumentation as ins
import dexpigen.piping as pp
from dexpigen.base import DexpiBaseModel

# Concrete classes that map to elements without a ``ComponentClass`` discriminator
# (``Pipe`` -> ``<Connection>``, ``PipingNode`` -> ``<Node>``), plus the base itself.
NO_COMPONENT_CLASS = {"DexpiBaseModel", "Pipe", "PipingNode"}


def _concrete_classes(module):
    return [
        cls
        for cls in vars(module).values()
        if isinstance(cls, type)
        and issubclass(cls, DexpiBaseModel)
        and not getattr(cls, "_abstract", False)
        and cls.__name__ not in NO_COMPONENT_CLASS
    ]


def test_every_concrete_class_has_component_class_and_uri():
    for module in (eq, pp, ins):
        for cls in _concrete_classes(module):
            assert cls.component_class, cls.__name__
            assert cls.component_class_uri.startswith("http://"), cls.__name__


def test_rename_exceptions():
    assert eq.Blower.component_class == "BlowerFan"
    assert eq.Fan.component_class == "BlowerFan"
    assert eq.Dryer.component_class == "Drier"
    assert eq.ReciprocatingExtruder.component_class == "PistonExtruder"
    assert eq.RotatingExtruder.component_class == "AugerExtruder"
    assert eq.GravitationalSeparator.component_class == "GravitySeparator"
    assert eq.StationarySieve.component_class == "StationaryScreen"
    assert eq.VibratingSieve.component_class == "VibratingScreen"
    assert eq.LoadingUnloadingSystem.component_class == "Loading-UnloadingSystem"


def test_spot_check_rds_uris():
    assert eq.Tank.component_class_uri == "http://data.posccaesar.org/rdl/RDS445139"
    assert (
        eq.CentrifugalPump.component_class_uri
        == "http://data.posccaesar.org/rdl/RDS416834"
    )
    assert eq.Nozzle.component_class_uri == "http://data.posccaesar.org/rdl/RDS415214"
    assert (
        pp.OperatedValve.component_class_uri
        == "http://data.posccaesar.org/rdl/RDS11141590"
    )
    assert (
        pp.PipingNetworkSystem.component_class_uri
        == "http://data.posccaesar.org/rdl/RDS270359"
    )


def test_spot_check_sandbox_uris():
    assert (
        ins.ProcessInstrumentationFunction.component_class_uri
        == "http://sandbox.dexpi.org/rdl/ProcessInstrumentationFunction"
    )
    assert (
        eq.CustomEquipment.component_class_uri
        == "http://sandbox.dexpi.org/rdl/CustomEquipment"
    )
    assert (
        ins.SignalConveyingFunction.component_class_uri
        == "http://sandbox.dexpi.org/rdl/SignalConveyingFunction"
    )
