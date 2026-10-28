"""Convert a Dex extraction into a ``ConceptualModel`` with drawing graphics.

``dex_to_model`` runs ``check_extraction`` first, so a contract violation
raises ``DexExtractionError``. A mapping gap never raises: whatever cannot be
mapped is skipped and named in ``DexConversion.report``, and so is every
assumption the converter makes.

The rules:

- classes are coarse: the label picks the family root only (no text is read);
  an unknown label, ``insulation`` included, is skipped;
- a piping line with an ``instrument`` end is a sensing line, not a pipe;
  ``signal-line`` and ``data-line`` both become signals;
- a line flows from the end at its first point, unless its hint says ``reverse``;
- one ``PipingNetworkSystem`` per connected piping network, one
  ``PipingNetworkSegment`` per chain of lines between nozzles, off-page
  connectors, dead ends, tees and other branch points;
- graphics are sheet millimetres (origin bottom-left, y up), converted once
  from image pixels through the ``DrawingSize``.
"""

import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
from pydantic import BaseModel

from dexpigen.base import XY
from dexpigen.entities.base import Entity
from dexpigen.entities.equipment import EquipmentEntity
from dexpigen.entities.extraction import (
    DexExtraction,
    Direction,
    DrawingSize,
    NodeType,
    check_extraction,
)
from dexpigen.entities.segment import LineKind, SegmentEntity
from dexpigen.equipment import CustomEquipment, Nozzle
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    OperatedValveReference,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    Flange,
    FlowInPipeOffPageConnector,
    FlowOutPipeOffPageConnector,
    OperatedValve,
    Pipe,
    PipeOffPageConnector,
    PipeReducer,
    PipeTee,
    PipingComponent,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
)
from dexpigen.serialization import to_proteus_xml

# Coarse label -> in-line piping class. Off-page connectors and tees are typed by their lines.
_INLINE: dict[str, type[PipingComponent]] = {
    "valve": OperatedValve,
    "control-valve": OperatedValve,
    "flange": Flange,
    "reducer": PipeReducer,
}
_OFF_PAGE = "off-page-connector"
_MAPPED = {"equipment", "nozzle", "instrument", "actuator", _OFF_PAGE, *_INLINE}

type _Px = tuple[float, float]
type _Drawn = tuple[str, str, SegmentEntity]  # a line as drawn: its two ends and its Entity


@dataclass(frozen=True)
class DexConversion:
    """What ``dex_to_model`` returns: the model, and one report line per skipped or assumed thing."""

    model: ConceptualModel
    report: list[str]


def dex_to_model(
    graph: nx.Graph,
    entities: Iterable[Entity | BaseModel],
    size: DrawingSize | Mapping[str, Any] | BaseModel,
    *,
    model_id: str = "DexModel",
) -> DexConversion:
    """Convert one Dex extraction (its graph, Entities and drawing size) into a ``ConceptualModel``.

    Raises ``DexExtractionError`` when the input breaks the contract (see
    ``check_extraction``); everything else that cannot be mapped is in the report.
    """
    return _Converter(check_extraction(graph, entities, size), model_id).run()


def dex_to_proteus(
    graph: nx.Graph,
    entities: Iterable[Entity | BaseModel],
    size: DrawingSize | Mapping[str, Any] | BaseModel,
    *,
    model_id: str = "DexModel",
) -> str:
    """``dex_to_model`` followed by ``to_proteus_xml``; the report is dropped."""
    return to_proteus_xml(dex_to_model(graph, entities, size, model_id=model_id).model)


def _wire_id(prefix: str, raw: str) -> str:
    """A Proteus ``ID`` (an XML NCName) for an object made from an Entity or edge id."""
    return f"{prefix}-{re.sub(r'[^A-Za-z0-9_.-]', '_', raw)}"


@dataclass(frozen=True)
class _Line:
    """A drawn piping line in flow order: from ``source`` to ``target`` along ``points`` (px)."""

    segment: SegmentEntity
    source: str
    target: str
    points: list[_Px]


@dataclass
class _Network:
    """The piping lines with their ends: lines per node, and the in-line ports per (line, node)."""

    lines: list[_Line]
    at: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    incoming: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    outgoing: dict[str, list[int]] = field(default_factory=lambda: defaultdict(list))
    ports: dict[tuple[int, str], PipingNode] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for i, line in enumerate(self.lines):
            self.outgoing[line.source].append(i)
            self.incoming[line.target].append(i)
            self.at[line.source].append(i)
            self.at[line.target].append(i)


