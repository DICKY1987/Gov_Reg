# Move Plan Report

Run ID: phaseA_20260215_085057
Generated UTC: 2026-02-15T08:50:57.347129+00:00

## Destination Roots
- REGISTRY_FILES: 01260207201000001250_REGISTRY (dir_id=01260207201000001250)
- ID_FILES: 01260207201000001162_GEU/01260207201000001165_ID (dir_id=01260207201000001165)
- MULTI_CLI_PLANNING: 01260207201000001221_Multi CLI (dir_id=01260207201000001221)
- TEMPLATE_OPERATIONS: newPhasePlanProcess (dir_id=01260207201000001177)

## Mapping Rule
- If a file is already under its destination root, destination_relpath == source_relpath.
- Otherwise, destination_relpath = <dest_root_relpath>/<source_relpath> (full re-root).

## Counts
- candidates: 1271
- eligible: 70
- ambiguous skipped: 104
- unclassified skipped: 412
- excluded skipped: 355
- missing source skipped: 1201
- destination collision skipped: 0