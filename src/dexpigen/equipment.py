"""Equipment: the abstract ``Equipment`` root, its concrete subclasses,
``Nozzle``, ``CustomEquipment``, and the concrete ``Chamber``."""

from __future__ import annotations

from typing import Annotated, ClassVar, Self

from pydantic import Field, PrivateAttr, model_validator

from dexpigen.base import (
    Composed,
    DexpiBaseModel,
    GraphicItem,
    Ref,
    reject_duplicates,
    reject_recomposition,
)
from dexpigen.piping import PipingSourceItem, PipingTargetItem, SensingLocation

_NOZZLE_ALREADY_COMPOSED = "nozzle is already composed under this equipment"
_CHAMBER_ALREADY_COMPOSED = "chamber is already composed under this equipment"


class Chamber(DexpiBaseModel):
    """An equipment chamber (DEXPI ``Equipment.Chamber``).

    ``Chamber`` is concrete in DEXPI 1.3 (``ComponentClass="Chamber"``,
    ``RDS903151421``); the chamber *subtypes* (``DryingChamber``, ...) are out of
    v0.1 scope, so the generic ``Chamber`` is used directly, matching the
    reference examples.
    """

    component_class: ClassVar[str] = "Chamber"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS903151421"

    sub_tag_name: str | None = None

    _owner: Equipment | None = PrivateAttr(default=None)


class Nozzle(PipingSourceItem, PipingTargetItem, SensingLocation, GraphicItem):
    """A nozzle composed under an equipment (DEXPI ``Equipment.Nozzle``).

    A nozzle is a piping source and target, a sensing location, and owns its
    connection nodes.
    """

    component_class: ClassVar[str] = "Nozzle"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS415214"

    sub_tag_name: str | None = None
    chamber: Annotated[Chamber | None, Ref] = None

    _owner: Equipment | None = PrivateAttr(default=None)


class Equipment(GraphicItem):
    """Abstract root of the equipment tree (DEXPI ``Equipment.Equipment``)."""

    _abstract: ClassVar[bool] = True

    tag_name: str | None = None
    tag_name_prefix: str | None = None
    tag_name_sequence_number: str | None = None
    tag_name_suffix: str | None = None
    equipment_description: str | None = None

    nozzles: Annotated[list[Nozzle], Composed] = Field(default_factory=list)
    drying_chambers: Annotated[list[Chamber], Composed] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bind_owned_children(self) -> Self:
        """Bind composed children and enforce ownership on the constructor path.

        Keeps the constructor (``Pump(dex_id=..., nozzles=[...])``) on the same
        ownership rules as the aggregate methods below.
        """
        reject_duplicates(self.drying_chambers, _CHAMBER_ALREADY_COMPOSED)
        reject_duplicates(self.nozzles, _NOZZLE_ALREADY_COMPOSED)
        for chamber in self.drying_chambers:
            self._adopt_chamber(chamber)
        for nozzle in self.nozzles:
            self._adopt_nozzle(nozzle)
        return self

    def add_nozzle(self, nozzle: Nozzle) -> Self:
        """Compose ``nozzle`` under this equipment, enforcing single ownership."""
        reject_recomposition(nozzle, self.nozzles, _NOZZLE_ALREADY_COMPOSED)
        self._adopt_nozzle(nozzle)
        self.nozzles.append(nozzle)
        return self

    def add_drying_chamber(self, chamber: Chamber) -> Self:
        """Compose ``chamber`` under this equipment, enforcing single ownership."""
        reject_recomposition(chamber, self.drying_chambers, _CHAMBER_ALREADY_COMPOSED)
        self._adopt_chamber(chamber)
        self.drying_chambers.append(chamber)
        return self

    def _adopt_nozzle(self, nozzle: Nozzle) -> None:
        owner = nozzle._owner
        if owner is not None and owner is not self:
            raise ValueError("nozzle is already owned by another equipment")
        if nozzle.chamber is not None and nozzle.chamber._owner is not self:
            raise ValueError("nozzle chamber must belong to the same equipment")
        nozzle._owner = self

    def _adopt_chamber(self, chamber: Chamber) -> None:
        owner = chamber._owner
        if owner is not None and owner is not self:
            raise ValueError("chamber is already owned by another equipment")
        chamber._owner = self


