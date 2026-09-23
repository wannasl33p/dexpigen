# Map extraction types to DEXPI 1.3 classes

Type: research
Status: resolved
Blocked by:

## Question

Which official DEXPI P&ID 1.3 classes (package, class name, inheritance, key attributes, RDL/ComponentClass where specified) correspond to this v0.1 set?

- Equipment, with subclasses present in 1.3 even if extraction will often fall back
- CustomEquipment as fallback
- Valve and its 1.3 subclasses
- in-off-page-connector and out-off-page-connector
- ActuatingSystemComponent / controlled valve assembly
- SignalLine
- MainProcessLine
- Instrument (including tag and typical data attributes)
- SpectacleBlind, Reducer, Flange
- Nozzle (including tag)

Primary sources only: DEXPI P&ID Specification 1.3 (https://dexpi.plants-and-bytes.de/ and GitLab `dexpi/Specification` tag `V1.3.0`). Do not read pyDEXPI source.

Write findings to `.scratch/dexpi-13-inmemory-model/research/01-dexpi-13-class-mapping.md` with citations.

## Answer

Official DEXPI 1.3 class names for the v0.1 extraction set are recorded in [01-dexpi-13-class-mapping](../research/01-dexpi-13-class-mapping.md). Extraction aliases are not 1:1 with metamodel classes: there is no `Valve`, `Instrument`, `MainProcessLine`, or `ActuatingSystemComponent` class. Fallback equipment is `CustomEquipment`. Tags split across `TagName` (equipment), `ProcessInstrumentationFunctionNumber` (instrument), and `SubTagName` (nozzle).

## Comments

- Primary-source findings and the recommended v0.1 aliases are documented in [`../research/01-dexpi-13-class-mapping.md`](../research/01-dexpi-13-class-mapping.md). Key naming decisions: `SignalLine` maps to `SignalConveyingFunction` (general; not `SignalLineFunction` — revised in ticket 06), `MainProcessLine` maps at line level to `PipingNetworkSystem`, generic `Valve` is an application-side union rather than a DEXPI class, and a control-valve assembly is `ActuatingSystem` plus `OperatedValveReference`.
