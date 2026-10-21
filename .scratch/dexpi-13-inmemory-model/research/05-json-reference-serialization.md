# JSON / reference serialization of a DEXPI object graph

## Scope and sources

This note answers one question: what does "serialize the object graph by reference" concretely mean, and what would it take for this project? It is the research note blocking issue 12 (`issues/12-json-reference-serialization.md`).

Primary sources used, all consulted directly (not from memory):

1. **pyDEXPI 1.2.0 source** — the released wheel `pydexpi-1.2.0-py3-none-any.whl` from PyPI, unzipped locally, cross-checked against the `master` branch on GitHub. Verified with `diff`: the wheel and `master` are byte-identical for all three source files quoted below (`loaders/json_serializer.py`, `dexpi_classes/pydantic_classes.py`, `toolkits/base_model_utils.py`). The test file quoted in §2.4 is from `master` only (wheels do not ship tests).
   - `pydexpi/loaders/json_serializer.py` — https://github.com/process-intelligence-research/pyDEXPI/blob/master/pydexpi/loaders/json_serializer.py
   - `pydexpi/dexpi_classes/pydantic_classes.py` — https://github.com/process-intelligence-research/pyDEXPI/blob/master/pydexpi/dexpi_classes/pydantic_classes.py
   - `pydexpi/toolkits/base_model_utils.py` — https://github.com/process-intelligence-research/pyDEXPI/blob/master/pydexpi/toolkits/base_model_utils.py
   - README — https://github.com/process-intelligence-research/pyDEXPI
2. **DEXPI P&ID Specification 1.3** — `data/DEXPI-PID-Specification-1.3.pdf.md` (line numbers below are from that file).
3. **Proteus P&ID Schema 4.1.1 XSD** — `data/schemas/ProteusPIDSchema 4.1.1.xsd` (line numbers below are from that file).

One generated artifact is used as evidence: a JSON fragment produced by running pyDEXPI 1.2.0 locally against a hand-built two-valve `PipingNetworkSegment` (command in §2). It is reproducible, not quoted from a document.

## 1. What "serialization by reference" concretely means

"By reference" is not a DEXPI standard; it is a property of a serialization scheme. Concretely it means three decisions, and only the third is what people usually mean by the phrase:

1. **Every object gets a document-scoped identity** — a string that is stable within the file and can be written where the object itself is not.
2. **Every object is written exactly once**, at its containing (composition) site, so the output is a tree whose edges are composition edges.
3. **A non-compositional relationship (a "reference attribute") is written as the target's identity string, not as a copy of the target.** At load time the identity string is resolved back to the one object instance, so shared identity and cycles survive.

The point of (3) is that a naive serialization of an object graph either (a) duplicates shared objects (an object referenced twice appears twice, and the two copies stop being the same object after a round trip), or (b) recurses forever on a cycle. Identity strings are what break both. In the words of the DEXPI 1.3 spec, object identity is *not* value equality, so a copy is a different thing:

> "the identity of values of classes (which are conventionally called objects) is handled differently: two objects that belong to the same class and that have equal attribute values (e.g, two instances of Nozzle, both with the SubTagName N1 and no value for all other attributes of Nozzle) are not identical."
> — `data/DEXPI-PID-Specification-1.3.pdf.md` lines 725-729 (§2.1.1)

DEXPI already makes exactly this composition/reference split, in the XML mapping (this is what research 04 documented from the XML side, here stated by the spec itself):

> "3.5. Reference Attributes — Most reference attributes are implemented using `<Association>` elements."
> "3.6. Composition Attributes — Most composition attributes correspond to a parent-child relation in the XML hierarchy."
> — ibid. lines 1136 and 1138

So a DEXPI object graph is *already* an identity-bearing graph in the wire format: composition becomes nesting, references become identity pointers. JSON serialization is a second encoding of the same two categories, and the only interesting question is what the identity pointer looks like.

In Proteus XML the identity pointer has XML-native semantics — the XSD declares it as `xsd:ID` / `xsd:IDREF`:

```xml
<!-- ProteusPIDSchema 4.1.1.xsd -->
<xsd:attribute name="ID" type="xsd:ID" use="required"/>                     <!-- line 713 -->
<xsd:attribute name="ItemID" type="xsd:IDREF" use="optional"/>              <!-- line 543 -->
```

`xsd:ID` is document-unique and `xsd:IDREF` must resolve to one, so the XML format is literally "write each object once with an `ID`, and point at it elsewhere with `ItemID`". the DEXPI spec spells that use out as an `<Association>` element carrying the relationship name:

