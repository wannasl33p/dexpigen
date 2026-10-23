# Piping classes

Piping network systems and segments, connections, nodes, valves, fittings and off-page connectors.

Generated from `dexpigen.piping` by `scripts/gen_reference.py`; do not edit by hand.

## Contents

- [PipingNode](#pipingnode)
- [PipingNodeOwner](#pipingnodeowner)
  - [PipingSourceItem](#pipingsourceitem)
  - [PipingTargetItem](#pipingtargetitem)
- [SensingLocation](#sensinglocation)
  - [PipingNetworkSegment](#pipingnetworksegment)
- [PipingConnection](#pipingconnection)
  - [Pipe](#pipe)
- [PipingNetworkSegmentItem](#pipingnetworksegmentitem)
  - [PipingComponent](#pipingcomponent)
    - [OperatedValve](#operatedvalve)
      - [BallValve](#ballvalve)
      - [GlobeValve](#globevalve)
      - [ButterflyValve](#butterflyvalve)
      - [NeedleValve](#needlevalve)
      - [GateValve](#gatevalve)
    - [CheckValve](#checkvalve)
    - [SafetyValveOrFitting](#safetyvalveorfitting)
    - [FlowMeasuringElement](#flowmeasuringelement)
    - [PipeFitting](#pipefitting)
      - [Flange](#flange)
      - [PipeTee](#pipetee)
      - [PipeReducer](#pipereducer)
      - [LineBlind](#lineblind)
  - [PipeOffPageConnector](#pipeoffpageconnector)
    - [FlowInPipeOffPageConnector](#flowinpipeoffpageconnector)
    - [FlowOutPipeOffPageConnector](#flowoutpipeoffpageconnector)
- [PipeOffPageConnectorReference](#pipeoffpageconnectorreference)
  - [PipeOffPageConnectorObjectReference](#pipeoffpageconnectorobjectreference)
  - [PipeOffPageConnectorReferenceByNumber](#pipeoffpageconnectorreferencebynumber)
- [PipingNetworkSystem](#pipingnetworksystem)

## Classes

### PipingNode

A connection point owned by a `PipingNodeOwner`.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

No own fields.

### PipingNodeOwner

Abstract role: composes `PipingNode` connection points.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `nodes` | list[[PipingNode](#pipingnode)] | `[]` | composed |
| `flow_in_index` | int \| None | `None` |  |
| `flow_out_index` | int \| None | `None` |  |

### PipingSourceItem

Abstract role: a valid piping source item.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [PipingNodeOwner](#pipingnodeowner)
- Abstract: yes

No own fields.

### PipingTargetItem

Abstract role: a valid piping target item.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [PipingNodeOwner](#pipingnodeowner)
- Abstract: yes

No own fields.

### SensingLocation

Abstract role: a piping object a process signal generating function can be located in (`Nozzle`, `PipingComponent`, `PipingNetworkSegment`).

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

No own fields.

### PipingNetworkSegment

A stretch of a `PipingNetworkSystem`.

- ComponentClass: `PipingNetworkSegment`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS267704`
- Bases: [SensingLocation](#sensinglocation)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `segment_number` | str \| None | `None` |  |
| `fluid_code` | str \| None | `None` |  |
| `piping_class_code` | str \| None | `None` |  |
| `items` | list[[PipingNetworkSegmentItem](#pipingnetworksegmentitem)] | `[]` | composed |
| `connections` | list[[PipingConnection](#pipingconnection)] | `[]` | composed |

### PipingConnection

Abstract base for a piping connection between two endpoints.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `source_item` | [PipingSourceItem](#pipingsourceitem) \| None | `None` | ref |
| `source_node` | [PipingNode](#pipingnode) \| None | `None` | ref |
| `target_item` | [PipingTargetItem](#pipingtargetitem) \| None | `None` | ref |
| `target_node` | [PipingNode](#pipingnode) \| None | `None` | ref |

### Pipe

A concrete piping connection between two endpoints.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [PipingConnection](#pipingconnection)
- Abstract: no

No own fields.

### PipingNetworkSegmentItem

Abstract role: an in-line item composed in a segment's `items`.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

No own fields.

### PipingComponent

Abstract base for an in-line piping component (valve or fitting).

- ComponentClass: -
- ComponentClassURI: -
- Bases: [PipingNetworkSegmentItem](#pipingnetworksegmentitem), [PipingSourceItem](#pipingsourceitem), [PipingTargetItem](#pipingtargetitem), [SensingLocation](#sensinglocation)
- Abstract: yes

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `fluid_code` | str \| None | `None` |  |
| `on_hold` | [OnHoldClassification](enumerations.md#onholdclassification) \| None | `None` |  |
| `piping_class_artefact` | [PipingClassArtefactClassification](enumerations.md#pipingclassartefactclassification) \| None | `None` |  |
| `pressure_test_circuit_number` | str \| None | `None` |  |
| `piping_component_name` | str \| None | `None` |  |
| `piping_component_number` | str \| None | `None` |  |

### OperatedValve

Concrete family root and fallback for an unspecified operated valve.

- ComponentClass: `OperatedValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS11141590`
- Bases: [PipingComponent](#pipingcomponent)
- Abstract: no

No own fields.

### BallValve

- ComponentClass: `BallValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS416654`
- Bases: [OperatedValve](#operatedvalve)
- Abstract: no

No own fields.

### GlobeValve

- ComponentClass: `GlobeValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS416204`
- Bases: [OperatedValve](#operatedvalve)
- Abstract: no

No own fields.

### ButterflyValve

- ComponentClass: `ButterflyValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS416609`
- Bases: [OperatedValve](#operatedvalve)
- Abstract: no

No own fields.

### NeedleValve

- ComponentClass: `NeedleValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS421064`
- Bases: [OperatedValve](#operatedvalve)
- Abstract: no

No own fields.

### GateValve

- ComponentClass: `GateValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS416519`
- Bases: [OperatedValve](#operatedvalve)
- Abstract: no

No own fields.

### CheckValve

Concrete family root and fallback for an unspecified check valve.

- ComponentClass: `CheckValve`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS292229`
- Bases: [PipingComponent](#pipingcomponent)
- Abstract: no

No own fields.

### SafetyValveOrFitting

Concrete family root and fallback for an unspecified safety valve/fitting.

- ComponentClass: `SafetyValveOrFitting`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/SafetyValveOrFitting`
- Bases: [PipingComponent](#pipingcomponent)
- Abstract: no

No own fields.

### FlowMeasuringElement

An in-line flow measuring element, a sensing location for a flow signal.

- ComponentClass: `FlowMeasuringElement`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/FlowMeasuringElement`
- Bases: [PipingComponent](#pipingcomponent)
- Abstract: no

No own fields.

### PipeFitting

Abstract base for pipe fittings (flange, reducer, line blind).

- ComponentClass: -
- ComponentClassURI: -
- Bases: [PipingComponent](#pipingcomponent)
- Abstract: yes

No own fields.

### Flange

- ComponentClass: `Flange`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS13307654`
- Bases: [PipeFitting](#pipefitting)
- Abstract: no

No own fields.

### PipeTee

- ComponentClass: `PipeTee`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS427724`
- Bases: [PipeFitting](#pipefitting)
- Abstract: no

No own fields.

### PipeReducer

- ComponentClass: `PipeReducer`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS416294`
- Bases: [PipeFitting](#pipefitting)
- Abstract: no

No own fields.

### LineBlind

- ComponentClass: `LineBlind`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS280034`
- Bases: [PipeFitting](#pipefitting)
- Abstract: no

No own fields.

### PipeOffPageConnector

Abstract base for a pipe off-page connector.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [PipingNetworkSegmentItem](#pipingnetworksegmentitem), [PipingNodeOwner](#pipingnodeowner)
- Abstract: yes

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `connector_reference` | [PipeOffPageConnectorReference](#pipeoffpageconnectorreference) \| None | `None` | composed |

### FlowInPipeOffPageConnector

A pipe off-page connector that is a valid piping source.

- ComponentClass: `FlowInPipeOffPageConnector`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/FlowInPipeOffPageConnector`
- Bases: [PipeOffPageConnector](#pipeoffpageconnector), [PipingSourceItem](#pipingsourceitem)
- Abstract: no

No own fields.

### FlowOutPipeOffPageConnector

A pipe off-page connector that is a valid piping target.

- ComponentClass: `FlowOutPipeOffPageConnector`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/FlowOutPipeOffPageConnector`
- Bases: [PipeOffPageConnector](#pipeoffpageconnector), [PipingTargetItem](#pipingtargetitem)
- Abstract: no

No own fields.

### PipeOffPageConnectorReference

Abstract base for a reference to a pipe off-page connector.

- ComponentClass: -
- ComponentClassURI: -
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: yes

No own fields.

### PipeOffPageConnectorObjectReference

A reference to a `PipeOffPageConnector` object.

- ComponentClass: `PipeOffPageConnectorObjectReference`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/PipeOffPageConnectorObjectReference`
- Bases: [PipeOffPageConnectorReference](#pipeoffpageconnectorreference)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `referenced_connector` | [PipeOffPageConnector](#pipeoffpageconnector) \| None | `None` | ref |

### PipeOffPageConnectorReferenceByNumber

A reference to a pipe off-page connector by drawing and connector number.

- ComponentClass: `PipeOffPageConnectorReferenceByNumber`
- ComponentClassURI: `http://sandbox.dexpi.org/rdl/PipeOffPageConnectorReferenceByNumber`
- Bases: [PipeOffPageConnectorReference](#pipeoffpageconnectorreference)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `referenced_connector_number` | str \| None | `None` |  |
| `referenced_drawing_number` | str \| None | `None` |  |

### PipingNetworkSystem

The DEXPI line object, composed of `PipingNetworkSegment` objects.

- ComponentClass: `PipingNetworkSystem`
- ComponentClassURI: `http://data.posccaesar.org/rdl/RDS270359`
- Bases: [DexpiBaseModel](model.md#dexpibasemodel)
- Abstract: no

| Field | Type | Default | Relation |
| --- | --- | --- | --- |
| `line_number` | str \| None | `None` |  |
| `fluid_code` | str \| None | `None` |  |
| `piping_class_code` | str \| None | `None` |  |
| `segments` | list[[PipingNetworkSegment](#pipingnetworksegment)] | `[]` | composed |
