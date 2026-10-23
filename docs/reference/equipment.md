# Equipment classes

The `Equipment` tree, `Nozzle`, `Chamber` and `CustomEquipment`.

Generated from `dexpigen.equipment` by `scripts/gen_reference.py`; do not edit by hand.

## Contents

- [Chamber](#chamber)
- [Nozzle](#nozzle)
- [Equipment](#equipment)
  - [CustomEquipment](#customequipment)
  - [Agglomerator](#agglomerator)
  - [Blower](#blower)
  - [Centrifuge](#centrifuge)
  - [Compressor](#compressor)
  - [CoolingTower](#coolingtower)
  - [Dryer](#dryer)
  - [ElectricGenerator](#electricgenerator)
  - [Extruder](#extruder)
  - [Fan](#fan)
  - [HeatExchanger](#heatexchanger)
  - [Heater](#heater)
  - [Mill](#mill)
  - [Mixer](#mixer)
  - [MobileTransportSystem](#mobiletransportsystem)
  - [Motor](#motor)
  - [Pump](#pump)
  - [Separator](#separator)
  - [Sieve](#sieve)
  - [StationaryTransportSystem](#stationarytransportsystem)
  - [Turbine](#turbine)
  - [Vessel](#vessel)
  - [WasteGasEmitter](#wastegasemitter)
  - [Weigher](#weigher)
- [Equipment leaves without own fields](#equipment-leaves-without-own-fields)

## Classes

### Chamber

An equipment chamber (DEXPI `Equipment.Chamber`).

- ComponentClass: `Chamber`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS903151421`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `sub_tag_name` | str \| None | `None` |  |

### Nozzle

A nozzle composed under an equipment (DEXPI `Equipment.Nozzle`).

- ComponentClass: `Nozzle`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS415214`
- Bases: [PipingSourceItem](piping.md#pipingsourceitem), [PipingTargetItem](piping.md#pipingtargetitem), [SensingLocation](piping.md#sensinglocation)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `sub_tag_name` | str \| None | `None` |  |
| `chamber` | [Chamber](#chamber) \| None | `None` | ref |

### Equipment

Abstract root of the equipment tree (DEXPI `Equipment.Equipment`).

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `tag_name` | str \| None | `None` |  |
| `tag_name_prefix` | str \| None | `None` |  |
| `tag_name_sequence_number` | str \| None | `None` |  |
| `tag_name_suffix` | str \| None | `None` |  |
| `equipment_description` | str \| None | `None` |  |
| `nozzles` | list[[Nozzle](#nozzle)] | `[]` | composed |
| `drying_chambers` | list[[Chamber](#chamber)] | `[]` | composed |

### CustomEquipment

Fallback equipment for an extraction type with no matching subclass.

- ComponentClass: `CustomEquipment`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/CustomEquipment`
- Bases: [Equipment](#equipment)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `source_type_label` | str \| None | `None` |  |

### Agglomerator

- ComponentClass: `Agglomerator`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/Agglomerator`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Blower

- ComponentClass: `BlowerFan`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/BlowerFan`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Centrifuge

- ComponentClass: `Centrifuge`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS420974`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Compressor

- ComponentClass: `Compressor`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS14286497`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### CoolingTower

- ComponentClass: `CoolingTower`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS14072341`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Dryer

- ComponentClass: `Drier`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS1066939451`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### ElectricGenerator

- ComponentClass: `ElectricGenerator`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS415709`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Extruder

- ComponentClass: `Extruder`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS394044551`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Fan

- ComponentClass: `BlowerFan`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/BlowerFan`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### HeatExchanger

- ComponentClass: `HeatExchanger`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS304199`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Heater

- ComponentClass: `Heater`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS13048646`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Mill

- ComponentClass: `Mill`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS11589220`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Mixer

- ComponentClass: `Mixer`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/Mixer`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### MobileTransportSystem

- ComponentClass: `MobileTransportSystem`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/MobileTransportSystem`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Motor

- ComponentClass: `Motor`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS7191198`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Pump

- ComponentClass: `Pump`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS327239`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Separator

- ComponentClass: `Separator`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS2194378711`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Sieve

- ComponentClass: `Sieve`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/Sieve`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### StationaryTransportSystem

- ComponentClass: `StationaryTransportSystem`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/StationaryTransportSystem`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Turbine

- ComponentClass: `Turbine`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS313289`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Vessel

- ComponentClass: `Vessel`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS414674`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### WasteGasEmitter

- ComponentClass: `WasteGasEmitter`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/WasteGasEmitter`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

### Weigher

- ComponentClass: `Weigher`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/Weigher`
- Bases: [Equipment](#equipment)
- Abstract: no

No own fields.

## Equipment leaves without own fields

Concrete equipment classes with no subclasses and no fields of their own.

| Class | Parent | ComponentClass | ComponentClassURI |
| --- | --- | --- | --- |
| `ReciprocatingPressureAgglomerator` | [Agglomerator](#agglomerator) | `ReciprocatingPressureAgglomerator` | `http://sandbox.dexpi.org/rdl/ReciprocatingPressureAgglomerator` |
| `RotatingGrowthAgglomerator` | [Agglomerator](#agglomerator) | `RotatingGrowthAgglomerator` | `http://sandbox.dexpi.org/rdl/RotatingGrowthAgglomerator` |
| `RotatingPressureAgglomerator` | [Agglomerator](#agglomerator) | `RotatingPressureAgglomerator` | `http://sandbox.dexpi.org/rdl/RotatingPressureAgglomerator` |
| `Agitator` | [Equipment](#equipment) | `Agitator` | `http://data.posccaesar.org/rdl/RDS16045622` |
| `AxialBlower` | [Blower](#blower) | `AxialBlower` | `http://data.posccaesar.org/rdl/RDS433259` |
| `CentrifugalBlower` | [Blower](#blower) | `CentrifugalBlower` | `http://data.posccaesar.org/rdl/RDS16766514` |
| `Burner` | [Equipment](#equipment) | `Burner` | `http://data.posccaesar.org/rdl/RDS284399` |
| `FilteringCentrifuge` | [Centrifuge](#centrifuge) | `FilteringCentrifuge` | `http://sandbox.dexpi.org/rdl/FilteringCentrifuge` |
| `SedimentalCentrifuge` | [Centrifuge](#centrifuge) | `SedimentalCentrifuge` | `http://sandbox.dexpi.org/rdl/SedimentalCentrifuge` |
| `AirEjector` | [Compressor](#compressor) | `AirEjector` | `http://data.posccaesar.org/rdl/RDS5770157` |
| `AxialCompressor` | [Compressor](#compressor) | `AxialCompressor` | `http://data.posccaesar.org/rdl/RDS417239` |
| `CentrifugalCompressor` | [Compressor](#compressor) | `CentrifugalCompressor` | `http://data.posccaesar.org/rdl/RDS417194` |
| `ReciprocatingCompressor` | [Compressor](#compressor) | `ReciprocatingCompressor` | `http://data.posccaesar.org/rdl/RDS417284` |
| `RotaryCompressor` | [Compressor](#compressor) | `RotaryCompressor` | `http://data.posccaesar.org/rdl/RDS435374` |
| `DryCoolingTower` | [CoolingTower](#coolingtower) | `DryCoolingTower` | `http://data.posccaesar.org/rdl/RDS14072386` |
| `SprayCooler` | [CoolingTower](#coolingtower) | `SprayCooler` | `http://sandbox.dexpi.org/rdl/SprayCooler` |
| `WetCoolingTower` | [CoolingTower](#coolingtower) | `WetCoolingTower` | `http://data.posccaesar.org/rdl/RDS14071846` |
| `ConvectionDryer` | [Dryer](#dryer) | `ConvectionDryer` | `http://sandbox.dexpi.org/rdl/ConvectionDryer` |
| `HeatedSurfaceDryer` | [Dryer](#dryer) | `HeatedSurfaceDryer` | `http://sandbox.dexpi.org/rdl/HeatedSurfaceDryer` |
| `AlternatingCurrentGenerator` | [ElectricGenerator](#electricgenerator) | `AlternatingCurrentGenerator` | `http://data.posccaesar.org/rdl/RDS873359` |
| `DirectCurrentGenerator` | [ElectricGenerator](#electricgenerator) | `DirectCurrentGenerator` | `http://sandbox.dexpi.org/rdl/DirectCurrentGenerator` |
| `ReciprocatingExtruder` | [Extruder](#extruder) | `PistonExtruder` | `http://data.posccaesar.org/rdl/RDS412409911` |
| `RotatingExtruder` | [Extruder](#extruder) | `AugerExtruder` | `http://data.posccaesar.org/rdl/RDS394045941` |
| `AxialFan` | [Fan](#fan) | `AxialFan` | `http://data.posccaesar.org/rdl/RDS414044` |
| `RadialFan` | [Fan](#fan) | `RadialFan` | `http://data.posccaesar.org/rdl/RDS414089` |
| `Feeder` | [Equipment](#equipment) | `Feeder` | `http://data.posccaesar.org/rdl/RDS300644` |
| `Filter` | [Equipment](#equipment) | `Filter` | `http://data.posccaesar.org/rdl/RDS300689` |
| `AirCoolingSystem` | [HeatExchanger](#heatexchanger) | `AirCoolingSystem` | `http://data.posccaesar.org/rdl/RDS277379` |
| `ElectricHeater` | [HeatExchanger](#heatexchanger) | `ElectricHeater` | `http://data.posccaesar.org/rdl/RDS14070475` |
| `PlateHeatExchanger` | [HeatExchanger](#heatexchanger) | `PlateHeatExchanger` | `http://sandbox.dexpi.org/rdl/PlateHeatExchanger` |
| `SpiralHeatExchanger` | [HeatExchanger](#heatexchanger) | `SpiralHeatExchanger` | `http://sandbox.dexpi.org/rdl/SpiralHeatExchanger` |
| `ThinFilmEvaporator` | [HeatExchanger](#heatexchanger) | `ThinFilmEvaporator` | `http://sandbox.dexpi.org/rdl/ThinFilmEvaporator` |
| `TubularHeatExchanger` | [HeatExchanger](#heatexchanger) | `TubularHeatExchanger` | `http://data.posccaesar.org/rdl/RDS13971182` |
| `Boiler` | [Heater](#heater) | `Boiler` | `http://data.posccaesar.org/rdl/RDS14058190` |
| `Furnace` | [Heater](#heater) | `Furnace` | `http://data.posccaesar.org/rdl/RDS441134` |
| `SteamGenerator` | [Heater](#heater) | `SteamGenerator` | `http://data.posccaesar.org/rdl/RDS13306207` |
| `Crusher` | [Mill](#mill) | `Crusher` | `http://data.posccaesar.org/rdl/RDS11589940` |
| `Grinder` | [Mill](#mill) | `Grinder` | `http://sandbox.dexpi.org/rdl/Grinder` |
| `Kneader` | [Mixer](#mixer) | `Kneader` | `http://sandbox.dexpi.org/rdl/Kneader` |
| `RotaryMixer` | [Mixer](#mixer) | `RotaryMixer` | `http://sandbox.dexpi.org/rdl/RotaryMixer` |
| `StaticMixer` | [Mixer](#mixer) | `StaticMixer` | `http://data.posccaesar.org/rdl/RDS1016684` |
| `ForkliftTruck` | [MobileTransportSystem](#mobiletransportsystem) | `ForkliftTruck` | `http://data.posccaesar.org/rdl/RDS11590075` |
| `RailWaggon` | [MobileTransportSystem](#mobiletransportsystem) | `RailWaggon` | `http://data.posccaesar.org/rdl/RDS11524697` |
| `Ship` | [MobileTransportSystem](#mobiletransportsystem) | `Ship` | `http://data.posccaesar.org/rdl/RDS11523932` |
| `TransportableContainer` | [MobileTransportSystem](#mobiletransportsystem) | `TransportableContainer` | `http://data.posccaesar.org/rdl/RDS22164402859` |
| `Truck` | [MobileTransportSystem](#mobiletransportsystem) | `Truck` | `http://data.posccaesar.org/rdl/RDS11524112` |
| `AlternatingCurrentMotor` | [Motor](#motor) | `AlternatingCurrentMotor` | `http://data.posccaesar.org/rdl/RDS472994` |
| `CombustionEngine` | [Motor](#motor) | `CombustionEngine` | `http://data.posccaesar.org/rdl/RDS1083734` |
| `DirectCurrentMotor` | [Motor](#motor) | `DirectCurrentMotor` | `http://data.posccaesar.org/rdl/RDS472949` |
| `PackagingSystem` | [Equipment](#equipment) | `PackagingSystem` | `http://sandbox.dexpi.org/rdl/PackagingSystem` |
| `ProcessColumn` | [Equipment](#equipment) | `ProcessColumn` | `http://data.posccaesar.org/rdl/RDS4316825224` |
| `CentrifugalPump` | [Pump](#pump) | `CentrifugalPump` | `http://data.posccaesar.org/rdl/RDS416834` |
| `EjectorPump` | [Pump](#pump) | `EjectorPump` | `http://data.posccaesar.org/rdl/RDS860624` |
| `ReciprocatingPump` | [Pump](#pump) | `ReciprocatingPump` | `http://data.posccaesar.org/rdl/RDS416969` |
| `RotaryPump` | [Pump](#pump) | `RotaryPump` | `http://data.posccaesar.org/rdl/RDS420749` |
| `ElectricalSeparator` | [Separator](#separator) | `ElectricalSeparator` | `http://sandbox.dexpi.org/rdl/ElectricalSeparator` |
| `GravitationalSeparator` | [Separator](#separator) | `GravitySeparator` | `http://data.posccaesar.org/rdl/RDS16042131` |
| `MechanicalSeparator` | [Separator](#separator) | `MechanicalSeparator` | `http://data.posccaesar.org/rdl/RDS279134` |
| `ScrubbingSeparator` | [Separator](#separator) | `ScrubbingSeparator` | `http://sandbox.dexpi.org/rdl/ScrubbingSeparator` |
| `RevolvingSieve` | [Sieve](#sieve) | `RevolvingSieve` | `http://sandbox.dexpi.org/rdl/RevolvingSieve` |
| `StationarySieve` | [Sieve](#sieve) | `StationaryScreen` | `http://sandbox.dexpi.org/rdl/StationaryScreen` |
| `VibratingSieve` | [Sieve](#sieve) | `VibratingScreen` | `http://sandbox.dexpi.org/rdl/VibratingScreen` |
| `Conveyor` | [StationaryTransportSystem](#stationarytransportsystem) | `Conveyor` | `http://data.posccaesar.org/rdl/RDS11589895` |
| `Lift` | [StationaryTransportSystem](#stationarytransportsystem) | `Lift` | `http://data.posccaesar.org/rdl/RDS13601120` |
| `LoadingUnloadingSystem` | [StationaryTransportSystem](#stationarytransportsystem) | `Loading-UnloadingSystem` | `http://data.posccaesar.org/rdl/RDS11525012` |
| `GasTurbine` | [Turbine](#turbine) | `GasTurbine` | `http://sandbox.dexpi.org/rdl/GasTurbine` |
| `SteamTurbine` | [Turbine](#turbine) | `SteamTurbine` | `http://data.posccaesar.org/rdl/RDS416744` |
| `PressureVessel` | [Vessel](#vessel) | `PressureVessel` | `http://data.posccaesar.org/rdl/RDS427229` |
| `Silo` | [Vessel](#vessel) | `Silo` | `http://data.posccaesar.org/rdl/RDS1022399` |
| `Tank` | [Vessel](#vessel) | `Tank` | `http://data.posccaesar.org/rdl/RDS445139` |
| `Chimney` | [WasteGasEmitter](#wastegasemitter) | `Chimney` | `http://sandbox.dexpi.org/rdl/Chimney` |
| `Flare` | [WasteGasEmitter](#wastegasemitter) | `Flare` | `http://sandbox.dexpi.org/rdl/Flare` |
| `BatchWeigher` | [Weigher](#weigher) | `BatchWeigher` | `http://sandbox.dexpi.org/rdl/BatchWeigher` |
| `ContinuousWeigher` | [Weigher](#weigher) | `ContinuousWeigher` | `http://sandbox.dexpi.org/rdl/ContinuousWeigher` |
