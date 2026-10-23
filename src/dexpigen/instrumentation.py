"""Instrumentation: instrument/function bubbles, the control-valve assembly,
signal lines, and the signal endpoint roles.

``ProcessInstrumentationFunction`` is the P&ID bubble; ``ProcessControlFunction``
is its control/safeguarding subtype. A control valve is ``OperatedValve`` (see
``piping``) plus an ``ActuatingSystem`` that composes ``ControlledActuator``,
``OperatedValveReference`` and optional ``Positioner``, linked by an
``ActuatingFunction``. A dashed signal line is a ``SignalConveyingFunction``
whose ``source``/``target`` reference functions only, via the abstract
``SignalConveyingFunctionSource``/``SignalConveyingFunctionTarget`` roles.
"""

from __future__ import annotations

from typing import Annotated, Any, ClassVar, Self

from pydantic import Field, PrivateAttr, model_validator

from dexpigen.base import Composed, CustomAttribute, DexpiBaseModel, Ref
from dexpigen.enumerations import FailActionClassification
from dexpigen.piping import OperatedValve, PipingNetworkSegment, SensingLocation

_ALREADY_COMPOSED_MESSAGE = (
    "function is already composed under this process instrumentation function"
)


class SignalConveyingFunctionSource(DexpiBaseModel):
    """Abstract role: a valid ``SignalConveyingFunction`` source."""

    _abstract: ClassVar[bool] = True


class SignalConveyingFunctionTarget(DexpiBaseModel):
    """Abstract role: a valid ``SignalConveyingFunction`` target."""

    _abstract: ClassVar[bool] = True


class ProcessSignalGeneratingFunction(SignalConveyingFunctionSource):
    """The sensing function of a PIF: a signal source located on a piping object.

    It is composed by its ``ProcessInstrumentationFunction`` and references the
    ``SensingLocation`` (nozzle, piping component or segment) it is located in.
    The location is a reference, not ownership, so it may be shared.
    """

    component_class: ClassVar[str] = "ProcessSignalGeneratingFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ProcessSignalGeneratingFunction"

    process_signal_generating_function_number: str | None = None
    sensor_type: str | None = None
    sensing_location: Annotated[SensingLocation | None, Ref] = None

    _owner: ProcessInstrumentationFunction | None = PrivateAttr(default=None)


