# Confirm ActuatingSystemComponent in DEXPI 1.3

Type: research
Status: resolved
Blocked by:

## Question

In DEXPI P&ID Specification 1.3, what is the canonical model of a control valve (actuator + valve)?

The project currently names this `ActuatingSystemComponent`. Confirm whether that class exists, what it contains, and how it relates to `Valve`, `ActuatingSystem`, `ActuatingFunction`, `OperatedValveReference`, and signal targets.

Primary sources: DEXPI P&ID Specification 1.3. Do not read pyDEXPI source.

Write findings to `.scratch/dexpi-13-inmemory-model/research/03-actuating-system-component.md` with citations.

## Answer

`ActuatingSystemComponent` is a Proteus XML tag, not a DEXPI 1.3 class. A control valve is `OperatedValve` plus `ActuatingSystem` (`ControlledActuator`, `OperatedValveReference`) plus optional `ActuatingFunction` for signal attachment. Detail: [03-actuating-system-component](../research/03-actuating-system-component.md).

The dedicated research agent stalled before writing the file; this ticket was completed from the same official 1.3 HTML pages.
