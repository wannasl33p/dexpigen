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

from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

from dexpigen.base import DexpiBaseModel
from dexpigen.enumerations import FailActionClassification
from dexpigen.piping import OperatedValve, PipingNetworkSegment


class CustomAttribute(BaseModel):
    """A generic name/value entry in the DEXPI customization bag.

    A value object, not an identified DEXPI instance, so it carries no ``id``/
    ``dex_id``.
    """

    model_config = ConfigDict(validate_assignment=True)

    name: str
    value: str | None = None


class SignalConveyingFunctionSource(DexpiBaseModel):
    """Abstract role: a valid ``SignalConveyingFunction`` source."""

    _abstract: ClassVar[bool] = True


class SignalConveyingFunctionTarget(DexpiBaseModel):
    """Abstract role: a valid ``SignalConveyingFunction`` target."""

    _abstract: ClassVar[bool] = True


class ProcessInstrumentationFunction(
    SignalConveyingFunctionSource, SignalConveyingFunctionTarget
):
    """The P&ID instrument/function bubble.

    The instrument tag is first-class (number, category, modifier, additional
    functions); every other DEXPI field lives in the generic ``custom_attributes``
    bag. It composes the ``ActuatingFunction`` and ``SignalConveyingFunction``
    objects that realise this function.
    """

    component_class: ClassVar[str] = "ProcessInstrumentationFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ProcessInstrumentationFunction"

    process_instrumentation_function_number: str | None = None
    process_instrumentation_function_category: str | None = None
    process_instrumentation_function_modifier: str | None = None
    process_instrumentation_functions: str | None = None

    custom_attributes: list[CustomAttribute] = Field(default_factory=list)
    actuating_functions: list[ActuatingFunction] = Field(default_factory=list)
    signal_conveying_functions: list[SignalConveyingFunction] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def _bind_functions(self) -> Self:
        for function in self.actuating_functions:
            self._adopt_function(function)
        for function in self.signal_conveying_functions:
            self._adopt_function(function)
        return self

    def _adopt_function(
        self, function: ActuatingFunction | SignalConveyingFunction
    ) -> None:
        owner = function._owner
        if owner is not None and owner is not self:
            raise ValueError(
                "function is already owned by another process instrumentation function"
            )
        function._owner = self

    def add_actuating_function(self, function: ActuatingFunction) -> Self:
        """Compose ``function`` under this bubble, enforcing single ownership."""
        self._adopt_function(function)
        self.actuating_functions.append(function)
        return self

    def add_signal_conveying_function(
        self, function: SignalConveyingFunction
    ) -> Self:
        """Compose ``function`` under this bubble, enforcing single ownership."""
        self._adopt_function(function)
        self.signal_conveying_functions.append(function)
        return self

    def add_custom_attribute(self, attribute: CustomAttribute) -> Self:
        """Add a generic ``attribute`` to this bubble's customization bag."""
        self.custom_attributes.append(attribute)
        return self


class ProcessControlFunction(ProcessInstrumentationFunction):
    """A control/safeguarding system bubble (a function, not ``Equipment``)."""
    component_class: ClassVar[str] = "ProcessControlFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/ProcessControlFunction"


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

    valve: OperatedValve | None = None
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

    controlled_actuator: ControlledActuator | None = None
    operated_valve_reference: OperatedValveReference | None = None
    positioner: Positioner | None = None

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

    systems: ActuatingSystem | None = None
    actuating_location: PipingNetworkSegment | None = None

    _owner: ProcessInstrumentationFunction | None = PrivateAttr(default=None)


class SignalConveyingFunction(DexpiBaseModel):
    """A dashed signal line connecting two functions (no graphics)."""
    component_class: ClassVar[str] = "SignalConveyingFunction"
    component_class_uri: ClassVar[str] = "http://sandbox.dexpi.org/rdl/SignalConveyingFunction"

    source: SignalConveyingFunctionSource | None = None
    target: SignalConveyingFunctionTarget | None = None

    _owner: ProcessInstrumentationFunction | None = PrivateAttr(default=None)


class SignalOffPageConnector(DexpiBaseModel):
    """Abstract base for a signal off-page connector."""

    _abstract: ClassVar[bool] = True


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
