"""Proteus XML serializer for the DEXPI 1.3 in-memory model.

``to_proteus_xml`` walks a ``ConceptualModel`` and returns the Proteus XML
string: the document skeleton, polymorphic element tags, ``GenericAttributes``
for data fields, nested elements for composition, and ``Association`` for
references (emitted on both endpoints). It is a writer — no XSD validation,
no round-trip gate. After generating, validate the output with
``examples/validate_dexpi.py``.

Before writing, ``to_proteus_xml`` checks the model graph for the mistakes the
construction API cannot see (see ``_check_model``): an object composed twice or
appended to a composition list in place, a ``dex_id`` that is not a unique XML
``NCName``, and a reference to an object that is not composed in the model.
"""

from __future__ import annotations

import re
from typing import Any

from dexpigen.base import Composed, CustomAttribute, DexpiBaseModel, Ref, relation_of
from dexpigen.enumerations import FailActionClassification
from dexpigen.equipment import Chamber, Equipment, Nozzle
from dexpigen.instrumentation import (
    ActuatingFunction,
    ActuatingSystem,
    ControlledActuator,
    InstrumentationLoopFunction,
    OperatedValveReference,
    Positioner,
    ProcessInstrumentationFunction,
    ProcessSignalGeneratingFunction,
    SignalConveyingFunction,
    SignalConveyingFunctionSource,
    SignalConveyingFunctionTarget,
    SignalOffPageConnector,
)
from dexpigen.model import ConceptualModel
from dexpigen.piping import (
    Pipe,
    PipeOffPageConnector,
    PipeOffPageConnectorObjectReference,
    PipeOffPageConnectorReference,
    PipeOffPageConnectorReferenceByNumber,
    PipingComponent,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PipingNode,
    SensingLocation,
)

SANDBOX = "http://sandbox.dexpi.org/rdl/"

PLANT_INFORMATION: dict[str, str] = {
    "Application": "Dexpi",
    "ApplicationVersion": "1.3.1",
    "Date": "2022-11-04",
    "Discipline": "PID",
    "Is3D": "no",
    "OriginatingSystem": "P&ID Toolbox",
    "OriginatingSystemVendor": "pnb plants & bytes GmbH, Aachen, Germany",
    "OriginatingSystemVersion": "1.1.0",
    "SchemaVersion": "4.1.1",
    "Time": "20:30:49.613611",
    "Units": "mm",
}

FAIL_ACTION_URI = {
    "FailClose": "http://data.posccaesar.org/rdl/RDS5921400",
    "FailOpen": "http://data.posccaesar.org/rdl/RDS5921445",
    "FailRetainPosition": "http://data.posccaesar.org/rdl/RDS5921464",
}

# Global RDL declaration order (from the reference examples), used to sort the
# GenericAttributes within an element. Unknown names sort last, stably.
RDL_ORDER: dict[str, int] = {
    name: i
    for i, name in enumerate(
        [
            "ActuatingSystemNumberAssignmentClass",
            "ActuatingFunctionNumberAssignmentClass",
            "DeviceTypeNameAssignmentClass",
            "FailActionSpecialization",
            "FailActionRepresentationAssignmentClass",
            "SubTagNameAssignmentClass",
            "FluidCodeAssignmentClass",
            "InsulationThickness",
            "InsulationTypeAssignmentClass",
            "LineNumberAssignmentClass",
            "NominalDiameterNumericalValueRepresentationAssignmentClass",
            "NominalDiameterRepresentationAssignmentClass",
            "NominalDiameterStandardSpecialization",
            "NominalDiameterTypeRepresentationAssignmentClass",
            "PipingClassCodeAssignmentClass",
            "PrimarySecondaryPipingNetworkSegmentSpecialization",
            "SegmentNumberAssignmentClass",
            "PipingComponentNameAssignmentClass",
            "PipingComponentNumberAssignmentClass",
            "PressureTestCircuitNumberAssignmentClass",
            "LocationSpecialization",
            "ProcessInstrumentationFunctionCategoryAssignmentClass",
            "ProcessInstrumentationFunctionNumberAssignmentClass",
            "ProcessInstrumentationFunctionModifierAssignmentClass",
            "ProcessInstrumentationFunctionsAssignmentClass",
            "DesignHeatFlowRate",
            "DesignHeatTransferArea",
            "PlateHeight",
            "PlateWidth",
            "DesignPressureHead",
            "DesignRotationalSpeed",
            "DesignShaftPower",
            "DesignVolumeFlowRate",
            "CylinderLength",
            "NominalCapacity(Volume)",
            "TagNameAssignmentClass",
            "TagNamePrefixAssignmentClass",
            "TagNameSequenceNumberAssignmentClass",
            "TagNameSuffixAssignmentClass",
            "EquipmentDescriptionAssignmentClass",
            "LowerLimitDesignPressure",
            "LowerLimitDesignTemperature",
            "MaterialOfConstructionCodeAssignmentClass",
            "NominalDiameter",
            "UpperLimitDesignPressure",
            "UpperLimitDesignTemperature",
            "TypicalInformationAssignmentClass",
        ]
    )
}