```xml
<Association Type="is a part of" ItemID="enterprise1"/>
```

`data/DEXPI-PID-Specification-1.3.pdf.md` line ~4437 (example for `IndustrialComplex.ParentStructure`); the same shape appears at line 4412-4415, and the relationship-type strings are catalogued in research 04.

## 2. The pyDEXPI JSON format

### 2.1 The entry points

pyDEXPI has no `dump_json()`. The JSON path is a serializer class with `save` / `load` plus in-memory helpers, and the README documents only `save`/`load`:

```python
from pydexpi.loaders import JsonSerializer

my_serializer = JsonSerializer()
my_serializer.save(dexpi_model, "dummy_path", "dummy_filename")
dexpi_model = my_serializer.load("dummy_path", "dummy_filename")
```

- README, section "Serialization" (lines 116-140): "You can load and save DEXPI Python models via the serializer. Currently pickle `.pkl` and json `.json` are offered as file formats."
- `JsonSerializer` also exposes `model_to_dict`, `dict_to_model`, `export_to_bytes`, `export_to_stream`, `load_from_bytes`, `load_from_string` (`pydexpi/loaders/json_serializer.py`, lines 34-210).
- Note: pyDEXPI classes are Pydantic models, so the inherited `BaseModel.model_dump_json()` exists, but pyDEXPI never calls it and it is *not* the reference format — see §3.4.

### 2.2 Shape: one nested tree, with references replaced by id strings

The encoder is `DexpiToDictEncoder.dexpi_element_to_dict`. It classifies every field of an object into one of three categories and emits a dict with a fixed key set (`pydexpi/loaders/json_serializer.py`, lines 262-300):

```python
element_dict = {"uri": element.uri}
if isinstance(element, DexpiBaseModel):
    element_dict["id"] = element.id
if comp_attribute_dict:
    element_dict["composition"] = comp_attribute_dict
if reference_attribute_dict:
    element_dict["reference"] = reference_attribute_dict
if data_attribute_dict:
    element_dict["data"] = data_attribute_dict
```

with the key line for references, three lines above:

```python
# Package reference attributes. For reference attributes, we only store the IDs.
reference_attribute_dict[attr] = _call_on_list_or_object_or_none(lambda x: x.id, attr_val)
```

So the four keys are:

| key | content | emitted for |
|---|---|---|
| `uri` | the class URI constant of the object's concrete class | always |
| `id` | the object's identity string | every `DexpiBaseModel` (not data-type models) |
| `composition` | nested dict (or list of dicts), recursed | non-empty only |
| `reference` | target `id` string, or list of id strings | non-empty only |
| `data` | primitive, or a nested dict for a structured data type | non-empty only |

**There is no flat `id -> object` map.** The output is a single root document with composition nesting; identity strings are the only cross-links. The flat map exists only transiently inside the *decoder* (§2.4).

### 2.3 A small real example

Generated by running pyDEXPI 1.2.0 (`uv run --with pydexpi --python 3.13`) on a `PipingNetworkSegment` holding two `BallValve`s and one `PipingConnection` that links them; empty values pruned for readability.

```json
{
  "uri": "https://pyDEXPI.org/schemas/pydexpi_1_3/pipingNetworkSegment.py",
  "id": "e4ec0085-988c-41f0-926c-e81e41c7cfdf",
  "composition": {
    "connections": [
      {
        "uri": "https://pyDEXPI.org/schemas/pydexpi_1_3/pipingConnection.py",
        "id": "53038bf9-ba8b-4d6c-9841-6c6f7493439d",
        "reference": {
          "sourceItem": "0ef84fb5-7a83-458d-8118-cf7d1b7ccf24",
          "sourceNode": "ce7b6160-f3bd-4f74-aaa8-e07d4e588c06",
          "targetItem": "bbb6f88e-3cd4-430c-b277-4d98756b64b9",
          "targetNode": "00a636f4-b976-4cc0-960b-cdeb59a7a717"
        }
      }
    ],
    "items": [
      {
        "uri": "https://pyDEXPI.org/schemas/pydexpi_1_3/ballValve.py",
        "id": "0ef84fb5-7a83-458d-8118-cf7d1b7ccf24",
        "composition": {
          "nodes": [
            { "uri": "https://pyDEXPI.org/schemas/pydexpi_1_3/pipingNode.py",
              "id": "ce7b6160-f3bd-4f74-aaa8-e07d4e588c06" }
          ]
        }
      },
      {
        "uri": "https://pyDEXPI.org/schemas/pydexpi_1_3/ballValve.py",
        "id": "bbb6f88e-3cd4-430c-b277-4d98756b64b9",
        "composition": {
          "nodes": [
            { "uri": "https://pyDEXPI.org/schemas/pydexpi_1_3/pipingNode.py",
              "id": "00a636f4-b976-4cc0-960b-cdeb59a7a717" }
          ]
        }
      }
    ]
  },
  "data": { "fluidCode": "N2" }
}
```

