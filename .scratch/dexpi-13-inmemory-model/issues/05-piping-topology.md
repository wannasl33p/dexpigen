# Decide MainProcessLine piping topology

Type: grilling
Status: resolved
Blocked by: 01

## Question

A MainProcessLine in extraction is a process-pipe edge. In DEXPI 1.3, piping is typically a PipingNetworkSystem of PipingNetworkSegments connected through piping connections and components (flange, reducer, spectacle blind, valve, off-page connector).

What subset of that topology is in v0.1, and which objects own which references? What is required versus optional for a “line” that has no geometry?

## Answer

### Ownership

- `PipingNetworkSystem` is the line. Its only composition is `segments`. `lineNumber` is optional `str | None`; the model does **not** enforce uniqueness or 1:1 `lineNumber` → system.
- `PipingNetworkSegment` is a stretch of that line. Its identifier is `segmentNumber`, not `lineNumber`.
- `Pipe` lives in `segment.connections` when there is an actual piping connection between endpoints.
- Flange, reducer, line-blind / spectacle-blind, operated valve: `PipingNetworkSegment.items`.
- Off-page connector is a `PipingNetworkSegmentItem` (`FlowInPipeOffPageConnector` / `FlowOutPipeOffPageConnector`). If it belongs to the segment it is in `items`. `sourceItem` / `targetItem` **reference** it (internal first/last item) or an external object (e.g. equipment `Nozzle`).

### Line without geometry

A usable construction is `PipingNetworkSystem` + at least one `PipingNetworkSegment` so items and connectors have an owner. Zero segments remains DEXPI-valid Pydantic; one-segment systems in tests are fixture convenience, not a DEXPI rule.

### Mapper vs model

| Claim | Layer |
| --- | --- |
| One system contains many segments | model |
| Known line number → one system | mapper / P&ID convention |
| No number → one system per extraction edge | mapper only |

Jacket line numbers are a separate case, not extra segments of the same system.

## Comments

- Extraction `MainProcessLine` aliases `PipingNetworkSystem`.