class _Converter:
    def __init__(self, extraction: DexExtraction, model_id: str) -> None:
        self.ex = extraction
        size = extraction.size
        self.scale = (size.drawing_width / size.image_width, size.drawing_height / size.image_height)
        self.height = size.drawing_height
        self.model = ConceptualModel(
            dex_id=model_id, drawing_extent=(size.drawing_width, size.drawing_height)
        )
        self.report: list[str] = []
        self.assumed: list[str] = []  # lines whose flow came from the point order
        self.skipped: set[str] = set()  # nodes already reported as skipped
        self.objects: dict[str, Any] = {}  # graph node -> the DEXPI object made for it

    def run(self) -> DexConversion:
        self._skip_unmapped_labels()
        self._equipment_and_nozzles()
        piping, sensing, signals = self._lines()
        self._piping(_Network(piping))
        for node, entity in self.ex.entities.items():
            if entity.label in (*_INLINE, _OFF_PAGE) and node not in self.objects and node not in self.skipped:
                self._skip(node, f"{entity.label} {node!r}: it is on no piping line")
        systems = self._actuators()
        self._signals(signals, systems)
        self._sensing(sensing)
        if self.assumed:
            listed = ", ".join(repr(edge) for edge in self.assumed)
            self.report.append(
                f"flow direction assumed from the point order for {len(self.assumed)} line(s): {listed}"
            )
        return DexConversion(model=self.model, report=self.report)

    # --- geometry -------------------------------------------------------------

    def _mm(self, point: _Px) -> XY:
        return (point[0] * self.scale[0], self.height - point[1] * self.scale[1])

    def _anchor(self, node: str) -> _Px:
        """A node's position in px: its point, equipment box centre or symbol quad centre."""
        if self.ex.node_type(node) is not NodeType.OBJECT:
            point = self.ex.point(node)
            return (point.x, point.y)
        entity = self.ex.entities[node]
        if isinstance(entity, EquipmentEntity):
            x0, y0, x1, y1 = entity.polygon.bounds
            return ((x0 + x1) / 2, (y0 + y1) / 2)
        return (sum(x for x, _ in entity.quad) / 4, sum(y for _, y in entity.quad) / 4)

    def _graphics(self, entity: Entity) -> dict[str, Any]:
        """``position`` and ``outline`` (mm) of the object made for ``entity``."""
        if isinstance(entity, EquipmentEntity):
            ring = list(entity.polygon.exterior.coords)
        else:
            ring = [*entity.quad, entity.quad[0]]
        return {
            "position": self._mm(self._anchor(entity.id)),
            "outline": [self._mm((x, y)) for x, y, *_ in ring],
        }

    def _starts_at(self, points: list[_Px], first: str, second: str) -> bool:
        """Whether ``points`` run from ``first`` to ``second`` rather than the other way."""
        a, b = self._anchor(first), self._anchor(second)
        straight = math.dist(points[0], a) + math.dist(points[-1], b)
        crossed = math.dist(points[0], b) + math.dist(points[-1], a)
        return straight <= crossed

    def _flow(self, u: str, v: str, segment: SegmentEntity) -> _Line:
        points = [(x, y) for x, y, *_ in segment.geometry.coords]
        start, end = (u, v) if self._starts_at(points, u, v) else (v, u)
        direction = self.ex.direction(u, v)
        if direction is Direction.REVERSE:
            return _Line(segment, end, start, points[::-1])
        if direction is not Direction.FORWARD:
            self.assumed.append(segment.id)
        return _Line(segment, start, end, points)

    # --- labels -----------------------------------------------------------------

    def _label(self, node: str) -> str:
        node_type = self.ex.node_type(node)
        return self.ex.entities[node].label if node_type is NodeType.OBJECT else node_type.value

    def _attached(self, node: str) -> list[str]:
        """The nodes joined to ``node`` by an attachment edge (no SegmentEntity)."""
        if node not in self.ex.graph:
            return []
        return [other for other in self.ex.graph[node] if self.ex.segment(node, other) is None]

    def _skip(self, node: str, why: str) -> None:
        self.skipped.add(node)
        self.report.append(f"skipped {why}")

    def _skip_unmapped_labels(self) -> None:
        for node, entity in self.ex.entities.items():
            if not isinstance(entity, SegmentEntity) and entity.label not in _MAPPED:
                self._skip(node, f"Entity {node!r} with label {entity.label!r}: no DEXPI class for this label")

    # --- equipment ------------------------------------------------------------

    def _equipment_and_nozzles(self) -> None:
        for node, entity in self.ex.entities.items():
            if entity.label == "equipment":  # an equipment outline, or a symbol labelled so
                equipment = CustomEquipment(
                    dex_id=_wire_id("CustomEquipment", node),
                    source_type_label=entity.label,
                    **self._graphics(entity),
                )
                self.objects[node] = equipment
                self.model.add_equipment(equipment)
        for node, entity in self.ex.entities.items():
            if entity.label != "nozzle":
                continue
            owners = [self.objects[n] for n in self._attached(node) if isinstance(self.objects.get(n), CustomEquipment)]
            if not owners:
                self._skip(node, f"nozzle {node!r}: it is attached to no equipment")
                continue
            nozzle = Nozzle(dex_id=_wire_id("Nozzle", node), **self._graphics(entity))
            nozzle.add_node(PipingNode(dex_id=f"{nozzle.dex_id}-Node1"))
            owners[0].add_nozzle(nozzle)
            self.objects[node] = nozzle

    # --- lines ----------------------------------------------------------------

    def _lines(self) -> tuple[list[_Line], list[_Drawn], list[_Drawn]]:
        """Piping lines in flow order, then sensing lines and signal lines as drawn."""
        piping: list[_Line] = []
        sensing: list[_Drawn] = []
        signals: list[_Drawn] = []
        for u, v in self.ex.graph.edges:
            segment = self.ex.segment(u, v)
            if segment is None:
                continue  # an attachment
            if u == v:
                self.report.append(f"skipped line {segment.id!r}: it starts and ends at {u!r}")
            elif segment.kind is not LineKind.PIPING:
                signals.append((u, v, segment))
            elif "instrument" in (self._label(u), self._label(v)):
                sensing.append((u, v, segment))
            else:
                piping.append(self._flow(u, v, segment))
        return piping, sensing, signals

    # --- piping ---------------------------------------------------------------

    def _piping(self, net: _Network) -> None:
        self._inline_items(net)
        pipes = [self._pipe(i, line, net) for i, line in enumerate(net.lines)]
        chains = self._chains(net)
        owner = self._segment_owners(net, chains)
        system_of, count = self._networks(net)
        systems = [PipingNetworkSystem(dex_id=f"PipingNetworkSystem-{s + 1}") for s in range(count)]
        for c, (chain, nodes) in enumerate(chains):
            segment = PipingNetworkSegment(dex_id=f"PipingNetworkSegment-{c + 1}")
            for node in dict.fromkeys(nodes):
                if owner.get(node) == c:
                    segment.add_item(self.objects[node])
            for i in chain:
                segment.add_connection(pipes[i])
            systems[system_of[chain[0]]].add_segment(segment)
        for system in systems:
            self.model.add_piping_network_system(system)

    def _inline_items(self, net: _Network) -> None:
        """Make the in-line objects, each with one port per line: incoming lines first."""
        for node, lines in net.at.items():
            item = self._inline_item(node, len(lines), bool(net.outgoing[node]))
            if item is None:
                continue
            self.objects[node] = item
            for k, i in enumerate([*net.incoming[node], *net.outgoing[node]], start=1):
                port = PipingNode(dex_id=f"{item.dex_id}-Node{k}")
                item.add_node(port)
                net.ports[(i, node)] = port
            if net.incoming[node]:
                item.flow_in_index = 1
            if net.outgoing[node]:
                item.flow_out_index = len(net.incoming[node]) + 1

    def _inline_item(self, node: str, lines: int, outgoing: bool) -> PipingComponent | PipeOffPageConnector | None:
        """The in-line object for ``node``: a tee, an in-line component or an off-page connector."""
        node_type = self.ex.node_type(node)
        if node_type is NodeType.JUNCTION:
            if lines != 3:
                self.report.append(f"junction {node!r} has {lines} piping line(s); a tee has three")
            return PipeTee(dex_id=_wire_id("PipeTee", node), position=self._mm(self._anchor(node)))
        if node_type is NodeType.DEADEND or node in self.skipped:
            return None
        entity = self.ex.entities[node]
        if entity.label in _INLINE:
            cls = _INLINE[entity.label]
            return cls(dex_id=_wire_id(cls.__name__, node), **self._graphics(entity))
        if entity.label == _OFF_PAGE:
            if lines != 1:
                self._skip(node, f"off-page connector {node!r}: it has {lines} piping lines, not one")
                return None
            cls = FlowInPipeOffPageConnector if outgoing else FlowOutPipeOffPageConnector
            return cls(dex_id=_wire_id(cls.__name__, node), **self._graphics(entity))
        return None  # a nozzle (it has its own node) or an object that holds no pipe

    def _pipe(self, i: int, line: _Line, net: _Network) -> Pipe:
        ends: list[tuple[Any, PipingNode | None]] = []
        for node in (line.source, line.target):
            item = self.objects.get(node)
            if isinstance(item, Nozzle):
                ends.append((item, item.nodes[0]))
            elif (i, node) in net.ports:
                ends.append((item, net.ports[(i, node)]))
            else:
                ends.append((None, None))
                if self.ex.node_type(node) is NodeType.OBJECT and node not in self.skipped:
                    self.report.append(
                        f"pipe {line.segment.id!r}: its end {node!r} ({self._label(node)!r}) "
                        "cannot hold a pipe; that end is left open"
                    )
        if ends[0][0] is None and ends[1][0] is None:
            self.report.append(f"pipe {line.segment.id!r} has no item at either end")
        points = [self._mm(point) for point in line.points]
        for (_, port), point in zip(ends, (points[0], points[-1]), strict=True):
            if port is not None and port.position is None:
                port.position = point
        (source, source_node), (target, target_node) = ends
        return Pipe(
            dex_id=_wire_id("Pipe", line.segment.id),
            source_item=source,
            source_node=source_node,
            target_item=target,
            target_node=target_node,
            center_line=points,
        )

    def _inline(self, node: str, net: _Network) -> bool:
        """Whether a segment runs through ``node``: a two-port in-line component."""
        item = self.objects.get(node)
        return isinstance(item, PipingComponent) and not isinstance(item, PipeTee) and len(net.at[node]) == 2

    def _chains(self, net: _Network) -> list[tuple[list[int], list[str]]]:
        """Chains of lines through two-port in-line items, cut everywhere else: (lines, nodes)."""
        used: set[int] = set()
        chains: list[tuple[list[int], list[str]]] = []

        def walk(start: str, first: int) -> tuple[list[int], list[str]]:
            chain, nodes, node, i = [], [start], start, first
            while True:
                used.add(i)
                chain.append(i)
                line = net.lines[i]
                node = line.target if line.source == node else line.source
                nodes.append(node)
                following = next((j for j in net.at[node] if j not in used), None) if self._inline(node, net) else None
                if following is None:
                    return chain, nodes
                i = following

        for node, lines in net.at.items():
            if not self._inline(node, net):
                chains.extend(walk(node, i) for i in lines if i not in used)
        for i, line in enumerate(net.lines):  # a closed loop of in-line items only
            if i not in used:
                chains.append(walk(line.source, i))
        return chains

    def _segment_owners(self, net: _Network, chains: list[tuple[list[int], list[str]]]) -> dict[str, int]:
        """The chain each in-line object belongs to: its own, or for a chain end (tee,
        off-page connector, end flange) the first chain flowing into it, else the first reaching it."""
        items = {node for _, node in net.ports}
        owner: dict[str, int] = {}
        for c, (_, nodes) in enumerate(chains):
            for node in nodes:
                if self._inline(node, net):
                    owner.setdefault(node, c)
        ends = [(c, nodes[k], chain[k]) for c, (chain, nodes) in enumerate(chains) for k in (0, -1)]
        for c, node, i in ends:
            if node in items and net.lines[i].target == node:
                owner.setdefault(node, c)
        for c, node, _ in ends:
            if node in items:
                owner.setdefault(node, c)
        return owner

    def _networks(self, net: _Network) -> tuple[dict[int, int], int]:
        """The connected piping network of every line, numbered in line order, and their count."""
        network_of: dict[int, int] = {}
        count = 0
        for i in range(len(net.lines)):
            if i in network_of:
                continue
            network_of[i], stack = count, [i]
            while stack:
                line = net.lines[stack.pop()]
                for node in (line.source, line.target):
                    for k in net.at[node]:
                        if k not in network_of:
                            network_of[k] = count
                            stack.append(k)
            count += 1
        return network_of, count

    # --- instrumentation --------------------------------------------------------

    def _actuators(self) -> dict[str, ActuatingSystem]:
        """Make the PIFs and, per actuator, its ActuatingSystem (returned by actuator node)."""
        pifs = 0
        for node, entity in self.ex.entities.items():
            if entity.label == "instrument":
                pif = ProcessInstrumentationFunction(
                    dex_id=_wire_id("ProcessInstrumentationFunction", node), **self._graphics(entity)
                )
                self.model.add_process_instrumentation_function(pif)
                self.objects[node] = pif
                pifs += 1
        if pifs:
            self.report.append(f"{pifs} instrument(s) without number, category or loop: no text is read")

        systems: dict[str, ActuatingSystem] = {}
        for node, entity in self.ex.entities.items():
            if entity.label != "actuator":
                continue
            system = ActuatingSystem(dex_id=_wire_id("ActuatingSystem", node))
            system.add_controlled_actuator(
                ControlledActuator(dex_id=_wire_id("ControlledActuator", node), **self._graphics(entity))
            )
            valves = [self.objects[n] for n in self._attached(node) if isinstance(self.objects.get(n), OperatedValve)]
            if valves:
                system.add_operated_valve_reference(
                    OperatedValveReference(dex_id=_wire_id("OperatedValveReference", node), valve=valves[0])
                )
            else:
                self.report.append(f"actuator {node!r} is attached to no converted valve: its system has no valve")
            self.model.add_actuating_system(system)
            systems[node] = system
        return systems

    def _signals(self, signals: list[_Drawn], systems: dict[str, ActuatingSystem]) -> None:
        functions: dict[str, ActuatingFunction] = {}  # actuator -> its function, under the first PIF
        for u, v, segment in signals:
            labels = (self._label(u), self._label(v))
            if sorted(labels) == ["actuator", "instrument"]:
                instrument, actuator = (u, v) if labels[0] == "instrument" else (v, u)
                pif = self.objects[instrument]
                function = functions.get(actuator)
                if function is None:
                    function = ActuatingFunction(
                        dex_id=_wire_id("ActuatingFunction", actuator), systems=systems[actuator]
                    )
                    pif.add_actuating_function(function)
                    functions[actuator] = function
                points = [(x, y) for x, y, *_ in segment.geometry.coords]
                if not self._starts_at(points, instrument, actuator):
                    points.reverse()
                source, target = pif, function
            elif labels == ("instrument", "instrument"):
                line = self._flow(u, v, segment)
                source, target, points = self.objects[line.source], self.objects[line.target], line.points
            else:
                self.report.append(
                    f"skipped signal line {segment.id!r} between {labels[0]!r} and {labels[1]!r}: "
                    "only instrument-actuator and instrument-instrument signals are mapped"
                )
                continue
            source.add_signal_conveying_function(
                SignalConveyingFunction(
                    dex_id=_wire_id("SignalConveyingFunction", segment.id),
                    source=source,
                    target=target,
                    center_line=[self._mm(point) for point in points],
                )
            )
        for actuator in systems:
            if actuator not in functions:
                self.report.append(f"actuator {actuator!r} receives no signal: its system has no actuating function")

    def _sensing(self, sensing: list[_Drawn]) -> None:
        for u, v, segment in sensing:
            instrument, other = (u, v) if self._label(u) == "instrument" else (v, u)
            location = self.objects.get(other)
            if self._label(other) == "instrument" or not isinstance(location, Nozzle | PipingComponent):
                self.report.append(
                    f"skipped sensing line {segment.id!r}: its end {other!r} ({self._label(other)!r}) "
                    "is not a converted nozzle or piping component"
                )
                continue
            self.objects[instrument].add_process_signal_generating_function(
                ProcessSignalGeneratingFunction(
                    dex_id=_wire_id("ProcessSignalGeneratingFunction", segment.id), sensing_location=location
                )
            )