def _esc(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _attrs(**kw: Any) -> str:
    return "".join(f' {k}="{_esc(str(v))}"' for k, v in kw.items())


def _item_attrs(obj: DexpiBaseModel, component_class: str) -> str:
    """Identity attributes of a plant item: ID, ComponentClass(URI), ComponentName.

    ``ComponentName`` is a Proteus-level attribute, emitted only when set.
    """
    extra: dict[str, str] = {}
    if obj.component_name is not None:
        extra["ComponentName"] = obj.component_name
    return _attrs(
        ID=obj.dex_id, ComponentClass=component_class,
        ComponentClassURI=obj.component_class_uri, **extra,
    )


class _Writer:
    def __init__(self) -> None:
        self._lines: list[str] = []
        self._depth = 0

    def _ind(self) -> str:
        return "  " * self._depth

    def open(self, tag: str, attrs: str) -> None:
        self._lines.append(f"{self._ind()}<{tag}{attrs}>")
        self._depth += 1

    def close(self, tag: str) -> None:
        self._depth -= 1
        self._lines.append(f"{self._ind()}</{tag}>")

    def leaf(self, tag: str, attrs: str) -> None:
        self._lines.append(f"{self._ind()}<{tag}{attrs}/>")

    def text(self) -> str:
        return "\n".join(self._lines) + "\n"


def _assignment_class(field: str) -> str:
    return f"{field}AssignmentClass"


def _string(field: str, value: Any, *, keep_empty: bool = False) -> CustomAttribute | None:
    if value is None or (value == "" and not keep_empty):
        return None
    return CustomAttribute(name=_assignment_class(field), value=str(value))


def _field_attributes(obj: DexpiBaseModel) -> list[CustomAttribute]:
    """First-class data fields as GenericAttribute entries."""
    attrs: list[CustomAttribute] = []

    def add(a: CustomAttribute | None) -> None:
        if a is not None:
            attrs.append(a)

    if isinstance(obj, Equipment):
        add(_string("TagNameSuffix", obj.tag_name_suffix, keep_empty=True))
        add(_string("TagNameSequenceNumber", obj.tag_name_sequence_number))
        add(_string("TagNamePrefix", obj.tag_name_prefix))
        add(_string("TagName", obj.tag_name))
        add(_string("EquipmentDescription", obj.equipment_description))
    elif isinstance(obj, Nozzle):
        add(_string("SubTagName", obj.sub_tag_name))
    elif isinstance(obj, Chamber):
        add(_string("SubTagName", obj.sub_tag_name))
    elif isinstance(obj, PipingNetworkSystem):
        add(_string("PipingClassCode", obj.piping_class_code))
        add(_string("LineNumber", obj.line_number))
        add(_string("FluidCode", obj.fluid_code))
    elif isinstance(obj, PipingNetworkSegment):
        add(_string("SegmentNumber", obj.segment_number))
        add(_string("PipingClassCode", obj.piping_class_code))
        add(_string("FluidCode", obj.fluid_code))
    elif isinstance(obj, PipingComponent):
        add(_string("PipingComponentNumber", obj.piping_component_number))
        add(_string("PipingComponentName", obj.piping_component_name))
        add(_string("PressureTestCircuitNumber", obj.pressure_test_circuit_number))
        add(_string("FluidCode", obj.fluid_code))
    elif isinstance(obj, ActuatingSystem):
        add(_string("TypicalInformation", obj.typical_information))
        add(_string("ActuatingSystemNumber", obj.actuating_system_number))
    elif isinstance(obj, ControlledActuator):
        add(_string("SubTagName", obj.sub_tag_name))
        add(_string("FailActionRepresentation", obj.fail_action_representation))
        if isinstance(obj.fail_action, FailActionClassification):
            v = obj.fail_action.value
            attrs.append(CustomAttribute(
                name="FailActionSpecialization", value=v, format="anyURI",
                value_uri=FAIL_ACTION_URI.get(v),
            ))
        add(_string("DeviceTypeName", obj.device_type_name))
    elif isinstance(obj, OperatedValveReference):
        add(_string("SubTagName", obj.sub_tag_name))
    elif isinstance(obj, Positioner):
        add(_string("SubTagName", obj.sub_tag_name))
        add(_string("DeviceTypeName", obj.device_type_name))
    elif isinstance(obj, ActuatingFunction):
        add(_string("ActuatingFunctionNumber", obj.actuating_function_number))
    elif isinstance(obj, ProcessInstrumentationFunction):
        add(_string("ProcessInstrumentationFunctions", obj.process_instrumentation_functions_code))
        add(_string("ProcessInstrumentationFunctionModifier", obj.process_instrumentation_function_modifier))
        add(_string("ProcessInstrumentationFunctionNumber", obj.process_instrumentation_function_number))
        add(_string("ProcessInstrumentationFunctionCategory", obj.process_instrumentation_function_category))
    elif isinstance(obj, ProcessSignalGeneratingFunction):
        add(_string("ProcessSignalGeneratingFunctionNumber", obj.process_signal_generating_function_number))
        add(_string("SensorType", obj.sensor_type))
    elif isinstance(obj, InstrumentationLoopFunction):
        add(_string("InstrumentationLoopFunctionNumber", obj.instrumentation_loop_function_number))
    elif isinstance(obj, PipeOffPageConnectorReferenceByNumber):
        add(_string("ReferencedConnectorNumber", obj.referenced_connector_number))
        add(_string("ReferencedDrawingNumber", obj.referenced_drawing_number))

    return attrs


# Per-class GenericAttribute declaration order (from the reference examples).
# A name's position differs between classes (e.g. SubTagName), so the order is
# per class, not a single global list.
CLASS_ORDER: dict[str, list[str]] = {
    "Equipment": [
        "DesignHeatFlowRate", "DesignHeatTransferArea", "PlateHeight", "PlateWidth",
        "DesignPressureHead", "DesignRotationalSpeed", "DesignShaftPower",
        "DesignVolumeFlowRate", "CylinderLength", "NominalCapacity(Volume)",
        "TagNameAssignmentClass", "TagNamePrefixAssignmentClass",
        "TagNameSequenceNumberAssignmentClass", "TagNameSuffixAssignmentClass",
        "EquipmentDescriptionAssignmentClass",
    ],
    "Chamber": [
        "LowerLimitDesignPressure", "LowerLimitDesignTemperature",
        "MaterialOfConstructionCodeAssignmentClass", "NominalDiameter",
        "NominalDiameterTypeRepresentationAssignmentClass", "SubTagNameAssignmentClass",
        "UpperLimitDesignPressure", "UpperLimitDesignTemperature",
    ],
    "Nozzle": ["SubTagNameAssignmentClass"],
    "PipingNetworkSystem": [
        "FluidCodeAssignmentClass", "InsulationThickness", "InsulationTypeAssignmentClass",
        "LineNumberAssignmentClass", "NominalDiameterNumericalValueRepresentationAssignmentClass",
        "NominalDiameterRepresentationAssignmentClass", "NominalDiameterStandardSpecialization",
        "NominalDiameterTypeRepresentationAssignmentClass", "PipingClassCodeAssignmentClass",
    ],
    "PipingNetworkSegment": [
        "FluidCodeAssignmentClass", "InsulationThickness", "InsulationTypeAssignmentClass",
        "NominalDiameterNumericalValueRepresentationAssignmentClass",
        "NominalDiameterRepresentationAssignmentClass", "NominalDiameterStandardSpecialization",
        "NominalDiameterTypeRepresentationAssignmentClass", "PipingClassCodeAssignmentClass",
        "PrimarySecondaryPipingNetworkSegmentSpecialization", "SegmentNumberAssignmentClass",
    ],
    "PipingComponent": [
        "FluidCodeAssignmentClass", "InsulationThickness", "InsulationTypeAssignmentClass",
        "PipingClassCodeAssignmentClass", "PipingComponentNameAssignmentClass",
        "PipingComponentNumberAssignmentClass", "PressureTestCircuitNumberAssignmentClass",
    ],
    "ActuatingSystem": ["ActuatingSystemNumberAssignmentClass", "TypicalInformationAssignmentClass"],
    "ControlledActuator": [
        "DeviceTypeNameAssignmentClass", "FailActionSpecialization",
        "FailActionRepresentationAssignmentClass", "SubTagNameAssignmentClass",
    ],
    "OperatedValveReference": ["SubTagNameAssignmentClass"],
    "Positioner": ["DeviceTypeNameAssignmentClass", "SubTagNameAssignmentClass"],
    "ActuatingFunction": ["ActuatingFunctionNumberAssignmentClass"],
    "ProcessInstrumentationFunction": [
        "LocationSpecialization", "ProcessInstrumentationFunctionCategoryAssignmentClass",
        "ProcessInstrumentationFunctionNumberAssignmentClass",
        "ProcessInstrumentationFunctionModifierAssignmentClass",
        "ProcessInstrumentationFunctionsAssignmentClass",
    ],
    "PipingNode": [
        "NominalDiameterNumericalValueRepresentationAssignmentClass",
        "NominalDiameterRepresentationAssignmentClass", "NominalDiameterStandardSpecialization",
        "NominalDiameterTypeRepresentationAssignmentClass",
    ],
    "ProcessSignalGeneratingFunction": [
        "ProcessSignalGeneratingFunctionNumberAssignmentClass",
        "SensorTypeAssignmentClass",
    ],
    "PipeOffPageConnector": ["PipeConnectorNumberAssignmentClass"],
    "PipeOffPageConnectorReference": [
        "ReferencedConnectorNumberAssignmentClass",
        "ReferencedDrawingNumberAssignmentClass",
    ],
    "InstrumentationLoopFunction": ["InstrumentationLoopFunctionNumberAssignmentClass"],
}


def _class_key(obj: DexpiBaseModel) -> str:
    if isinstance(obj, Chamber):
        return "Chamber"
    if isinstance(obj, Equipment):
        return "Equipment"
    if isinstance(obj, Nozzle):
        return "Nozzle"
    if isinstance(obj, PipingNetworkSystem):
        return "PipingNetworkSystem"
    if isinstance(obj, PipingNetworkSegment):
        return "PipingNetworkSegment"
    if isinstance(obj, PipingComponent):
        return "PipingComponent"
    if isinstance(obj, PipeOffPageConnector):
        return "PipeOffPageConnector"
    if isinstance(obj, PipeOffPageConnectorReference):
        return "PipeOffPageConnectorReference"
    if isinstance(obj, PipingNode):
        return "PipingNode"
    if isinstance(obj, ActuatingSystem):
        return "ActuatingSystem"
    if isinstance(obj, ControlledActuator):
        return "ControlledActuator"
    if isinstance(obj, OperatedValveReference):
        return "OperatedValveReference"
    if isinstance(obj, Positioner):
        return "Positioner"
    if isinstance(obj, ActuatingFunction):
        return "ActuatingFunction"
    if isinstance(obj, ProcessInstrumentationFunction):
        return "ProcessInstrumentationFunction"
    if isinstance(obj, ProcessSignalGeneratingFunction):
        return "ProcessSignalGeneratingFunction"
    if isinstance(obj, InstrumentationLoopFunction):
        return "InstrumentationLoopFunction"
    return ""


def _emit_generic_attributes(w: _Writer, obj: DexpiBaseModel) -> None:
    attrs = list(obj.custom_attributes) + _field_attributes(obj)
    order = CLASS_ORDER.get(_class_key(obj), [])
    ordered = sorted(attrs, key=lambda a: order.index(a.name) if a.name in order else len(order))
    if not ordered:
        return
    w.open("GenericAttributes", _attrs(Set="DexpiAttributes", Number=str(len(ordered))))
    for a in ordered:
        uri = a.attribute_uri or (SANDBOX + a.name)
        parts = [_attrs(Name=a.name, AttributeURI=uri)]
        if a.language is not None:
            parts.append(f' Language="{a.language}"')
        if a.format == "double":
            parts.append(_attrs(Value=a.value or "", Format=a.format))
            if a.units is not None:
                parts.append(f' Units="{a.units}"')
            if a.units_uri is not None:
                parts.append(f' UnitsURI="{a.units_uri}"')
        else:
            parts.append(f' Format="{a.format}"')
            if a.value is not None:
                parts.append(f' Value="{_esc(a.value)}"')
            if a.value_uri is not None:
                parts.append(f' ValueURI="{a.value_uri}"')
        w.leaf("GenericAttribute", "".join(parts))
    w.close("GenericAttributes")


# --- model state for reverse references ---

_MODEL: ConceptualModel | None = None


def _actuating_function_of(system: ActuatingSystem) -> str:
    for pif in _MODEL.process_instrumentation_functions:  # type: ignore[union-attr]
        for af in pif.actuating_functions:
            if af.systems is system:
                return af.dex_id
    return ""


def _referenced_by(component: PipingComponent) -> list[str]:
    out: list[str] = []
    for system in _MODEL.actuating_systems:  # type: ignore[union-attr]
        ref = system.operated_valve_reference
        if ref is not None and ref.valve is component:
            out.append(ref.dex_id)
    return out


def _nozzles_of(chamber: Chamber) -> list[str]:
    out: list[str] = []
    for equipment in _MODEL.equipment:  # type: ignore[union-attr]
        for nozzle in equipment.nozzles:
            if nozzle.chamber is chamber:
                out.append(nozzle.dex_id)
    return out


def _signals_targeting(function: ActuatingFunction) -> list[str]:
    out: list[str] = []
    for pif in _MODEL.process_instrumentation_functions:  # type: ignore[union-attr]
        for signal in pif.signal_conveying_functions:
            if signal.target is function:
                out.append(signal.dex_id)
    return out


def _signals_starting_at(source: SignalConveyingFunctionSource) -> list[str]:
    out: list[str] = []
    for pif in _MODEL.process_instrumentation_functions:  # type: ignore[union-attr]
        for signal in pif.signal_conveying_functions:
            if signal.source is source:
                out.append(signal.dex_id)
    return out


def _signals_ending_at(target: SignalConveyingFunctionTarget) -> list[str]:
    out: list[str] = []
    for owner in _MODEL.process_instrumentation_functions:  # type: ignore[union-attr]
        for signal in owner.signal_conveying_functions:
            if signal.target is target:
                out.append(signal.dex_id)
    return out


def _psgfs_located_in(location: SensingLocation) -> list[str]:
    out: list[str] = []
    for pif in _MODEL.process_instrumentation_functions:  # type: ignore[union-attr]
        for psgf in pif.process_signal_generating_functions:
            if psgf.sensing_location is location:
                out.append(psgf.dex_id)
    return out


def _actuating_functions_located_in(segment: PipingNetworkSegment) -> list[str]:
    out: list[str] = []
    for pif in _MODEL.process_instrumentation_functions:  # type: ignore[union-attr]
        for function in pif.actuating_functions:
            if function.actuating_location is segment:
                out.append(function.dex_id)
    return out


def _object_references_to(connector: PipeOffPageConnector) -> list[str]:
    out: list[str] = []
    for line in _MODEL.piping_network_systems:  # type: ignore[union-attr]
        for segment in line.segments:
            for item in segment.items:
                ref = getattr(item, "connector_reference", None)
                if (
                    isinstance(ref, PipeOffPageConnectorObjectReference)
                    and ref.referenced_connector is connector
                ):
                    out.append(ref.dex_id)
    return out


def _loops_containing(pif: ProcessInstrumentationFunction) -> list[str]:
    out: list[str] = []
    for loop in _MODEL.instrumentation_loop_functions:  # type: ignore[union-attr]
        if any(member is pif for member in loop.process_instrumentation_functions):
            out.append(loop.dex_id)
    return out


# --- element emitters ---


def _emit_actuating_system(w: _Writer, system: ActuatingSystem) -> None:
    w.open("ActuatingSystem", _item_attrs(system, "ActuatingSystem"))
    _emit_generic_attributes(w, system)
    w.leaf("Association", _attrs(Type="fulfills", ItemID=_actuating_function_of(system)))
    if system.controlled_actuator is not None:
        _emit_component(w, system.controlled_actuator)
    if system.operated_valve_reference is not None:
        _emit_operated_valve_reference(w, system.operated_valve_reference)
    if system.positioner is not None:
        _emit_component(w, system.positioner)
    w.close("ActuatingSystem")


def _emit_component(w: _Writer, component: ControlledActuator | Positioner) -> None:
    w.open("ActuatingSystemComponent", _item_attrs(component, component.component_class))
    _emit_generic_attributes(w, component)
    w.close("ActuatingSystemComponent")


def _emit_operated_valve_reference(w: _Writer, reference: OperatedValveReference) -> None:
    w.open("ActuatingSystemComponent", _item_attrs(reference, "OperatedValveReference"))
    _emit_generic_attributes(w, reference)
    if reference.valve is not None:
        w.leaf("Association", _attrs(Type="refers to", ItemID=reference.valve.dex_id))
    w.close("ActuatingSystemComponent")


def _emit_pns(w: _Writer, line: PipingNetworkSystem) -> None:
    w.open("PipingNetworkSystem", _item_attrs(line, "PipingNetworkSystem"))
    _emit_generic_attributes(w, line)
    for segment in line.segments:
        _emit_segment(w, segment)
    w.close("PipingNetworkSystem")


def _emit_segment(w: _Writer, segment: PipingNetworkSegment) -> None:
    w.open("PipingNetworkSegment", _item_attrs(segment, "PipingNetworkSegment"))
    _emit_generic_attributes(w, segment)
    for psgf_id in _psgfs_located_in(segment):
        w.leaf("Association", _attrs(Type="is the location of", ItemID=psgf_id))
    for function_id in _actuating_functions_located_in(segment):
        w.leaf("Association", _attrs(Type="is the location of", ItemID=function_id))
    for item in segment.items:
        if isinstance(item, PipeOffPageConnector):
            _emit_off_page_connector(w, item)
        elif isinstance(item, PipingComponent):
            _emit_piping_component(w, item)
    for connection in segment.connections:
        _emit_connection(w, connection)
    w.close("PipingNetworkSegment")


def _emit_piping_component(w: _Writer, component: PipingComponent) -> None:
    w.open("PipingComponent", _item_attrs(component, component.component_class))
    _emit_connection_points(w, component)
    _emit_generic_attributes(w, component)
    for ref_id in _referenced_by(component):
        w.leaf("Association", _attrs(Type="is referenced by", ItemID=ref_id))
    for psgf_id in _psgfs_located_in(component):
        w.leaf("Association", _attrs(Type="is the location of", ItemID=psgf_id))
    w.close("PipingComponent")


def _emit_off_page_connector(w: _Writer, connector: PipeOffPageConnector) -> None:
    w.open("PipeOffPageConnector", _item_attrs(connector, connector.component_class))
    _emit_connection_points(w, connector)
    _emit_generic_attributes(w, connector)
    for ref_id in _object_references_to(connector):
        w.leaf("Association", _attrs(Type="is referenced by", ItemID=ref_id))
    if connector.connector_reference is not None:
        ref = connector.connector_reference
        w.open("PipeOffPageConnectorReference", _item_attrs(ref, ref.component_class))
        _emit_generic_attributes(w, ref)
        if (
            isinstance(ref, PipeOffPageConnectorObjectReference)
            and ref.referenced_connector is not None
        ):
            w.leaf("Association", _attrs(
                Type="refers to", ItemID=ref.referenced_connector.dex_id,
            ))
        w.close("PipeOffPageConnectorReference")
    w.close("PipeOffPageConnector")


def _emit_connection_points(w: _Writer, owner: Any) -> None:
    nodes = list(owner.nodes)
    kw: dict[str, Any] = {}
    if getattr(owner, "flow_in_index", None) is not None:
        kw["FlowIn"] = str(owner.flow_in_index)
    if getattr(owner, "flow_out_index", None) is not None:
        kw["FlowOut"] = str(owner.flow_out_index)
    kw["NumPoints"] = str(len(nodes) + 1)  # +1 for the implicit default node
    w.open("ConnectionPoints", _attrs(**kw))
    w.leaf("Node", _attrs(ID=f"{owner.dex_id}-DefaultNode"))
    for node in nodes:
        if node.custom_attributes:
            w.open("Node", _attrs(Type="process", ID=node.dex_id))
            _emit_generic_attributes(w, node)
            w.close("Node")
        else:
            w.leaf("Node", _attrs(Type="process", ID=node.dex_id))
    w.close("ConnectionPoints")


def _emit_connection(w: _Writer, connection: Pipe) -> None:
    kw: dict[str, Any] = {}
    if connection.source_item is not None:
        kw["FromID"] = connection.source_item.dex_id
        if connection.source_node is not None:
            kw["FromNode"] = str(list(connection.source_item.nodes).index(connection.source_node) + 1)
    if connection.target_item is not None:
        kw["ToID"] = connection.target_item.dex_id
        if connection.target_node is not None:
            kw["ToNode"] = str(list(connection.target_item.nodes).index(connection.target_node) + 1)
    w.leaf("Connection", _attrs(**kw))


def _emit_equipment(w: _Writer, equipment: Equipment) -> None:
    w.open("Equipment", _item_attrs(equipment, equipment.component_class))
    _emit_generic_attributes(w, equipment)
    for nozzle in equipment.nozzles:
        _emit_nozzle(w, nozzle)
    for chamber in equipment.drying_chambers:
        _emit_chamber(w, chamber)
    w.close("Equipment")


def _emit_nozzle(w: _Writer, nozzle: Nozzle) -> None:
    w.open("Nozzle", _item_attrs(nozzle, "Nozzle"))
    _emit_connection_points(w, nozzle)
    _emit_generic_attributes(w, nozzle)
    if nozzle.chamber is not None:
        w.leaf("Association", _attrs(Type="is located in", ItemID=nozzle.chamber.dex_id))
    for psgf_id in _psgfs_located_in(nozzle):
        w.leaf("Association", _attrs(Type="is the location of", ItemID=psgf_id))
    w.close("Nozzle")


def _emit_chamber(w: _Writer, chamber: Chamber) -> None:
    w.open("Equipment", _item_attrs(chamber, "Chamber"))
    _emit_generic_attributes(w, chamber)
    for nozzle_id in _nozzles_of(chamber):
        w.leaf("Association", _attrs(Type="is the location of", ItemID=nozzle_id))
    w.close("Equipment")


def _emit_instrumentation_loop_function(
    w: _Writer, loop: InstrumentationLoopFunction
) -> None:
    w.open("InstrumentationLoopFunction", _item_attrs(loop, loop.component_class))
    _emit_generic_attributes(w, loop)
    for pif in loop.process_instrumentation_functions:
        w.leaf("Association", _attrs(Type="is a collection including", ItemID=pif.dex_id))
    w.close("InstrumentationLoopFunction")


def _emit_pif(w: _Writer, pif: ProcessInstrumentationFunction) -> None:
    w.open("ProcessInstrumentationFunction", _item_attrs(pif, pif.component_class))
    _emit_generic_attributes(w, pif)
    # Child order follows the C01 reference (the XSD allows any order):
    # signal associations, loop associations, InformationFlow, ActuatingFunction, PSGF,
    # then the signal off-page connectors (not in C01).
    # Signals may be composed under any PIF, so both ends scan the whole model.
    for signal_id in _signals_starting_at(pif):
        w.leaf("Association", _attrs(Type="is logical start of", ItemID=signal_id))
    for signal_id in _signals_ending_at(pif):
        w.leaf("Association", _attrs(Type="is logical end of", ItemID=signal_id))
    for loop_id in _loops_containing(pif):
        w.leaf("Association", _attrs(Type="is a part of", ItemID=loop_id))
    for signal in pif.signal_conveying_functions:
        _emit_signal(w, signal)
    for function in pif.actuating_functions:
        _emit_actuating_function(w, function)
    for psgf in pif.process_signal_generating_functions:
        _emit_psgf(w, psgf)
    for connector in pif.signal_connectors:
        _emit_signal_connector(w, connector)
    w.close("ProcessInstrumentationFunction")


def _emit_signal_connector(w: _Writer, connector: SignalOffPageConnector) -> None:
    # The DEXPI 1.3 text names the tag <InformationFlowOffPageConnector>, but the
    # bundled Proteus 4.1.1 XSD only accepts <SignalOffPageConnector> here.
    w.open("SignalOffPageConnector", _item_attrs(connector, connector.component_class))
    _emit_generic_attributes(w, connector)
    if isinstance(connector, SignalConveyingFunctionSource):
        for signal_id in _signals_starting_at(connector):
            w.leaf("Association", _attrs(Type="is logical start of", ItemID=signal_id))
    if isinstance(connector, SignalConveyingFunctionTarget):
        for signal_id in _signals_ending_at(connector):
            w.leaf("Association", _attrs(Type="is logical end of", ItemID=signal_id))
    w.close("SignalOffPageConnector")


def _emit_psgf(w: _Writer, psgf: ProcessSignalGeneratingFunction) -> None:
    w.open("ProcessSignalGeneratingFunction", _item_attrs(psgf, psgf.component_class))
    _emit_generic_attributes(w, psgf)
    if psgf.sensing_location is not None:
        w.leaf("Association", _attrs(Type="is located in", ItemID=psgf.sensing_location.dex_id))
    for signal_id in _signals_starting_at(psgf):
        w.leaf("Association", _attrs(Type="is logical start of", ItemID=signal_id))
    w.close("ProcessSignalGeneratingFunction")


def _emit_signal(w: _Writer, signal: SignalConveyingFunction) -> None:
    w.open("InformationFlow", _item_attrs(signal, "SignalConveyingFunction"))
    if signal.source is not None:
        w.leaf("Association", _attrs(Type="has logical start", ItemID=signal.source.dex_id))
    if signal.target is not None:
        w.leaf("Association", _attrs(Type="has logical end", ItemID=signal.target.dex_id))
    w.close("InformationFlow")


def _emit_actuating_function(w: _Writer, function: ActuatingFunction) -> None:
    w.open("ActuatingFunction", _item_attrs(function, "ActuatingFunction"))
    _emit_generic_attributes(w, function)
    for signal_id in _signals_targeting(function):
        w.leaf("Association", _attrs(Type="is logical end of", ItemID=signal_id))
    if function.systems is not None:
        w.leaf("Association", _attrs(Type="is fulfilled by", ItemID=function.systems.dex_id))
    if function.actuating_location is not None:
        w.leaf("Association", _attrs(
            Type="is located in", ItemID=function.actuating_location.dex_id,
        ))
    w.close("ActuatingFunction")


# --- model checks run before writing ---

# XML ``NCName`` (the lexical space of ``xsd:ID``), approximated with Unicode
# word characters: a letter or underscore, then letters, digits, ``_``, ``-``
# or ``.``. No colon, no whitespace.
_NCNAME = re.compile(r"[^\W\d][\w.\-]*")


def _label(obj: DexpiBaseModel) -> str:
    return f"{type(obj).__name__} {obj.dex_id!r}"


def _model_values(value: Any) -> list[DexpiBaseModel]:
    """The model objects held by a field value (bare, optional or a list)."""
    if isinstance(value, DexpiBaseModel):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, DexpiBaseModel)]
    return []


