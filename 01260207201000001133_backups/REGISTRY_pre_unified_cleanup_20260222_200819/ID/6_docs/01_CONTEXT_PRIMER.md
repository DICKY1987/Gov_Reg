# ID System - AI Context Primer

**Load this first for maximum efficiency.**  
**Version:** 1.0.0  
**Last Updated:** 2026-02-22  
**Token Budget:** ~400 tokens

---

## System Identity

- **Name:** GovReg ID System
- **Version:** 1.0.0
- **Purpose:** Unified 20-digit ID allocation for files & directories
- **Status:** Production (47 active files)
- **Location:** `C:\Users\richg\Gov_Reg\ID`

---

## Critical Facts

1. All IDs are 20-digit numeric strings
2. `file_id`: `\d{20}` (no prefix) - Example: `01999000042260124027`
3. `doc_id`: `P_\d{20}` (Python prefix) - Example: `P_01999000042260124027`
4. `dir_id`: 20-digit ID stored in `.dir_id` JSON files
5. Allocator uses global counter: `%APPDATA%\GovReg\IdAllocator\COUNTER_STORE.json`

---

## File System Structure

```
ID/
├── 1_runtime/              → Core modules (14 files)
│   ├── allocators/         → ID generation (4)
│   ├── handlers/           → File/dir operations (2)
│   ├── validators/         → Validation & checks (4)
│   └── watchers/           → Monitoring & repair (4)
├── 2_cli_tools/            → CLI utilities (9 files)
│   ├── dir_id/             → Directory tools (3)
│   ├── file_id/            → File tools (2)
│   ├── hooks/              → Git hooks (2)
│   └── maintenance/        → Health & install (2)
├── 3_schemas/              → JSON schemas (6 files)
├── 4_config/               → Configuration (4 files)
├── 5_tests/                → Tests (4 files)
└── 6_docs/                 → This documentation
```

---

## Most Common Operations

| Task | Entry Point |
|------|-------------|
| Generate dir IDs | `2_cli_tools/dir_id/P_01999000042260125100_generate_dir_ids_gov_reg.py` |
| Allocate new ID | `1_runtime/allocators/P_01999000042260124031_unified_id_allocator.py::allocate_id()` |
| Validate system | `2_cli_tools/maintenance/P_01999000042260125113_healthcheck.py` |
| Repair corrupted .dir_id | `1_runtime/watchers/P_01999000042260125104_dir_id_auto_repair.py` |
| Add file IDs | `2_cli_tools/file_id/P_01260207201000000198_add_ids_recursive.py` |

---

## State Dependencies

### Global State
- **Counter Store:** `%APPDATA%\GovReg\IdAllocator\COUNTER_STORE.json`
- **Lock Mechanism:** File locks with 5000ms timeout
- **Configuration:** `.idpkg\config.json` (project root)

### Per-Directory State
- **Directory ID:** `.dir_id` JSON file in each governed directory
- **Schema:** `3_schemas/.dir_id.schema.json`

### External Dependencies
- **Registry:** `../../01260207201000001250_REGISTRY/`
- **Backups:** `../../01260207201000001133_backups/`

---

## Error Handling

- All errors documented in: `operations/troubleshooting.yaml`
- Failure modes have explicit rollback procedures
- Lock timeouts default to 5000ms
- Corrupted files auto-quarantined before repair

---

## Documentation Navigation

### Critical (Load First)
1. **Contracts** → `contracts/id_contract.yaml` - ID terminology SSOT
2. **Runtime** → `runtime/allocators.yaml` - Core allocation behavior

### Operational
3. **Workflows** → `operations/workflows.yaml` - Standard procedures
4. **Troubleshooting** → `operations/troubleshooting.yaml` - Error resolution

### Reference
5. **Schemas** → `schemas/*.json` - Data structure definitions
6. **History** → `history/` - Project completion reports (low priority)

---

## Token Budget Guidance

| Context Level | Load | Estimated Tokens |
|---------------|------|------------------|
| **Minimal** | This primer + `contracts/id_contract.yaml` | 900 |
| **Standard** | Minimal + `runtime/allocators.yaml` | 2,100 |
| **Full** | Standard + `operations/workflows.yaml` | 5,000 |

---

## Quick Command Reference

```bash
# Generate directory IDs
python 2_cli_tools/dir_id/P_01999000042260125100_generate_dir_ids_gov_reg.py

# Add file IDs recursively
python 2_cli_tools/file_id/P_01260207201000000198_add_ids_recursive.py

# Validate system health
python 2_cli_tools/maintenance/P_01999000042260125113_healthcheck.py

# Install automation (git hooks, watchers)
python 2_cli_tools/maintenance/install_automation.py
```

---

## Import Patterns

```python
# Allocate ID
from ID.1_runtime.allocators.P_01999000042260124031_unified_id_allocator import allocate_id
new_id = allocate_id(zone='governed')

# Handle .dir_id files
from ID.1_runtime.handlers.P_01999000042260125068_dir_id_handler import read_dir_id, write_dir_id
dir_data = read_dir_id('/path/to/dir')

# Validate ID format
from ID.1_runtime.validators.P_01999000042260125002_canonical_id_patterns import validate_file_id
is_valid = validate_file_id('01999000042260124027')
```

---

**Next Steps:**
- Load `contracts/id_contract.yaml` for terminology
- Load `00_MANIFEST.json` for full documentation map
- Query specific operations in `operations/workflows.yaml`