class CustomEquipment(Equipment):
    """Fallback equipment for an extraction type with no matching subclass.

    ``source_type_label`` (a project field, not a DEXPI attribute) keeps the
    unrecognized extraction type string.
    """

    component_class: ClassVar[str] = "CustomEquipment"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/CustomEquipment"

    source_type_label: str | None = None


# Concrete direct subclasses of ``Equipment``, generated 1:1 by name from the
# extraction ``type`` vocabulary (issue 07), each followed by its concrete
# deep leaves. Per-level ``Custom*`` leaves and un-named deep leaves are
# intentionally not generated.

class Agglomerator(Equipment):
    component_class: ClassVar[str] = "Agglomerator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Agglomerator"
class ReciprocatingPressureAgglomerator(Agglomerator):
    component_class: ClassVar[str] = "ReciprocatingPressureAgglomerator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ReciprocatingPressureAgglomerator"
class RotatingGrowthAgglomerator(Agglomerator):
    component_class: ClassVar[str] = "RotatingGrowthAgglomerator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/RotatingGrowthAgglomerator"
class RotatingPressureAgglomerator(Agglomerator):
    component_class: ClassVar[str] = "RotatingPressureAgglomerator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/RotatingPressureAgglomerator"

class Agitator(Equipment):
    component_class: ClassVar[str] = "Agitator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS16045622"

class Blower(Equipment):
    component_class: ClassVar[str] = "BlowerFan"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/BlowerFan"
class AxialBlower(Blower):
    component_class: ClassVar[str] = "AxialBlower"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS433259"
class CentrifugalBlower(Blower):
    component_class: ClassVar[str] = "CentrifugalBlower"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS16766514"

class Burner(Equipment):
    component_class: ClassVar[str] = "Burner"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS284399"

class Centrifuge(Equipment):
    component_class: ClassVar[str] = "Centrifuge"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS420974"
class FilteringCentrifuge(Centrifuge):
    component_class: ClassVar[str] = "FilteringCentrifuge"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/FilteringCentrifuge"
class SedimentalCentrifuge(Centrifuge):
    component_class: ClassVar[str] = "SedimentalCentrifuge"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/SedimentalCentrifuge"

class Compressor(Equipment):
    component_class: ClassVar[str] = "Compressor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS14286497"
class AirEjector(Compressor):
    component_class: ClassVar[str] = "AirEjector"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS5770157"
class AxialCompressor(Compressor):
    component_class: ClassVar[str] = "AxialCompressor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS417239"
class CentrifugalCompressor(Compressor):
    component_class: ClassVar[str] = "CentrifugalCompressor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS417194"
class ReciprocatingCompressor(Compressor):
    component_class: ClassVar[str] = "ReciprocatingCompressor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS417284"
class RotaryCompressor(Compressor):
    component_class: ClassVar[str] = "RotaryCompressor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS435374"

class CoolingTower(Equipment):
    component_class: ClassVar[str] = "CoolingTower"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS14072341"
class DryCoolingTower(CoolingTower):
    component_class: ClassVar[str] = "DryCoolingTower"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS14072386"
class SprayCooler(CoolingTower):
    component_class: ClassVar[str] = "SprayCooler"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/SprayCooler"
class WetCoolingTower(CoolingTower):
    component_class: ClassVar[str] = "WetCoolingTower"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS14071846"

class Dryer(Equipment):
    component_class: ClassVar[str] = "Drier"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS1066939451"
class ConvectionDryer(Dryer):
    component_class: ClassVar[str] = "ConvectionDryer"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ConvectionDryer"
class HeatedSurfaceDryer(Dryer):
    component_class: ClassVar[str] = "HeatedSurfaceDryer"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/HeatedSurfaceDryer"

class ElectricGenerator(Equipment):
    component_class: ClassVar[str] = "ElectricGenerator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS415709"