class ProcessInstrumentationFunction(
    SignalConveyingFunctionSource, SignalConveyingFunctionTarget
):
    """The P&ID instrument/function bubble.

    The instrument tag is first-class (number, category, modifier, additional
    functions); every other DEXPI field lives in the generic ``custom_attributes``
    bag. It composes the ``ActuatingFunction`` and ``SignalConveyingFunction``
    objects that realise this function, the ``ProcessSignalGeneratingFunction``
    objects that anchor it to the process, and its ``SignalOffPageConnector``
    objects (DEXPI ``SignalConnectors``).
    """

    component_class: ClassVar[str] = "ProcessInstrumentationFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ProcessInstrumentationFunction"

    process_instrumentation_function_number: str | None = None
    process_instrumentation_function_category: str | None = None
    process_instrumentation_function_modifier: str | None = None
    process_instrumentation_functions_code: str | None = None

    actuating_functions: Annotated[list[ActuatingFunction], Composed] = Field(
        default_factory=list
    )
    signal_conveying_functions: Annotated[list[SignalConveyingFunction], Composed] = (
        Field(default_factory=list)
    )
    process_signal_generating_functions: Annotated[
        list[ProcessSignalGeneratingFunction], Composed
    ] = Field(default_factory=list)
    signal_connectors: Annotated[list[SignalOffPageConnector], Composed] = Field(
        default_factory=list
    )

    @model_validator(mode="before")
    @classmethod
    def _reject_renamed_keyword(cls, data: Any) -> Any:
        # ``process_instrumentation_functions`` was renamed; fail loudly rather
        # than letting ``extra=ignore`` drop the value silently.
        if isinstance(data, dict) and "process_instrumentation_functions" in data:
            raise ValueError(
                "process_instrumentation_functions was renamed to "
                "process_instrumentation_functions_code"
            )
        return data

    @model_validator(mode="after")
    def _bind_functions(self) -> Self:
        # Pydantic re-runs this validator when an existing instance is validated
        # again, so it must not reject functions already bound to this bubble.
        # Duplicates within the same constructor list are rejected by identity.
        for functions in (
            self.actuating_functions,
            self.signal_conveying_functions,
            self.process_signal_generating_functions,
            self.signal_connectors,
        ):
            if len({id(function) for function in functions}) != len(functions):
                raise ValueError(_ALREADY_COMPOSED_MESSAGE)
        for function in self.actuating_functions:
            self._adopt_function(function)
        for function in self.signal_conveying_functions:
            self._adopt_function(function)
        for function in self.process_signal_generating_functions:
            self._adopt_function(function)
        for connector in self.signal_connectors:
            self._adopt_function(connector)
        return self

    def _adopt_function(
        self,
        function: ActuatingFunction
        | SignalConveyingFunction
        | ProcessSignalGeneratingFunction
        | SignalOffPageConnector,
    ) -> None:
        owner = function._owner
        if owner is not None and owner is not self:
            raise ValueError(
                "function is already owned by another process instrumentation function"
            )
        function._owner = self

    def _reject_recomposition(
        self,
        function: ActuatingFunction
        | SignalConveyingFunction
        | ProcessSignalGeneratingFunction
        | SignalOffPageConnector,
    ) -> None:
        # Re-composing would append the same object twice, giving two elements
        # with one ``ID`` (schema-invalid XML).
        if function._owner is self:
            raise ValueError(_ALREADY_COMPOSED_MESSAGE)

    def add_actuating_function(self, function: ActuatingFunction) -> Self:
        """Compose ``function`` under this bubble, enforcing single ownership."""
        self._reject_recomposition(function)
        self._adopt_function(function)
        self.actuating_functions.append(function)
        return self

    def add_signal_conveying_function(
        self, function: SignalConveyingFunction
    ) -> Self:
        """Compose ``function`` under this bubble, enforcing single ownership."""
        self._reject_recomposition(function)
        self._adopt_function(function)
        self.signal_conveying_functions.append(function)
        return self

    def add_process_signal_generating_function(
        self, function: ProcessSignalGeneratingFunction
    ) -> Self:
        """Compose ``function`` under this bubble, enforcing single ownership."""
        self._reject_recomposition(function)
        self._adopt_function(function)
        self.process_signal_generating_functions.append(function)
        return self

    def add_signal_connector(self, connector: SignalOffPageConnector) -> Self:
        """Compose ``connector`` under this bubble, enforcing single ownership."""
        self._reject_recomposition(connector)
        self._adopt_function(connector)
        self.signal_connectors.append(connector)
        return self


class ProcessControlFunction(ProcessInstrumentationFunction):
    """A control/safeguarding system bubble (a function, not ``Equipment``)."""
    component_class: ClassVar[str] = "ProcessControlFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ProcessControlFunction"


class InstrumentationLoopFunction(DexpiBaseModel):
    """A top-level loop function that collects one or more PIFs.

    The PIFs are referenced, not composed: they stay top-level in the model and
    may be referenced by more than one loop.
    """

    component_class: ClassVar[str] = "InstrumentationLoopFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/InstrumentationLoopFunction"

    instrumentation_loop_function_number: str | None = None
    process_instrumentation_functions: Annotated[
        list[ProcessInstrumentationFunction], Ref
    ] = Field(default_factory=list)


class ControlledActuator(DexpiBaseModel):
    """The energy-to-motion transducer of a control-valve assembly."""
    component_class: ClassVar[str] = "ControlledActuator"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ControlledActuator"

    device_type_name: str | None = None
    fail_action: FailActionClassification | None = None
    fail_action_representation: str | None = None
    sub_tag_name: str | None = None

    _owner: ActuatingSystem | None = PrivateAttr(default=None)


class OperatedValveReference(DexpiBaseModel):
    """A reference to the ``OperatedValve`` a control-valve assembly controls."""
    component_class: ClassVar[str] = "OperatedValveReference"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/OperatedValveReference"

    valve: Annotated[OperatedValve | None, Ref] = None
    sub_tag_name: str | None = None

    _owner: ActuatingSystem | None = PrivateAttr(default=None)


