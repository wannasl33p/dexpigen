# Custom attributes

**Goal:** carry DEXPI data that has no first-class field (design values, materials, nominal diameters, ...) and the Proteus `ComponentName`.

**Script:** [examples/recipes/custom_attributes.py](../../examples/recipes/custom_attributes.py) (a physical quantity on a tank, a string on a chamber, a value on a node, a URI-valued attribute on a PIF, a shape name on a tee).

## Steps

1. **Check for a first-class field first.** The [class index](../reference/index.md) lists each class's own fields; a value that has a field (for example `tag_name`, `fluid_code`, `sub_tag_name`) must go there, because the writer emits fields itself. Writing the same name again as a custom attribute duplicates it.
2. **Otherwise add a `CustomAttribute`** to the object's `custom_attributes` bag with `add_custom_attribute`. Every model object has the bag, connection nodes (`PipingNode`) included. Each entry is written as one Proteus `GenericAttribute` in the object's `GenericAttributes` block.
3. **Fill the entry like the Proteus element it becomes:**
   - `name`: the RDL name exactly as in Proteus, for example `MaterialOfConstructionCodeAssignmentClass` or `NominalCapacity(Volume)`;
   - `value`: always a string, also for numbers;
   - `format`: "string" (default), "double" for physical quantities, "anyURI" for enumerated values, or "integer";
   - `units` and `units_uri` for a "double";
   - `value_uri` for an "anyURI" value;
   - `attribute_uri` only when it differs from the default `http://sandbox.dexpi.org/rdl/<name>`;
   - `language` when the value is language-tagged.
4. **Order does not matter.** The writer sorts the generic attributes of each element into the order the DEXPI reference examples use; names it does not know go last, in insertion order.
5. **Shape names go to `component_name`.** It sets the Proteus `ComponentName` attribute of the element (for example `T_TYPE_CONNECTION_SHAPE` on a pipe tee). It is a wire attribute, not DEXPI data; the DEXPI component name of a piping component is `piping_component_name`.
6. **Serialize and validate** as in [serialize-and-validate](serialize-and-validate.md); a wrong `format` or a missing unit shows up only there.

## Reading a Proteus file

When reproducing an existing Proteus file, every `GenericAttribute` whose name is not one of the object's first-class fields becomes a `CustomAttribute` with the same `name`, `Value`, `Format`, `Units`, `UnitsURI`, `ValueURI` and, when it is not the sandbox default, `AttributeURI`. `examples/C01/build.py` does this for the C01 reference P&ID from a table in `examples/C01/_extras.py`.

## Pitfalls

- [Keep component_name for the Proteus ComponentName only](../pitfalls.md#keep-component_name-for-the-proteus-componentname-only)
- [Validate every XML you write](../pitfalls.md#validate-every-xml-you-write)