def _fields_with(obj: DexpiBaseModel, relation: Any) -> list[str]:
    cls = type(obj)
    if not cls.__pydantic_complete__:
        cls.model_rebuild()
    return [
        name for name, info in cls.model_fields.items()
        if relation_of(info.metadata) is relation
    ]


def _check_model(model: ConceptualModel) -> None:
    """Reject a model graph that would serialize to invalid or dangling XML.

    Walks the composition tree from ``model`` (every ``Composed`` field) and
    raises ``ValueError`` when:

    - an object is reached twice (composed in two places, or listed twice);
    - a composed child does not record the object that composes it as its
      owner, which happens when a composition list is mutated in place
      (``equipment.nozzles.append(...)``) instead of using ``add_*``;
    - a ``dex_id`` (the Proteus ``ID``) is not an XML ``NCName`` or is not
      unique, including the implicit ``<dex_id>-DefaultNode`` IDs;
    - a ``Ref`` field points at an object that is not composed in the model.
    """
    composed: dict[int, DexpiBaseModel] = {}
    order: list[DexpiBaseModel] = []

    def visit(obj: DexpiBaseModel, parent: DexpiBaseModel | None) -> None:
        if id(obj) in composed:
            raise ValueError(f"{_label(obj)} is composed more than once in the model")
        composed[id(obj)] = obj
        order.append(obj)
        if (
            parent is not None
            and "_owner" in type(obj).__private_attributes__
            and obj._owner is not parent
        ):
            raise ValueError(
                f"{_label(obj)} is not owned by the {type(parent).__name__} that "
                "composes it; use the add_* method instead of mutating the list in place"
            )
        for name in _fields_with(obj, Composed):
            for child in _model_values(getattr(obj, name)):
                visit(child, obj)

    visit(model, None)
    objects = order[1:]  # the root has no Proteus ID

    seen: set[str] = set()
    for obj in objects:
        wire_ids = [obj.dex_id]
        if "nodes" in type(obj).model_fields:
            wire_ids.append(f"{obj.dex_id}-DefaultNode")
        for wire_id in wire_ids:
            if not _NCNAME.fullmatch(wire_id):
                raise ValueError(
                    f"dex_id {wire_id!r} of {type(obj).__name__} is not a valid XML NCName; "
                    "the Proteus ID must start with a letter or underscore and "
                    "contain no spaces or colons"
                )
            if wire_id in seen:
                raise ValueError(
                    f"duplicate dex_id {wire_id!r}: the Proteus ID must be unique in the model"
                )
            seen.add(wire_id)

    for obj in objects:
        for name in _fields_with(obj, Ref):
            for target in _model_values(getattr(obj, name)):
                if id(target) not in composed:
                    raise ValueError(
                        f"{_label(target)} is referenced by {_label(obj)}.{name} "
                        "but not composed anywhere in the model"
                    )


def to_proteus_xml(model: ConceptualModel) -> str:
    """Serialize ``model`` to a Proteus 4.1.1 XML string.

    Raises ``ValueError`` if the model graph fails the checks in
    ``_check_model``. The output is not schema-validated here; run
    ``examples/validate_dexpi.py`` on it.
    """
    _check_model(model)
    global _MODEL
    _MODEL = model
    w = _Writer()
    w._lines.append("<?xml version='1.0' encoding='UTF-8'?>")
    w.open("PlantModel", "")
    w.open("PlantInformation", _attrs(**PLANT_INFORMATION))
    w.leaf("UnitsOfMeasure", "")
    w.close("PlantInformation")
    for system in model.actuating_systems:
        _emit_actuating_system(w, system)
    for line in model.piping_network_systems:
        _emit_pns(w, line)
    for pif in model.process_instrumentation_functions:
        _emit_pif(w, pif)
    for equipment in model.equipment:
        _emit_equipment(w, equipment)
    for loop in model.instrumentation_loop_functions:
        _emit_instrumentation_loop_function(w, loop)
    w.close("PlantModel")
    return w.text()