class Positioner(DexpiBaseModel):
    """The positioner of a control-valve assembly."""
    component_class: ClassVar[str] = "Positioner"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/Positioner"

    device_type_name: str | None = None
    sub_tag_name: str | None = None

    _owner: ActuatingSystem | None = PrivateAttr(default=None)


class ActuatingSystem(DexpiBaseModel):
    """A control-valve physical assembly (actuator, valve reference, positioner)."""
    component_class: ClassVar[str] = "ActuatingSystem"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ActuatingSystem"

    actuating_system_number: str | None = None
    typical_information: str | None = None

    controlled_actuator: Annotated[ControlledActuator | None, Composed] = None
    operated_valve_reference: Annotated[OperatedValveReference | None, Composed] = None
    positioner: Annotated[Positioner | None, Composed] = None

    @model_validator(mode="after")
    def _bind_children(self) -> Self:
        for child in (
            self.controlled_actuator,
            self.operated_valve_reference,
            self.positioner,
        ):
            if child is not None:
                self._adopt(child)
        return self

    def _adopt(
        self,
        child: ControlledActuator | OperatedValveReference | Positioner,
    ) -> None:
        owner = child._owner
        if owner is not None and owner is not self:
            raise ValueError("component is already owned by another actuating system")
        child._owner = self

    def add_controlled_actuator(self, actuator: ControlledActuator) -> Self:
        """Compose ``actuator`` under this system, enforcing single ownership."""
        self._adopt(actuator)
        self.controlled_actuator = actuator
        return self

    def add_operated_valve_reference(
        self, reference: OperatedValveReference
    ) -> Self:
        """Compose ``reference`` under this system, enforcing single ownership."""
        self._adopt(reference)
        self.operated_valve_reference = reference
        return self

    def add_positioner(self, positioner: Positioner) -> Self:
        """Compose ``positioner`` under this system, enforcing single ownership."""
        self._adopt(positioner)
        self.positioner = positioner
        return self


class ActuatingFunction(
    SignalConveyingFunctionSource, SignalConveyingFunctionTarget
):
    """The control-loop function that references its assembly and location."""

    component_class: ClassVar[str] = "ActuatingFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ActuatingFunction"

    actuating_function_number: str | None = None

    systems: Annotated[ActuatingSystem | None, Ref] = None
    actuating_location: Annotated[PipingNetworkSegment | None, Ref] = None

    _owner: ProcessInstrumentationFunction | None = PrivateAttr(default=None)


class SignalConveyingFunction(DexpiBaseModel):
    """A dashed signal line connecting two functions (no graphics)."""
    component_class: ClassVar[str] = "SignalConveyingFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/SignalConveyingFunction"

    source: Annotated[SignalConveyingFunctionSource | None, Ref] = None
    target: Annotated[SignalConveyingFunctionTarget | None, Ref] = None

    _owner: ProcessInstrumentationFunction | None = PrivateAttr(default=None)


class SignalOffPageConnector(DexpiBaseModel):
    """Abstract base for a signal off-page connector.

    It is composed under a ``ProcessInstrumentationFunction``
    (``signal_connectors``) and written as a Proteus ``<SignalOffPageConnector>``
    inside that bubble.
    """

    _abstract: ClassVar[bool] = True

    _owner: ProcessInstrumentationFunction | None = PrivateAttr(default=None)


class FlowInSignalOffPageConnector(
    SignalOffPageConnector, SignalConveyingFunctionSource
):
    """A signal off-page connector that is a valid signal source."""

    component_class: ClassVar[str] = "FlowInSignalOffPageConnector"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/FlowInSignalOffPageConnector"


class FlowOutSignalOffPageConnector(
    SignalOffPageConnector, SignalConveyingFunctionTarget
):
    """A signal off-page connector that is a valid signal target."""

    component_class: ClassVar[str] = "FlowOutSignalOffPageConnector"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/FlowOutSignalOffPageConnector"
