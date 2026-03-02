# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**EAFIX Directory Management System** - A multi-subsystem platform for file identity management, module contracts, and terminology governance. The system assigns 16-digit numeric ID prefixes to files and provides machine-checkable completion contracts.

**Status**: Production Ready (v2.1)

## Architecture

```
Directory management system/
├── id_16_digit/              # Core identity system (702 IDs allocated)
├── DOD_modules_contracts/    # Machine-checkable "done" contracts
├── Multi_project_glossary/   # 83+ term governance framework
├── file watcher/             # Real-time file monitoring
├── GIT_OPS/                  # Git automation & delivery
└── UI/                       # UI components
```

## Subsystem-Specific Guidance

Each subsystem has its own CLAUDE.md with detailed instructions:
- `id_16_digit/0199900006260118_CLAUDE.md` - Identity system commands and ID structure
- `DOD_modules_contracts/CLAUDE.md` - Module contract validation
- `Multi_project_glossary/CLAUDE.md` - Glossary validation and term updates

## Essential Commands

### Identity System (id_16_digit/)

```bash
cd id_16_digit

# Scan files and derive identity metadata
python "Enhanced File Scanner v2.py" --identity-config IDENTITY_CONFIG.yaml -f csv .

# Registry CLI operations
python automation/2026012120420011_registry_cli.py validate --strict
python automation/2026012120420011_registry_cli.py derive --apply
python automation/2026012120420011_registry_cli.py export --format csv --output registry.csv
python automation/2026012120420011_registry_cli.py export --format sqlite --output registry.sqlite

# Allocate single ID
python -c "from core.registry_store import RegistryStore; r = RegistryStore('registry/ID_REGISTRY.json'); print(r.allocate_id('999', '20', 'path/to/file.py', 'YOUR_NAME'))"

# Run tests (34/34 passing)
cd tests
python -m pytest 2026012120460003_test_derive_apply.py -v
python -m pytest 2026012120460004_test_export.py -v
python -m pytest 2026012120460005_test_validators.py -v
```

### Module Contracts (DOD_modules_contracts/)

```powershell
cd DOD_modules_contracts
powershell -ExecutionPolicy Bypass -File scripts/validate_structure.ps1 -Mode validation
powershell -ExecutionPolicy Bypass -File scripts/validate_structure.ps1 -Mode acceptance
```

### Glossary System (Multi_project_glossary/)

```bash
cd Multi_project_glossary
python scripts/DOC-SCRIPT-SCRIPTS-VALIDATE-GLOSSARY-265__validate_glossary.py
python scripts/DOC-SCRIPT-SCRIPTS-UPDATE-TERM-264__update_term.py --spec updates/add-schemas.yaml --dry-run
```

## 16-Digit ID Structure

All identity-managed files use prefix format `TTNNNSSSSSSSSSSS_filename.ext`:

```
TTNNNSSSSSSSSSSS
││││└─────────┴─ SCOPE (6 digits): Collision domain (fixed: 260118)
│││└──────────── SEQ (5 digits): Monotonic counter (allocated)
││└───────────── NS (3 digits): Namespace code (derived from path)
└┴────────────── TYPE (2 digits): File type code (derived from extension)
```

**Type Codes**: 01=md, 02=txt, 10=csv, 11=json, 12=yaml, 20=py, 21=ps1, 00=unknown
**Namespace Codes**: 100=docs, 110=data, 200=python scripts, 420=reports, 999=uncategorized

## Key Registry Files

| File | Purpose |
|------|---------|
| `id_16_digit/registry/ID_REGISTRY.json` | Master ID allocation registry |
| `id_16_digit/registry/identity_audit_log.jsonl` | Immutable allocation history |
| `id_16_digit/IDENTITY_CONFIG.yaml` | Type codes & namespace routing |
| `id_16_digit/contracts/*.yaml` | Write, derivation, evidence policies |
| `DOD_modules_contracts/module.manifest.yaml` | Module contract SSOT |

## Design Patterns

- **Registry as SSOT**: All file identity tracked in `ID_REGISTRY.json` with 80+ column schema
- **Policy-Driven Validation**: YAML policies define per-column write ownership and derivation rules
- **Atomic Operations**: Registry updates use `os.replace()` with automatic backups
- **Evidence-Based Validation**: Validators emit JSON reports to `evidence/` directories
- **Checkable Contracts**: Module completion defined by machine-enforceable manifests, not prose

## Dependencies

- Python 3.11+
- PyYAML (`pip install pyyaml`)
- PowerShell (for contract validation scripts)
