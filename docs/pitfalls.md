# Pitfalls

Rules that are easy to get wrong when building a `ConceptualModel`, most frequent first.
Each entry gives the **Symptom** (exact error text or wrong output), **Why** (DEXPI 1.3 or project policy), the **Fix**, and what **Enforced by** means for it: a test that guards the check, XSD only (only `examples/validate_dexpi.py` catches it), or not enforced (nothing catches it; you must get it right).

Error texts below are message fragments. Errors raised inside a constructor arrive wrapped in a Pydantic validation error (a ValueError subclass) whose text contains the fragment.

## Contents

1. [Give every composed child exactly one owner](#give-every-composed-child-exactly-one-owner)
2. [Compose with add methods, never by mutating a list](#compose-with-add-methods-never-by-mutating-a-list)
3. [Treat dex_id as the wire identity, not id](#treat-dex_id-as-the-wire-identity-not-id)
4. [Reference the same object, never a copy](#reference-the-same-object-never-a-copy)
5. [Compose everything you reference](#compose-everything-you-reference)
6. [Compare model objects with is, not ==](#compare-model-objects-with-is-not-)
7. [Instantiate concrete classes only](#instantiate-concrete-classes-only)
8. [Compose signals, actuating functions and sensors under a PIF](#compose-signals-actuating-functions-and-sensors-under-a-pif)
9. [Add the PIFs of a loop at the top level too](#add-the-pifs-of-a-loop-at-the-top-level-too)
10. [Take a connection node from its own item](#take-a-connection-node-from-its-own-item)
11. [Point an OperatedValveReference at an OperatedValve](#point-an-operatedvalvereference-at-an-operatedvalve)
12. [Count flow indices from 1](#count-flow-indices-from-1)
13. [Keep component_name for the Proteus ComponentName only](#keep-component_name-for-the-proteus-componentname-only)
14. [Validate every XML you write](#validate-every-xml-you-write)
15. [Map extraction types by name, with the documented fallbacks](#map-extraction-types-by-name-with-the-documented-fallbacks)

## Give every composed child exactly one owner

- **Symptom:** `add_nozzle` on a second equipment raises `nozzle is already owned by another equipment` (likewise `node is already owned by another owner`, `item is already owned by another segment`, `segment is already owned by another system`, `function is already owned by another process instrumentation function`). Adding it twice to the same owner raises `nozzle is already composed under this equipment`.
- **Why:** DEXPI 1.3: a composition child has exactly one owner and exists only inside it (see Composition in `CONTEXT.md`).
- **Fix:** Create a separate object for each owner; add each child once.
- **Enforced by:** `tests/test_equipment.py::test_nozzle_cannot_have_two_owners`, `tests/test_equipment.py::test_nozzle_same_owner_readd_is_rejected`, `tests/test_piping.py::test_segment_same_owner_readd_is_rejected`

## Compose with add methods, never by mutating a list

- **Symptom:** `to_proteus_xml` raises `use the add_* method instead of mutating the list in place`, or `is composed more than once in the model` when the same child was appended under two owners.
- **Why:** Project policy: `add_nozzle`, `add_node`, `add_item`, ... record the owner and run the ownership checks; `equipment.nozzles.append` skips both. Assigning a whole list (`tank.nozzles = [...]`) or passing it to the constructor is fine: it runs the same checks.
- **Fix:** Use the `add_*` method of the owner (or the constructor keyword).
- **Enforced by:** `tests/test_model_checks.py::test_list_append_bypassing_add_is_rejected`, `tests/test_model_checks.py::test_child_appended_to_a_second_owner_is_rejected`

## Treat dex_id as the wire identity, not id

- **Symptom:** `to_proteus_xml` raises `is not a valid XML NCName` or `the Proteus ID must be unique in the model`. Setting `id` changes nothing in the XML.
- **Why:** Project policy: `dex_id` is written as the Proteus `ID` (an XML ID: unique, starts with a letter or underscore, no spaces or colons); every pipe-end owner also gets an implicit `<dex_id>-DefaultNode` ID. `id` is an in-memory UUID key and never reaches the wire (see DEX_ID and id in `CONTEXT.md`).
- **Fix:** Give every object a unique, NCName-shaped `dex_id`; leave `id` alone.
- **Enforced by:** `tests/test_model_checks.py::test_dex_id_that_is_not_an_ncname_is_rejected`, `tests/test_model_checks.py::test_duplicate_dex_id_is_rejected`

## Reference the same object, never a copy

- **Symptom:** `to_proteus_xml` raises `but not composed anywhere in the model` (only the original is composed) or `the Proteus ID must be unique in the model` (both are composed).
- **Why:** Project policy: a reference holds the very Python object owned elsewhere; `model_copy` makes a second object with the same `dex_id`.
- **Fix:** Pass the original object to `valve`, `source`, `target`, `sensing_location`, `systems`, ...
- **Enforced by:** `tests/test_instrumentation.py::test_same_object_referenced_not_cloned`, `tests/test_model_checks.py::test_reference_to_uncomposed_object_is_rejected`

## Compose everything you reference

- **Symptom:** `to_proteus_xml` raises `but not composed anywhere in the model`, naming the target and the referring field.
- **Why:** DEXPI 1.3 / Proteus: every `Association` `ItemID` and `Connection` `FromID`/`ToID` must resolve to an element in the same file. The Relation column of the [class index](reference/index.md) marks reference fields `ref`.
- **Fix:** Also compose the target: a nozzle under its equipment, a valve in a segment's items, a PIF at the top level.
- **Enforced by:** `tests/test_model_checks.py::test_reference_to_uncomposed_object_is_rejected`, `tests/test_model_checks.py::test_sensing_location_must_be_composed`

## Compare model objects with is, not ==

- **Symptom:** No error. `==` compares every field of the whole subtree (slow on large models) and is true for a `model_copy`, so a membership test with `in` accepts a copy.
- **Why:** Project policy: object identity is Python identity; Pydantic `==` is structural.
- **Fix:** Use `is`, or `any(x is y for y in items)` for membership.
- **Enforced by:** not enforced

## Instantiate concrete classes only

- **Symptom:** `Equipment(dex_id=...)` raises `is abstract and cannot be instantiated`.
- **Why:** DEXPI 1.3 abstract classes (`Equipment`, `PipingComponent`, `PipeOffPageConnector`, `PipingConnection`, the role bases) have no `ComponentClass`.
- **Fix:** Pick a concrete subclass; the [class index](reference/index.md) shows Abstract: yes/no per class.
- **Enforced by:** `tests/test_equipment.py::test_equipment_is_abstract`

## Compose signals, actuating functions and sensors under a PIF

- **Symptom:** The object is missing from the XML: `ConceptualModel` has no field for `SignalConveyingFunction`, `ActuatingFunction` or `ProcessSignalGeneratingFunction`, and an unknown constructor keyword is silently ignored.
- **Why:** DEXPI 1.3: these functions are composed by their `ProcessInstrumentationFunction`.
- **Fix:** `add_signal_conveying_function`, `add_actuating_function`, `add_process_signal_generating_function` on the PIF; add the PIF at the top level.
- **Enforced by:** not enforced

## Add the PIFs of a loop at the top level too

- **Symptom:** `to_proteus_xml` raises `but not composed anywhere in the model` for a PIF named in `process_instrumentation_functions` of an `InstrumentationLoopFunction`.
- **Why:** DEXPI 1.3: a loop references the PIFs it collects ("is a collection including"); it does not own them.
- **Fix:** `add_process_instrumentation_function(pif)` on the `ConceptualModel` as well as listing it in the loop.
- **Enforced by:** `tests/test_model_checks.py::test_loop_referencing_pif_missing_from_model_is_rejected`

## Take a connection node from its own item

- **Symptom:** `Pipe(...)` raises `connection source node must belong to its source item` (or `connection target node must belong to its target item`).
- **Why:** DEXPI 1.3: a connection's node is one of its item's nodes.
- **Fix:** Pass `source_node=item.nodes[i]` for the same `item` given as `source_item`; add the node to the item before building the `Pipe`.
- **Enforced by:** `tests/test_piping.py::test_connection_node_rejects_foreign_node`

## Point an OperatedValveReference at an OperatedValve

- **Symptom:** `OperatedValveReference(valve=CheckValve(...))` raises a Pydantic validation error for `valve`.
- **Why:** DEXPI 1.3: the controlled valve of an `ActuatingSystem` is an `OperatedValve` (or a subclass such as `GlobeValve`); `CheckValve` and `SafetyValveOrFitting` are not.
- **Fix:** Model a control valve as an `OperatedValve` subclass.
- **Enforced by:** `tests/test_instrumentation.py::test_operated_valve_reference_rejects_check_valve`

## Count flow indices from 1

- **Symptom:** No error: `FlowIn`/`FlowOut` in the XML point at the wrong node.
- **Why:** Project policy, following Proteus `ConnectionPoints`: `flow_in_index`/`flow_out_index` are 1-based positions in `nodes`. The implicit default node is not counted.
- **Fix:** For `nodes = [inlet, outlet]` write `flow_in_index=1, flow_out_index=2`; leave a port undeclared with None.
- **Enforced by:** not enforced

## Keep component_name for the Proteus ComponentName only

- **Symptom:** No error: the value appears as the `ComponentName` XML attribute (a shape-library name such as `T_TYPE_CONNECTION_SHAPE`), not as DEXPI data.
- **Why:** Project policy: `ComponentName` is a Proteus wire attribute, not a DEXPI field (see ComponentName in `CONTEXT.md`).
- **Fix:** A DEXPI component name goes to `piping_component_name`; `component_name` only carries a source shape name.
- **Enforced by:** not enforced

## Validate every XML you write

- **Symptom:** xmllint reports `Schemas validity error` for the file, while `to_proteus_xml` returned normally.
- **Why:** Project policy: the serializer only writes; it checks the model graph, not the schema (for example a `CustomAttribute` with an invalid `format` is written as given).
- **Fix:** Run `uv run python examples/validate_dexpi.py out.xml` (or `validate()` from it) on every generated file.
- **Enforced by:** XSD only

## Map extraction types by name, with the documented fallbacks

- **Symptom:** No error: an unknown equipment type lands on a wrong concrete class (typically `Tank`).
- **Why:** Project policy: an extraction type maps to the concrete class of the same name (`tank` to `Tank`, `ball` to `BallValve`). Unmatched equipment becomes `CustomEquipment` with the original label in `source_type_label`, never `Tank`. An unspecified valve becomes the family root `OperatedValve`, `CheckValve` or `SafetyValveOrFitting`; an unspecified fitting becomes `PipeFitting`.
- **Fix:** Look the name up in the [class index](reference/index.md); otherwise use the fallback above.
- **Enforced by:** not enforced
