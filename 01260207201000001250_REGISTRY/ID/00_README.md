# ID System Quick Reference

Current entrypoint for the ID subsystem under `01260207201000001250_REGISTRY\ID\`.

## What Lives Here

- `1_runtime\`
  - Core allocators, handlers, validators, and watchers.
- `2_cli_tools\`
  - File-ID tools, git hooks, and maintenance commands.
- `3_schemas\`
  - JSON schemas for `.dir_id` and related contracts.
- `4_config\`
  - Compatibility/reference config artifacts.
- `6_docs\`
  - Maintained documentation. Start with `01_CONTEXT_PRIMER.md` and `00_MANIFEST.json`.
- `7_automation\`
  - Higher-level automation scripts, including dir-id generation, validation, reconciliation, and scanner tooling.
- `.dir_id`
  - Directory anchor for the `ID\` folder itself.

## Primary Entry Points

- Generate directory IDs
  - `7_automation\P_01999000042260125100_generate_dir_ids_gov_reg.py`
- Validate directory IDs
  - `7_automation\P_01999000042260125101_validate_dir_ids.py`
- Populate registry dir IDs
  - `7_automation\P_01999000042260125102_populate_registry_dir_ids.py`
- Add file IDs recursively
  - `2_cli_tools\file_id\P_01260207201000000198_add_ids_recursive.py`
- Run health check
  - `2_cli_tools\maintenance\P_01999000042260125113_healthcheck.py`
- Install automation
  - `2_cli_tools\maintenance\install_automation.py`

## Runtime Notes

- Primary runtime config is `.idpkg\config.json` at the project root.
- Primary runtime contract bundle is `.idpkg\contracts\`.
- The import/runtime surface is centered on:
  - `1_runtime\allocators\`
  - `1_runtime\handlers\`
  - `1_runtime\validators\`
  - `1_runtime\watchers\`

## Documentation

- `6_docs\01_CONTEXT_PRIMER.md`
  - Fastest orientation doc.
- `6_docs\00_MANIFEST.json`
  - Machine-readable map of the maintained docs set.
- `6_docs\operations\DUPLICATE_ID_PREVENTION.md`
  - Duplicate-prevention model and control layers.
- `6_docs\history\`
  - Historical implementation and scanner-reference material.

## Quick Commands

```powershell
python ID\7_automation\P_01999000042260125100_generate_dir_ids_gov_reg.py
python ID\2_cli_tools\file_id\P_01260207201000000198_add_ids_recursive.py
python ID\2_cli_tools\maintenance\P_01999000042260125113_healthcheck.py
python ID\2_cli_tools\maintenance\install_automation.py
```