Read it as the answer to the question: the two valves are written **once each**, under `composition.items`; the valve in `reference.sourceItem` is **not** a copy — it is the 36-character id `0ef84fb5-...`, which is the `id` of the first `ballValve` above it. `PipingConnection.sourceItem/sourceNode/targetItem/targetNode` are declared as reference-category fields on `PipingConnection`, `PipingNetworkSegment.connections/items` as composition-category fields, which is why one nests and the other points:

```python
class PipingConnection(DexpiBaseModel):
    # Reference attributes:
    sourceItem: PipingSourceItem | None = Field(None, json_schema_extra={"attribute_category": "reference"})
    ...
class PipingNetworkSegment(...):
    # Compositional attributes:
    connections: list[PipingConnection] = Field(default_factory=list, json_schema_extra={"attribute_category": "composition"})
    items: list[PipingNetworkSegmentItem] = Field(default_factory=list, json_schema_extra={"attribute_category": "composition"})
```

(`pydexpi/dexpi_classes/pydantic_classes.py`, `PipingConnection` at line ~240, `PipingNetworkSegment` at line 2258)

The category is part of the model, not a serializer setting: it lives in each field's `json_schema_extra={"attribute_category": "composition" | "reference" | "data"}`, and the serializer reads it back generically:

```python
def _get_attributes_with_category(dexpi_object, category):
    for fld_name, field in dexpi_object.__class__.model_fields.items():
        if field.json_schema_extra is not None:
            if "attribute_category" in field.json_schema_extra:
                if field.json_schema_extra["attribute_category"] == category:
                    attribute_dict[fld_name] = getattr(dexpi_object, fld_name)
```

(`pydexpi/toolkits/base_model_utils.py`, `_get_attributes_with_category`)

Important consequence: fields of a category are **never omitted**, even when empty/None. `test_export_to_bytes` asserts `b"uri" in json_bytes` and `b"composition" in json_bytes`, and in an unpruned dump a `PipingNetworkSegment` carries all four keys, including a `reference` block full of `null`s and a `data` block listing ~22 `null` data fields. The format is a full-field schema dump, not a sparse one.

### 2.4 Loading: two passes over a registry

`DictToDexpiDecoder` reconstructs the graph (`json_serializer.py`, lines 325-560). The id strings are resolved through a dict keyed by id, which is the flat map the format itself does not contain:

1. **Compositional pass** — recursively builds objects from `uri` + `composition` + `data`. If an object's `id` is already in `self.object_registry` it returns the existing instance instead of rebuilding it ("If the object has been created successfully already, return it from the registry"). Each new object is registered by id: `self.object_registry[new_object.id] = new_object`, with the comment "If there isn't [an ID], then the object cannot be referenced, so it doesn't need to be registered."
2. **Reference pass** — walks `reference` blocks and does `self.object_registry.__getitem__(id)`.

Forward references are handled by retrying: a *required* reference whose target has not been built yet raises `IncompletePassError`, and `dict_to_dexpi_element` re-runs the compositional pass until no new objects appear, with a guard:

```python
all_objects_parsed_flag = False
while not all_objects_parsed_flag:
    curr_obj_len = len(self.object_registry)
    try:
        the_object = self._compositional_pass(data)
        all_objects_parsed_flag = True
    except IncompletePassError:
        next_obj_len = len(self.object_registry)
        if next_obj_len == curr_obj_len:
            raise RuntimeError("Stalled parsing process: No new objects were created in the last pass.")
```

Optional references are resolved in the single final reference pass. This is structurally the same two-pass problem our Proteus writer already has to solve for `ItemID` (research 04: "Forward references are normal ... a parser must resolve in two passes"), and the same one our *reader*-less v0.1 does not have to solve at all.

Round-tripping is asserted to preserve identity, not just values — in `tests/test_loaders/test_json_loader.py`:

```python
# Compare via identity, which references the object ids
assert simple_pns.connections[1].sourceItem == reconstructed_pns.connections[1].sourceItem
```

and the full-model test compares the two graphs for isomorphism with NetworkX and then byte-compares the re-exported dict (`assert json_dict == reconstructed_json_dict`).

## 3. How `id` / `InstanceId` is used

