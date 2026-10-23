# Equipment and nozzles

**Goal:** model equipment items with their nozzles and chambers, including nozzles that sit in a chamber.

**Script:** [examples/recipes/equipment_and_nozzles.py](../../examples/recipes/equipment_and_nozzles.py) (pumps, two heat exchangers, a tank).

## Steps

1. **Pick the concrete class.** Instantiate the DEXPI class of the item, for example `CentrifugalPump`, `ReciprocatingPump`, `PlateHeatExchanger`, `TubularHeatExchanger` or `Tank` from `dexpigen.equipment`. `Equipment` itself is abstract. An extraction type with no matching class becomes `CustomEquipment` with `source_type_label`. All classes and their `ComponentClass` values are in the [equipment index](../reference/equipment.md).
2. **Set identity and tag.** Every object needs a unique `dex_id` (it becomes the Proteus `ID`). The tag lives in `tag_name`, with its parts in `tag_name_prefix`, `tag_name_sequence_number` and `tag_name_suffix`; `equipment_description` is free text. Every data field is optional; a field left at None or set to an empty string is not written, except `tag_name_suffix=""`, which is written as an empty value.
3. **Give each nozzle its pipe end.** Create a `Nozzle` (its label goes in `sub_tag_name`) and compose one `PipingNode` into it with `add_node`. A pipe later connects to that node.
4. **Compose nozzles under the equipment** with `add_nozzle`, or pass them in the constructor as `nozzles=[...]`. A nozzle has exactly one owner.
5. **Add chambers before the nozzles that sit in them.** Compose each `Chamber` with `add_drying_chamber` (or `drying_chambers=[...]`). A nozzle located in a chamber gets `chamber=` set to that `Chamber` when it is created, and the chamber must already belong to the same equipment when the nozzle is added. The `chamber` field is a reference: the chamber stays composed under the equipment.
6. **Add the equipment to the model** with `ConceptualModel.add_equipment`, or pass `equipment=[...]` to `ConceptualModel`. Equipment is top-level; nozzles and chambers are not.
7. **Serialize and validate** as in [serialize-and-validate](serialize-and-validate.md).

## What it becomes in Proteus XML

Each equipment item is an `Equipment` element with its `ComponentClass`; nozzles are nested `Nozzle` elements with `ConnectionPoints`; chambers are nested `Equipment` elements with `ComponentClass="Chamber"`. A nozzle in a chamber gets an `Association` of type "is located in", mirrored on the chamber as "is the location of".

## Pitfalls

- [Give every composed child exactly one owner](../pitfalls.md#give-every-composed-child-exactly-one-owner)
- [Compose with add methods, never by mutating a list](../pitfalls.md#compose-with-add-methods-never-by-mutating-a-list)
- [Treat dex_id as the wire identity, not id](../pitfalls.md#treat-dex_id-as-the-wire-identity-not-id)
- [Instantiate concrete classes only](../pitfalls.md#instantiate-concrete-classes-only)
- [Map extraction types by name, with the documented fallbacks](../pitfalls.md#map-extraction-types-by-name-with-the-documented-fallbacks)