class AlternatingCurrentGenerator(ElectricGenerator):
    component_class: ClassVar[str] = "AlternatingCurrentGenerator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS873359"
class DirectCurrentGenerator(ElectricGenerator):
    component_class: ClassVar[str] = "DirectCurrentGenerator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/DirectCurrentGenerator"

class Extruder(Equipment):
    component_class: ClassVar[str] = "Extruder"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS394044551"
class ReciprocatingExtruder(Extruder):
    component_class: ClassVar[str] = "PistonExtruder"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS412409911"
class RotatingExtruder(Extruder):
    component_class: ClassVar[str] = "AugerExtruder"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS394045941"

class Fan(Equipment):
    component_class: ClassVar[str] = "BlowerFan"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/BlowerFan"
class AxialFan(Fan):
    component_class: ClassVar[str] = "AxialFan"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS414044"
class RadialFan(Fan):
    component_class: ClassVar[str] = "RadialFan"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS414089"

class Feeder(Equipment):
    component_class: ClassVar[str] = "Feeder"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS300644"

class Filter(Equipment):
    component_class: ClassVar[str] = "Filter"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS300689"

class HeatExchanger(Equipment):
    component_class: ClassVar[str] = "HeatExchanger"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS304199"
class AirCoolingSystem(HeatExchanger):
    component_class: ClassVar[str] = "AirCoolingSystem"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS277379"
class ElectricHeater(HeatExchanger):
    component_class: ClassVar[str] = "ElectricHeater"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS14070475"
class PlateHeatExchanger(HeatExchanger):
    component_class: ClassVar[str] = "PlateHeatExchanger"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/PlateHeatExchanger"
class SpiralHeatExchanger(HeatExchanger):
    component_class: ClassVar[str] = "SpiralHeatExchanger"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/SpiralHeatExchanger"
class ThinFilmEvaporator(HeatExchanger):
    component_class: ClassVar[str] = "ThinFilmEvaporator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ThinFilmEvaporator"
class TubularHeatExchanger(HeatExchanger):
    component_class: ClassVar[str] = "TubularHeatExchanger"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS13971182"

class Heater(Equipment):
    component_class: ClassVar[str] = "Heater"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS13048646"
class Boiler(Heater):
    component_class: ClassVar[str] = "Boiler"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS14058190"
class Furnace(Heater):
    component_class: ClassVar[str] = "Furnace"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS441134"
class SteamGenerator(Heater):
    component_class: ClassVar[str] = "SteamGenerator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS13306207"

class Mill(Equipment):
    component_class: ClassVar[str] = "Mill"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11589220"
class Crusher(Mill):
    component_class: ClassVar[str] = "Crusher"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11589940"
class Grinder(Mill):
    component_class: ClassVar[str] = "Grinder"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Grinder"

class Mixer(Equipment):
    component_class: ClassVar[str] = "Mixer"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Mixer"
class Kneader(Mixer):
    component_class: ClassVar[str] = "Kneader"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Kneader"
class RotaryMixer(Mixer):
    component_class: ClassVar[str] = "RotaryMixer"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/RotaryMixer"
class StaticMixer(Mixer):
    component_class: ClassVar[str] = "StaticMixer"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS1016684"

class MobileTransportSystem(Equipment):
    component_class: ClassVar[str] = "MobileTransportSystem"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/MobileTransportSystem"
class ForkliftTruck(MobileTransportSystem):
    component_class: ClassVar[str] = "ForkliftTruck"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11590075"
class RailWaggon(MobileTransportSystem):
    component_class: ClassVar[str] = "RailWaggon"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11524697"
class Ship(MobileTransportSystem):
    component_class: ClassVar[str] = "Ship"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11523932"
class TransportableContainer(MobileTransportSystem):
    component_class: ClassVar[str] = "TransportableContainer"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS22164402859"
class Truck(MobileTransportSystem):
    component_class: ClassVar[str] = "Truck"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11524112"

class Motor(Equipment):
    component_class: ClassVar[str] = "Motor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS7191198"
class AlternatingCurrentMotor(Motor):
    component_class: ClassVar[str] = "AlternatingCurrentMotor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS472994"
