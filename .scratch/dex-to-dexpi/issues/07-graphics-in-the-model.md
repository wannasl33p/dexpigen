# Decide how the model carries graphics

Type: grilling
Status: resolved
Assignee: alex.valentsinovich
Blocked by: 01-proteus-graphics-minimum

## Question

Given the minimal Proteus graphics set, how does the library carry and write geometry? Options include optional position/extent fields on plant items, a separate graphics layer keyed by object, or graphics produced by the writer straight from the Dex extraction. Decide where line geometry (`CenterLine`) lives, how the "no graphics" rule in the v0.1 spec and in `CLAUDE.md` is amended, and how graphics appear in the generated class index and in model checks.

Input from [Research the minimum Proteus graphics](01-proteus-graphics-minimum.md): no blocker. Decide on that basis:
- whether shapes are written (a `ShapeCatalogue`, or inline `PolyLine` from the Dex polygon), given that items without a shape are invisible in a renderer;
- how `Reference` (rotation) is derived;
- one `Connection` per Pipe (ours) or per segment (C01);
- the per-kind symbol-origin offsets.

## Answer

Resolved by a fast-path grilling with the user on 2026-10-28 (one round of multiple-choice questions; defaults taken by the orchestrator are marked).

- **Where graphics live (user's choice):** optional fields on the model objects, default `None`. Not a separate layer, and not written straight from the Dex extraction. The fields are `position` and `outline` on equipment, nozzles, piping components, off-page connectors, PIFs, controlled actuators and positioners; `position` on `PipingNode`; `center_line` on `Pipe` and `SignalConveyingFunction`; and `drawing_extent` on `ConceptualModel`. Units are millimetres, origin bottom-left, y up (spec).
- **Pixels to millimetres (taken by default):** pixels go to millimetres through `DrawingSize` with y flipped; the formula is in section C of the spec.
- **Writer (user's choice):** `Position` in each item, each pipe's `CenterLine` in its segment, the signal `CenterLine` as the last child of its `InformationFlow`, and a `Drawing` with the sheet extent as the last child of `PlantModel`. Every `CenterLine` and `PolyLine` writes `NumPoints`, which the XSD requires; the spec's signal example leaves it out, and the writer must not.
- **Connections (spec):** one `Connection` per `Pipe`, as now. The XSD gives `Connection` no child elements, which is why the pipe's `CenterLine` goes in its segment.
- **Visibility (user's choice):** an inline `PolyLine` outline from the Entity quad or polygon ring. C01 instead keeps its shapes in a `ShapeCatalogue` (reference XML line 6230) and names them per item with `ComponentName`, so this departs from C01.
- **Rotation (user's choice):** none. `Reference` is (1, 0, 0), and the anchor is the box centre (quad centre for symbols, polygon bbox centre for equipment).
- **Symbol origins (user's choice):** no per-kind offset; every symbol sits at its quad centre, equipment at its box centre. On C01 that is 0 mm for equipment, PIFs and in-line items, and the known constant 2 mm for nozzles and 4 mm for actuators, which C01 places at the equipment end and the valve stem.
- **Element order (taken by default):** as in the XSD-validated research sample `research/01-samples/02-drawable.xml`: `PolyLine` and `Position` first in an item, the pipe `CenterLine`s before the segment's items, the signal `CenterLine` last in its `InformationFlow`. C01's own order differs (reference XML line 2289), and the XSD's unbounded choices make every order valid.
- **Actuator graphics (taken by default):** the actuator symbol's position and outline go on its `ControlledActuator`; the `ActuatingSystem` carries none, as in C01.
- **Rules and docs (taken by default):** `CLAUDE.md`, `README.md`, the serialize-and-validate recipe and the v0.1 spec now say graphics are optional fields. The class index shows the abstract role `GraphicItem` (`position`, `outline`) and the fields `PipingNode.position`, `PipingConnection.center_line`, `SignalConveyingFunction.center_line` and `ConceptualModel.drawing_extent`, typed with the aliases `XY` and `Points`. Model checks do not look at graphics.
