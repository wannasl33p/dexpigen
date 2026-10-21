# Decide how to add InstrumentationLoopFunction

Type: grilling
Status: resolved
Blocked by: research/07-pipetee-instrumentation-loop

## Question

How do we model `InstrumentationLoopFunction` in v0.2? It is a top-level loop function that collects one or more `ProcessInstrumentationFunction` via `is a collection including` / `is a part of`. Decide the fields (`InstrumentationLoopFunctionNumber`), the collection/reference shape, and how it fits `ConceptualModel` and the serializer.

## Answer

Add `InstrumentationLoopFunction` as a top-level aggregate that **references** (does not compose) `ProcessInstrumentationFunction` objects.

### Class identity

Concrete class `InstrumentationLoopFunction(DexpiBaseModel)` in `instrumentation.py`:
`component_class = "InstrumentationLoopFunction"`,
`component_class_uri = "http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction"`.
It is a `TechnicalItem`, **not** a `TaggedPlantItem` — no `TagName`.

### Fields

- `instrumentation_loop_function_number: str | None = None` (→ `InstrumentationLoopFunctionNumberAssignmentClass`).
- `process_instrumentation_functions: list[ProcessInstrumentationFunction]` — a **reference** list. The referenced PIFs stay top-level in `ConceptualModel.process_instrumentation_functions`; the loop does not own them.

### Naming — resolves the `ProcessInstrumentationFunctions` collision

`ProcessInstrumentationFunctions` names two different DEXPI things, so the Python names are split:

- The PIF **data field** (function letters, e.g. `"I"`, `"T"`) is renamed
  `process_instrumentation_functions: str | None` → **`process_instrumentation_functions_code: str | None`** (`instrumentation.py:53`).
- The loop's **reference** keeps the natural DEXPI name `process_instrumentation_functions`.

This is a **breaking change to the v0.1 PIF API**, accepted for v0.2. Affected sites: `instrumentation.py:53`; `serialization.py:211` (attribute read only — the emitted *name* string `"ProcessInstrumentationFunctions"` is unchanged); `tests/test_instrumentation.py:49,54`; `examples/C01/build.py:350,357,371,385`. `ConceptualModel.process_instrumentation_functions` — the top-level PIF collection — is a different thing and is **not** renamed.

### Serializer

- `_class_key`: branch returning `"InstrumentationLoopFunction"`.
- `CLASS_ORDER["InstrumentationLoopFunction"] = ["InstrumentationLoopFunctionNumberAssignmentClass"]`.
- `_field_attributes`: `elif isinstance(obj, InstrumentationLoopFunction): add(_string("InstrumentationLoopFunctionNumber", obj.instrumentation_loop_function_number))`.
- `_emit_instrumentation_loop_function`: open `<InstrumentationLoopFunction ID ComponentClass ComponentClassURI>`, `_emit_generic_attributes`, then one `Association Type="is a collection including" ItemID=pif.dex_id` per referenced PIF, close.
- **Inverse direction — write-time scan.** The model holds no back-reference on the PIF. `_emit_pif` resolves its loop(s) by scanning `_MODEL`, exactly like `_actuating_function_of` / `_signals_targeting`, and emits `Association Type="is a part of" ItemID=loop.dex_id` after the generic attributes. No `PrivateAttr`, no construction-time `0..1` check.
- **Top-level position:** last, after the `equipment` loop (matches C01).
- Cardinality: 1..* PIFs per loop, and a PIF may be referenced by more than one loop; the scan emits one `is a part of` per referencing loop (the spec's `0..1` opposite is not enforced).

### Fix the hardcoded `ComponentClass` in `_emit_pif`

`serialization.py:545-548` hardcodes `ComponentClass="ProcessInstrumentationFunction"`, so a `ProcessControlFunction` is written with the parent's `ComponentClass`. Switch to `pif.component_class` / `pif.component_class_uri`. A latent v0.1 bug, fixed as part of this work.

### ConceptualModel

Add `instrumentation_loop_functions: list[InstrumentationLoopFunction]` plus an `add_instrumentation_loop_function` helper mirroring `add_actuating_system`.

### Do not model

`ParentStructure`, `TagName`, and the Proteus `<PlantItem>` base beyond what `DexpiBaseModel` already provides.

### Scope

`InstrumentationLoopFunction` must come out of the out-of-scope lists during implementation (`spec.md:83`); the map's destination already assumes it is in v0.2.

## Comments

- Citations: spec:44618-44622 (class), 44650-44653 (number field), 44654-44656 + 44731-44736 (`is a collection including` / `is a part of`), 1290-1331 (top-level composition under `ConceptualModel`).
- The rename trades a v0.1 API break for keeping the natural DEXPI name on the more central concept (the reference), and for removing a genuine name collision.