### 3.1 The term "InstanceId" does not occur in the primary sources

`InstanceId` appears **nowhere** in `data/DEXPI-PID-Specification-1.3.pdf.md` (case-insensitive search for `instanceid`: no hits) and nowhere in `data/schemas/ProteusPIDSchema 4.1.1.xsd`. The DEXPI spec and the Proteus XSD call the identity attribute plain **`ID`** (`xsd:ID`), and the pointer **`ItemID`** (`xsd:IDREF`). It is also absent from the pyDEXPI source, which uses plain **`id`**.

So "`InstanceId`" in the team's user story is the project's own vocabulary for "the identity attribute", not a DEXPI or pyDEXPI term. If the project adopts the concept it should pick one of the two source spellings (`id` for a JSON/Python-facing name, `ID`/`ItemID` for Proteus-side) and say so in `CONTEXT.md`.

### 3.2 In pyDEXPI it is a UUID4 string, generated at construction

```python
class DexpiBaseModel(ABC, BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    # Object ID, defaults to a uuid if not specified
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Field to store proteus id if available
    proteusId: str | None = Field(None)

    # Hash function
    def __hash__(self):
        """Computes hash from id and type."""
        return hash((self.id, type(self)))
```

(`pydexpi/dexpi_classes/pydantic_classes.py`, lines 16-32; `import uuid` at line 7)

Facts that matter:

- **Yes, it is a UUID** — `str(uuid.uuid4())`, so the wire form is a dashed lowercase 36-char string exactly like ours.
- **It is mutable in pyDEXPI.** `id` has a default factory but no `frozen=True`; the class overrides `__copy__`/`__deepcopy__` specifically to assign a *new* id to the copy. This is a deliberate "a copy is a new object" rule, matching the DEXPI identity statement in §1. (Our model makes `id` `frozen=True` instead, which is stricter; a deep copy of ours would carry the id over unless we override copying too.)
- **The Proteus `ID` is kept separately**, in `proteusId: str | None`. The two identities are never conflated — the UUID is the JSON/pyDEXPI identity, the Proteus ID is whatever the imported XML said. Note the asymmetry with our model, where `dex_id` is the Proteus wire identity and the `id` UUID is currently **unused by the writer** (`serialization.py` emits `ID=...dex_id` throughout).
- **Identity drives hashing**: `hash((self.id, type(self)))` makes two distinct objects with equal field values hash differently, while the *same* object reached by two paths hashes the same — which is what a graph mapper (pyDEXPI's `GraphLoader`) needs.

### 3.3 The type discriminator is a separate key: `uri`

Every pyDEXPI class carries a `ClassVar` class URI:

```python
class DexpiModel(DexpiBaseModel):
    uri: ClassVar[str] = "https://pyDEXPI.org/schemas/pydexpi_1_3/dexpiModel.py"
```

and the decoder inverts it by scanning the class tree:

```python
def get_dexpi_class_from_uri(uri: str) -> type[DexpiBaseModel]:
    for submodule_name in dir(dexpi_classes):
        submodule = getattr(dexpi_classes, submodule_name)
        for attr in dir(submodule):
            candidate = getattr(submodule, attr)
            if isinstance(candidate, type):
                cls_uri = getattr(candidate, "uri", None)
                if cls_uri == uri:
                    return candidate
    raise AttributeError(f"Class with uri {uri!r} not a DEXPI class.")
```

(`pydexpi/toolkits/base_model_utils.py`)

This is the JSON counterpart of the Proteus `ComponentClass`/`ComponentClassURI` pair, but it is **not** the same value — the `uri` values are pyDEXPI's own namespace (`https://pyDEXPI.org/schemas/pydexpi_1_3/<className>.py`), not RDL URIs. Each concrete subclass declares its own (e.g. `ProcessControlFunction` at `pydantic_classes.py:4591`), so a subtype never inherits an ambiguous discriminator.

### 3.4 Why the hand-written encoder exists instead of Pydantic's JSON

Worth recording, because it is the reason a JSON writer is real work rather than a one-liner. Calling the Pydantic-inherited dump on a reference-carrying object loses the concrete type and the structure. Running `PipingConnection.model_dump_json(indent=2)` on the object from §2.3 yields:

```json
{
  "id": "72673c35-4019-4b63-b574-8368c0d78e91",
  "proteusId": null,
  "sourceItem": { "id": "20a79fda-2348-425e-bffd-95bac1568586", "proteusId": null },
  "sourceNode": { "id": "5d5fd6c3-149b-4d78-8f89-57fc6e19169e", "proteusId": null, "customAttributes": [], "nominalDiameterRepresentation": null, ... },
  ...
}
```

`sourceItem` is annotated `PipingSourceItem | None` — an abstract base — so Pydantic serializes only the base's fields and the concrete `BallValve` fields (`nodes`, `fluidCode`, ...) are silently gone; there is no type discriminator to recover them, no `composition`/`reference` distinction, and no `uri`. The hand-written encoder/decoder pair is what adds the discriminator and the reference semantics.

## 4. What it would take for this project (INFERENCE — my assessment, not a source claim)

Everything below is my own reading of the sources above applied to our code; it is not stated by pyDEXPI or the DEXPI spec.

**The model side is already 90% there, by accident.** We have the two pieces that make the format possible:

- `DexpiBaseModel.id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)` in `src/dexpigen/base.py` — the same UUID4-string identity pyDEXPI uses, already there for exactly this story. Ours is stricter (frozen) than pyDEXPI's, which is fine and arguably better; the only consequence is that a deep copy keeps the original id, so if we ever expose copying we must reassign ids there, as pyDEXPI does.
- `component_class` / `component_class_uri` ClassVars on every concrete class — a ready-made type discriminator, serving the same role as pyDEXPI's `uri`. We would emit the RDL pair rather than a private namespace, which is arguably more useful (it is the same discriminator the Proteus writer uses), but it is a different value from pyDEXPI's, so the two JSON formats would not be interchangeable.

**What is missing is the composition/reference distinction as model metadata.** pyDEXPI carries it per field in `json_schema_extra={"attribute_category": ...}`. We carry it only *inside the writer*, implicitly, as Python code: `serialization.py` nests what research 04's table marks as composition and emits `<Association>` for the five reference fields (`OperatedValveReference.valve`, `ActuatingFunction.systems`, `ActuatingFunction.actuating_location`, `SignalConveyingFunction.source`, `SignalConveyingFunction.target`). A JSON writer would either duplicate that knowledge as a second hard-coded list — the worst option, because the two lists drift — or, better, promote it to a declared, machine-readable per-field category that *both* writers read. That refactor is the real work item, and it pays for itself regardless of JSON: it makes "which of my fields are references?" answerable instead of implicit.

**Effort, concretely.** A `to_json`/`from_json` pair for our v0.1 graph is a moderate amount of work, not a project — our class count is roughly a third of pyDEXPI's (149 `class` statements across `src/dexpigen/*.py` vs 514 in pyDEXPI's `pydantic_classes.py`), the encoder is a ~30-line recursive walk over `model_fields` plus a category lookup, and the decoder is the two-pass registry from §2.4, which we need for forward references (an `ActuatingSystem` must emit an `ItemID` for an `ActuatingFunction` nested inside a later `ProcessInstrumentationFunction` — research 04 documents exactly this for the XML writer). The decision worth making *before* coding is the format question in issue 12: whether to copy pyDEXPI's exact key layout (`uri`/`id`/`composition`/`reference`/`data`) for ecosystem familiarity, or to emit the RDL `ComponentClass`/`ComponentClassURI` pair and a flatter shape. The sources support either; they only pin down that **references must be id strings and objects must be written once**.

