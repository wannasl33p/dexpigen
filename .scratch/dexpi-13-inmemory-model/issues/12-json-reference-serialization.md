# Decide JSON/reference serialization for v0.2

Type: grilling
Status: out-of-scope
Blocked by: research/05-json-reference-serialization

## Question

Should v0.2 add JSON serialization of the object graph ("by reference": each object serialized once and referred to by its `id`), alongside the Proteus XML writer? If so, what is the format, and how do composition (inline) vs reference (by id) map onto our Python-object-reference model?

## Out of scope

Ruled out of the v0.2 destination: JSON/reference serialization is **not needed at all** for this effort. Closed unclaimed — never resolved as a route decision; it is a scope boundary, not a step on the route. The research note (`research/05-json-reference-serialization.md`) stays on disk for a future effort.

If it returns, it returns as a fresh effort against a redrawn destination, not as a resumption of this map.
