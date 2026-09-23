# Decide the public construction API

Type: grilling
Status: resolved
Blocked by: 01, 03

## Question

How should a caller build a valid ConceptualModel in v0.1?

Decide: package/module layout; whether callers instantiate leaf DEXPI classes directly or go through factories; how composition is expressed (nested objects vs id references); how `InstanceId` and `DEX_ID` are assigned; how CustomEquipment carries the original type label; whether ActuatingSystemComponent is a facade or the real type.

## Answer

Follow pyDEXPI’s **construction shape**, not its source: Pydantic v2 classes, official DEXPI names, nested composition, object references, `validate_assignment=True`. Identity uses a frozen string UUID (`id`) plus a required extraction `dex_id`. There is no `ActuatingSystemComponent` class.

### Package layout

Top-level package is this library (not `pydexpi`). Split like the DEXPI packages / pyDEXPI modules:

- `.../equipment.py` — `Equipment` descendants, `Nozzle`, `CustomEquipment`
- `.../piping.py` — systems, segments, pipes, fittings, operated/check/safety valves, off-page connectors
- `.../instrumentation.py` — `ProcessInstrumentationFunction`, `SignalConveyingFunction`, `ActuatingSystem`, `ActuatingFunction`, …
- `.../physical_quantities.py`, `.../enumerations.py`
- `.../base.py` — `DexpiBaseModel`

Callers import official class names from those modules.

### Construction

Direct constructors of concrete classes, as in pyDEXPI (`Pump(tagName=..., nozzles=[...])`). Optional factories only for multi-object graphs (control valve → `OperatedValve` + `ActuatingSystem` + refs). No `ActuatingSystemComponent` type or facade type.

### Composition vs reference

- Composition: nested Python objects (`equipment.nozzles: list[Nozzle]`).
- Reference: the **same Python object** held by another field (e.g. `OperatedValveReference.valve: OperatedValve | None`), not `InstanceRef[T]`.
- JSON (later, out of v0.1 tests): serialize composition inline; serialize references by `id` so cycles and shared identity survive. String UUIDs have no JSON problem.

### Identity

On `DexpiBaseModel`:

- `id: str` — `default_factory` uuid4 hex/str, **frozen** after create (pyDEXPI uses `str(uuid.uuid4())`; same wire shape).
- `dex_id: str` — **required**, extraction id. Not used as DEXPI `id`.

### CustomEquipment

Unknown equipment type → `CustomEquipment`. Optional extra string `sourceTypeLabel` (project field, not a DEXPI attribute) holds the unrecognized extraction class name.

### Mutability

`model_config = ConfigDict(validate_assignment=True)`. Mutate via aggregate methods (`add_nozzle`, `add_segment`, …). `id` frozen.

## Comments

- pyDEXPI docs used as architectural reference only: Context7 `/process-intelligence-research/pydexpi` (`DexpiBaseModel`, nested nozzles, `id: str` uuid, JsonSerializer). No pyDEXPI source copied into this repo.
