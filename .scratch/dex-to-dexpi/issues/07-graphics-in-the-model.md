# Decide how the model carries graphics

Type: grilling
Status: open
Blocked by: 01-proteus-graphics-minimum

## Question

Given the minimal Proteus graphics set, how does the library carry and write geometry? Options include optional position/extent fields on plant items, a separate graphics layer keyed by object, or graphics produced by the writer straight from the Dex extraction. Decide where line geometry (`CenterLine`) lives, how the "no graphics" rule in the v0.1 spec and in `CLAUDE.md` is amended, and how graphics appear in the generated class index and in model checks.
