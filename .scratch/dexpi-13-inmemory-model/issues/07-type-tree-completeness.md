# Decide equipment and valve type-tree completeness

Type: grilling
Status: resolved
Blocked by: 01

## Question

v0.1 should have typed classes even though extraction will often not know the type. How much of the DEXPI 1.3 Equipment and Valve subclass trees do we generate now versus only the types we listed plus Custom* fallbacks?

Constraint already decided: unknown equipment → CustomEquipment, not Tank.

## Answer

The model is generated **1:1 by name** from the extraction `type` vocabulary, with `CustomEquipment` as the only fallback. No blanket full-tree generation, no per-level `Custom*` leaves.

**Equipment.** `Equipment` is the abstract root. A concrete class is generated for each extraction `type` whose name matches an official 1.3 concrete class, at whatever depth: `tank`→`Tank` (under `Vessel`), `pump`→`Pump`, `vessel`→`Vessel`, `silo`→`Silo`, … (all such classes are concrete with their own `ComponentClass`). Any unmatched `type` → `CustomEquipment`. The per-level `Custom*` leaves (`CustomPump`, `CustomVessel`, …) and un-named deep leaves are not generated.

**Valve.** `PipingComponent` is abstract. The concrete family roots `OperatedValve`, `CheckValve`, `SafetyValveOrFitting` are the instantiable fallback for an unspecified valve. Named matches: `ball`→`BallValve`, `globe`→`GlobeValve`, `butterfly`→`ButterflyValve`, `needle`→`NeedleValve`, `gate`→`GateValve`, `check`→`CheckValve` (`CheckValve` itself is concrete). `FlameArrestor`/`RuptureDisc` stay out (fittings, not valves).

**Fallback.** The `type`→class mapping is the mapper's later job (out of v0.1); the rule is 1:1 by name with `CustomEquipment` for no match.

## Comments

- Grilling: user picked 1:1 name mapping (Q1=c simplified), valve set `ball/globe/butterfly/check/needle/gate`, equipment fallback collapsed to `CustomEquipment` (Q3=b); per-level `Custom*` leaves dropped.
- Fact correction during resolution: DEXPI equipment intermediates (`Pump`, `Vessel`, …) and valve family roots (`OperatedValve`, `CheckValve`, `SafetyValveOrFitting`) are **concrete** (each has its own `ComponentClass`), not abstract; only `Equipment` and `PipingComponent` are abstract. So `pump`→`Pump` and `check`→`CheckValve` are directly instantiable.
