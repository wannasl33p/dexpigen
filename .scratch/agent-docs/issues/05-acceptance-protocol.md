# Decide the docs acceptance protocol

Type: grilling
Status: open
Blocked by: 02-doc-set-layout

## Question

How do we verify the docs are sufficient? Pin down the fresh-agent test: allowed inputs (docs + code only), the task (reproduce `examples/C01`, or a smaller excerpt such as C05), the pass criteria (schema-valid via `examples/validate_dexpi.py`, structural match to the golden XML), who runs it, and when it re-runs.
