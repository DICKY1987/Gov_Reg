# newPhasePlanProcess

## Active governance documents

The active v3.3 source-of-truth documents are:

- `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_3.json`
- `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_3.json`
- `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_3.json`

## Generated artifacts

Generated semantic navigation artifacts are rebuilt from the active documents:

- `inventory.json`
- `indexes/*_V3_3.index.json`
- `evidence/PH-*`

Run the generator from this directory with:

```powershell
python .\tools\index_generator.py
```

`NEWPHASEPLANPROCESS_ARRAYS.json` was a duplicate inventory alias and has been archived. Use `inventory.json` as the canonical array inventory.

## Tooling

- `tools/index_generator.py` builds inventory, indexes, and indexing evidence.
- `tools/resolver.py` resolves semantic IDs to JSON Pointers from generated index artifacts.

The older plan-instance CLI under `01260207201000001225_scripts` is legacy for this document set. It expects a different plan shape (`meta`, `plan`, `navigation`) and is not the validator for the three v3.3 governance source documents.

## Archive

Backups, old v3.0 files, migration notes, completion reports, and deprecated generated aliases were moved to:

```text
C:\Users\richg\CENTRAL_ARCHIVE\Gov_Reg\newPhasePlanProcess\2026-04-19_v3_3_cleanup
```

The move manifest is `archive_manifest_2026-04-19_v3_3_cleanup.json`.