**Two things I would flag as genuinely open, not answerable from the sources:**

1. **The cycle question.** pyDEXPI's format writes references as id strings but still requires the target to be *written somewhere* in the same document — the decoder resolves exclusively against `object_registry` populated during that load, and `JsonSerializer.load` calls `dict_to_model(data, external_refs={})`. Nothing in the reference pass tolerates a missing target: it calls `self.object_registry.__getitem__(attr_val)` with no `try`/`except` (the compositional pass is the only one that catches `KeyError`), so a dangling id raises `KeyError` on load. Verified locally: serializing a `PipingConnection` whose `targetItem` was never composed anywhere, then loading it back, raises `KeyError: '<the missing id>'`. For us that matters if JSON is ever used to serialize a *fragment* rather than a whole `ConceptualModel`; pyDEXPI's answer is effectively "the document is always self-contained".
2. **Two identities, and which one goes on the wire.** pyDEXPI keeps `id` (UUID, JSON identity) and `proteusId` (imported XML identity) strictly separate. We currently run the other way: `dex_id` is what our Proteus writer emits as `ID`/`ItemID`, and `id` is unused. If we add JSON we must decide whether JSON identity is `id` (making JSON and Proteus use different identity strings for the same object, matching pyDEXPI's separation of concerns) or `dex_id` (making the two formats agree, at the cost of `id` remaining decorative). This is a project decision, not a source fact, and it belongs in the issue-12 grilling rather than in this note.