class CombustionEngine(Motor):
    component_class: ClassVar[str] = "CombustionEngine"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS1083734"
class DirectCurrentMotor(Motor):
    component_class: ClassVar[str] = "DirectCurrentMotor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS472949"

class PackagingSystem(Equipment):
    component_class: ClassVar[str] = "PackagingSystem"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/PackagingSystem"

class ProcessColumn(Equipment):
    component_class: ClassVar[str] = "ProcessColumn"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS4316825224"

class Pump(Equipment):
    component_class: ClassVar[str] = "Pump"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS327239"
class CentrifugalPump(Pump):
    component_class: ClassVar[str] = "CentrifugalPump"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416834"
class EjectorPump(Pump):
    component_class: ClassVar[str] = "EjectorPump"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS860624"
class ReciprocatingPump(Pump):
    component_class: ClassVar[str] = "ReciprocatingPump"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416969"
class RotaryPump(Pump):
    component_class: ClassVar[str] = "RotaryPump"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS420749"

class Separator(Equipment):
    component_class: ClassVar[str] = "Separator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS2194378711"
class ElectricalSeparator(Separator):
    component_class: ClassVar[str] = "ElectricalSeparator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ElectricalSeparator"
class GravitationalSeparator(Separator):
    component_class: ClassVar[str] = "GravitySeparator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS16042131"
class MechanicalSeparator(Separator):
    component_class: ClassVar[str] = "MechanicalSeparator"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS279134"
class ScrubbingSeparator(Separator):
    component_class: ClassVar[str] = "ScrubbingSeparator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ScrubbingSeparator"

class Sieve(Equipment):
    component_class: ClassVar[str] = "Sieve"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Sieve"
class RevolvingSieve(Sieve):
    component_class: ClassVar[str] = "RevolvingSieve"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/RevolvingSieve"
class StationarySieve(Sieve):
    component_class: ClassVar[str] = "StationaryScreen"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/StationaryScreen"
class VibratingSieve(Sieve):
    component_class: ClassVar[str] = "VibratingScreen"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/VibratingScreen"

class StationaryTransportSystem(Equipment):
    component_class: ClassVar[str] = "StationaryTransportSystem"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/StationaryTransportSystem"
class Conveyor(StationaryTransportSystem):
    component_class: ClassVar[str] = "Conveyor"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11589895"
class Lift(StationaryTransportSystem):
    component_class: ClassVar[str] = "Lift"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS13601120"
class LoadingUnloadingSystem(StationaryTransportSystem):
    component_class: ClassVar[str] = "Loading-UnloadingSystem"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS11525012"

class Turbine(Equipment):
    component_class: ClassVar[str] = "Turbine"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS313289"
class GasTurbine(Turbine):
    component_class: ClassVar[str] = "GasTurbine"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/GasTurbine"
class SteamTurbine(Turbine):
    component_class: ClassVar[str] = "SteamTurbine"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS416744"

class Vessel(Equipment):
    component_class: ClassVar[str] = "Vessel"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS414674"
class PressureVessel(Vessel):
    component_class: ClassVar[str] = "PressureVessel"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS427229"
class Silo(Vessel):
    component_class: ClassVar[str] = "Silo"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS1022399"
class Tank(Vessel):
    component_class: ClassVar[str] = "Tank"
    component_class_uri: ClassVar[str] = "http://data.posccaesar.org/rdl/RDS445139"

class WasteGasEmitter(Equipment):
    component_class: ClassVar[str] = "WasteGasEmitter"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/WasteGasEmitter"
class Chimney(WasteGasEmitter):
    component_class: ClassVar[str] = "Chimney"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Chimney"
class Flare(WasteGasEmitter):
    component_class: ClassVar[str] = "Flare"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Flare"

class Weigher(Equipment):
    component_class: ClassVar[str] = "Weigher"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Weigher"
class BatchWeigher(Weigher):
    component_class: ClassVar[str] = "BatchWeigher"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/BatchWeigher"
class ContinuousWeigher(Weigher):
    component_class: ClassVar[str] = "ContinuousWeigher"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ContinuousWeigher"
