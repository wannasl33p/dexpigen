# Decide the task recipes and the invariants/pitfalls catalogue

Type: grilling
Status: resolved
Blocked by: 02-doc-set-layout
Assignee: alex.valentsinovich

## Question

Which tasks get a recipe (equipment + nozzles, piping system and connections, instrumentation loop, serialize and validate), and how are they anchored to runnable code (`examples/C01/build.py`, tests)? Which invariants and traps must be spelled out (single composition owner, `id` vs `dex_id`, reference vs clone, identity vs equality, fallback rules)? Decide format and the source of each entry.

Input from [Decide the generated class index](03-generated-class-index.md): the extraction type -> class rule (same-name class, `CustomEquipment`, valve family roots) is hand-written here, not generated; decide whether it sits in `docs/pitfalls.md` or a mapping recipe. Composition vs reference is visible per field in the generated index; pitfalls only explain the consequences.

## Answer

Resolved by grilling on 2026-10-23. No ADR: every choice is cheap to reverse.

- **Recipe scope = the C01 surface:** everything a deserialized `examples/C01` golden contains gets a recipe. Six recipes, in this order:
  1. `equipment-and-nozzles`: equipment, nozzles, chambers, nozzle -> chamber.
  2. `piping-network`: system -> segment -> valves, tees, reducer, off-page connectors, connections, nodes, `flow_in_index`/`flow_out_index`.
  3. `measurement`: PIF + PSGF + sensing location + signal + instrumentation loop.
  4. `control-valve`: `ActuatingSystem` (actuator, `OperatedValveReference`) + `ActuatingFunction`.
  5. `custom-attributes`: non-first-class data via `CustomAttribute` (most of C01's `GenericAttribute`s), and `component_name`.
  6. `serialize-and-validate`.
  Classes the model has but C01 lacks (`ProcessControlFunction`, signal OPCs, `CheckValve`, `CustomEquipment`, `FlowMeasuringElement`, ...) appear only in the generated index. There is no extraction-mapping recipe.
- **Anchoring:** one runnable, self-contained script per recipe, `examples/recipes/<task>.py`; recipe 6 uses `examples/minimal.py` (the README example). A recipe `.md` gives the goal, prose steps naming classes, a link to its script, and links to the relevant pitfalls; it copies no code. `examples/C01/build.py` stays the large real example linked from the README.
- **Recipe test:** `tests/test_recipes.py` runs every script, serializes the result and validates it with xmllint. It also asserts that the union of `ComponentClass` values **and** element tags emitted by all scripts covers everything in the latest `examples/C01/verNNN/c01.xml` golden. Tags catch `Connection`, `InformationFlow` and `Association`, which have no `ComponentClass`. A new C01 milestone with a new class fails the test until a recipe covers it.
- **`docs/pitfalls.md` entry format:** `## <rule, imperative>` followed by **Symptom** (exact error text or wrong output), **Why** (`DEXPI 1.3` or `project policy`, per the dexpi-13 construct-time invariant catalogue), **Fix** (one line), **Enforced by** (test node id, `XSD only`, or `not enforced`). No code block longer than one line. Ordered most-frequent first, with a TOC.
- **Catalogue (15 entries):**
  1. one composition owner; `add_*` to a second owner raises;
  2. mutating lists (`.nozzles.append`) bypasses checks; use `add_*`;
  3. `id` vs `dex_id`: `dex_id` becomes Proteus `ID` (`xsd:ID`: unique, NCName), `id` never reaches the wire;
  4. a reference is the same object, never a copy (`model_copy`);
  5. everything referenced must also be composed somewhere reachable from `ConceptualModel`;
  6. compare model objects with `is`, not `==` (structural, whole subtree);
  7. abstract classes reject instantiation;
  8. `SignalConveyingFunction` / `ActuatingFunction` / PSGF are composed under a PIF, not top-level;
  9. a loop references PIFs; the PIFs are still added top-level;
  10. a connection node belongs to its item;
  11. `OperatedValveReference` accepts `OperatedValve` only;
  12. `flow_in_index`/`flow_out_index` are 1-based;
  13. `ComponentName` is a wire attribute, not DEXPI data;
  14. the serializer only writes; always validate;
  15. extraction type -> class: same-name concrete class; unmatched equipment -> `CustomEquipment` with `source_type_label`, never `Tank`; unspecified valve -> `OperatedValve` / `CheckValve` / `SafetyValveOrFitting` (this settles the placement left open by ticket 03).
- **Enforcement gaps** (documented as `not enforced` now; handed to the implementation subagent, outside this map; an entry's **Enforced by** changes when its check lands):
  - `dex_id` uniqueness / NCName shape (only XSD catches it);
  - referenced-but-not-composed objects;
  - list mutation bypassing `_adopt_*`;
  - **bug:** `Equipment.add_nozzle` / `add_drying_chamber` on the same owner twice appends a duplicate, while PIF children reject a same-owner re-add.
- **Glossary:** `DEX_ID` and `id` entries in `CONTEXT.md` corrected: `dex_id` is the wire identity (Proteus `ID`), `id` is the in-memory key and never appears on the wire.

## Comments

**2026-10-23, implementation (WP2).** What landed for the enforcement gaps and the bug; version bumped to 0.3.0 (new errors a caller can hit).

- **Bug fixed:** `Equipment.add_nozzle` / `add_drying_chamber` reject a same-owner re-add (`nozzle is already composed under this equipment`, `chamber is already composed under this equipment`); a duplicate in the constructor list is rejected with the same message. The same bug existed in `add_node`, `add_item`, `add_connection` and `add_segment`; fixed the same way (`node is already composed under this owner`, `item is already composed under this segment`, `connection is already composed under this segment`, `segment is already composed under this system`). Tests: `tests/test_equipment.py::test_nozzle_same_owner_readd_is_rejected`, `::test_chamber_same_owner_readd_is_rejected`, `tests/test_piping.py::test_*_same_owner_readd_is_rejected`.
- **All three gaps closed, in one place:** `to_proteus_xml` now runs `_check_model` before writing. It walks the composition tree via the WP1 `Composed` markers and follows `Ref` fields. Construction stays permissive (extraction IDs may be anything until written). Stable message fragments:
  - `dex_id` shape: `is not a valid XML NCName` (`tests/test_model_checks.py::test_dex_id_that_is_not_an_ncname_is_rejected`); uniqueness, including the implicit `<dex_id>-DefaultNode` IDs: `the Proteus ID must be unique in the model` (`::test_duplicate_dex_id_is_rejected`). The root `ConceptualModel.dex_id` is exempt (no Proteus ID).
  - referenced but not composed: `but not composed anywhere in the model` (`::test_reference_to_uncomposed_object_is_rejected`).
  - list mutation bypassing `_adopt_*`: `use the add_* method instead of mutating the list in place` (owner not recorded; `::test_list_append_bypassing_add_is_rejected`) and `is composed more than once in the model` (same object reachable twice; `::test_child_appended_to_a_second_owner_is_rejected`). Direct field assignment (`tank.nozzles = [...]`) is not a gap: Pydantic re-runs the binding validators on assignment.
- **Side finding fixed:** `PipeOffPageConnectorReferenceByNumber.referenced_connector_number` / `referenced_drawing_number` were never serialized; they now emit `ReferencedConnectorNumberAssignmentClass` / `ReferencedDrawingNumberAssignmentClass` (needed to reproduce P02). `PipeOffPageConnectorObjectReference.referenced_connector` is still not written (no example uses it).
- **PipeFitting (from ticket 05), not changed:** DEXPI 1.3 section 8.43.1 marks `PipeFitting` as "Class", not "Abstract class" (compare 8.52.1 `PipingComponent`), and gives it an RDL reference, `ComponentClass="PipeFitting"`, `ComponentClassURI="http://sandbox.dexpi.org/rdl/PipeFitting"` and a Proteus instance example. Trimmed C03 instantiates it (`PipeFitting-1`). The model's `_abstract = True` on `PipeFitting` (guarded by `tests/test_piping.py::test_pipe_fitting_is_abstract`) contradicts the spec; making it concrete is for the human to decide.
