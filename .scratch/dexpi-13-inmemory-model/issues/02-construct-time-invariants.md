# Catalogue construct-time invariants for v0.1 classes

Type: research
Status: resolved
Blocked by: 01

## Question

For each class in the v0.1 set, which DEXPI 1.3 constraints can be enforced when constructing an in-memory object, without XML?

Cover at least: required vs optional attributes, cardinalities, allowed reference targets, composition vs reference, uniqueness of InstanceId, nozzle ownership, piping connectivity rules that are conceptual (not graphical), instrumentation/signal attachment rules.

Primary sources: DEXPI P&ID Specification 1.3. Do not read pyDEXPI source.

Write findings to `.scratch/dexpi-13-inmemory-model/research/02-construct-time-invariants.md` with citations.

## Answer

The official and project-level constraints are separated in the [construct-time invariant catalogue](../research/02-construct-time-invariants.md). The strongest DEXPI rules concern composition ownership, typed reference endpoints, nozzle/chamber ownership, connection-node ownership, and `OperatedValveReference` target type. UUID uniqueness is our policy, not a DEXPI 1.3 rule.

## Comments

Result: [construct-time invariant catalogue](../research/02-construct-time-invariants.md).
