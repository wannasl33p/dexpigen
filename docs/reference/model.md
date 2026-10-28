# Model root and shared base

`ConceptualModel` (the root), `DexpiBaseModel` (every object's base) and `CustomAttribute`.

Generated from `dexpigen.base`, `dexpigen.model` by `scripts/gen_reference.py`; do not edit by hand.

## Contents

- [CustomAttribute](#customattribute)
- [DexpiBaseModel](#dexpibasemodel)
  - [GraphicItem](#graphicitem)
  - [ConceptualModel](#conceptualmodel)

## Classes

### CustomAttribute

A generic name/value entry in the DEXPI customization bag.

- ComponentClass: -
- ComponentClassURI: -
- Bases: BaseModel
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `name` | str | required |  |
| `value` | str \| None | `None` |  |
| `format` | str | `'string'` |  |
| `attribute_uri` | str \| None | `None` |  |
| `units` | str \| None | `None` |  |
| `units_uri` | str \| None | `None` |  |
| `value_uri` | str \| None | `None` |  |
| `language` | str \| None | `None` |  |

### DexpiBaseModel

Root of every object in the in-memory DEXPI 1.3 conceptual model.

- ComponentClass: -
- ComponentClassURI: -
- Bases: BaseModel
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `id` | str | generated |  |
| `dex_id` | str | required |  |
| `custom_attributes` | list[[CustomAttribute](#customattribute)] | `[]` | composed |
| `component_name` | str \| None | `None` |  |

### GraphicItem

Abstract role: an item drawn on the sheet (equipment, nozzle, piping component, off-page connector, instrument bubble, actuator, positioner).

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](#dexpibasemodel)
- Abstract: yes

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `position` | XY \| None | `None` |  |
| `outline` | Points \| None | `None` |  |

### ConceptualModel

The root that aggregates all top-level objects of a P&ID.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `drawing_extent` | XY \| None | `None` |  |
| `equipment` | list[[Equipment](equipment.md#equipment)] | `[]` | composed |
| `piping_network_systems` | list[[PipingNetworkSystem](piping.md#pipingnetworksystem)] | `[]` | composed |
| `process_instrumentation_functions` | list[[ProcessInstrumentationFunction](instrumentation.md#processinstrumentationfunction)] | `[]` | composed |
| `actuating_systems` | list[[ActuatingSystem](instrumentation.md#actuatingsystem)] | `[]` | composed |
| `instrumentation_loop_functions` | list[[InstrumentationLoopFunction](instrumentation.md#instrumentationloopfunction)] | `[]` | composed |
