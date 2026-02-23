# ID System - Quick Reference

**Last Updated:** 2026-02-22  
**Purpose:** Unified 20-digit ID allocation & management for files and directories

---

## 📁 Folder Structure

```
ID/
├── 1_runtime/          → Core Python modules (import these)
│   ├── allocators/     → ID allocation engines
│   ├── handlers/       → File/Dir ID handlers
│   ├── validators/     → Validation & canonicality checks
│   └── watchers/       → Filesystem monitoring & auto-repair
│
├── 2_cli_tools/        → Command-line utilities (run these)
│   ├── dir_id/         → Directory ID generation & validation
│   ├── file_id/        → File ID assignment tools
│   ├── hooks/          → Git pre-commit/pre-push hooks
│   └── maintenance/    → Health checks & installation
│
├── 3_schemas/          → JSON schemas & validation contracts
├── 4_config/           → Configuration files & ID type definitions
├── 5_tests/            → Test suites (unit + integration)
├── 6_docs/             → Documentation (design, guides, reference)
└── 9_archive/          → Historical/deprecated files
```

---

## 🚀 Quick Start

### Generate Directory IDs
```bash
python 2_cli_tools/dir_id/P_01999000042260125100_generate_dir_ids_gov_reg.py
```

### Add File IDs Recursively
```bash
python 2_cli_tools/file_id/P_01260207201000000198_add_ids_recursive.py
```

### Install Git Hooks & Automation
```bash
python 2_cli_tools/maintenance/install_automation.py
```

### Run Health Check
```bash
python 2_cli_tools/maintenance/P_01999000042260125113_healthcheck.py
```

---

## 📖 Key Documentation

- **System Design**: `6_docs/system_design/01260207201000000122_DIR_ID_SYSTEM_DOCUMENTATION.md`
- **ID Contract**: `6_docs/system_design/01260207201000000174_ID_IDENTITY_CONTRACT.md`
- **User Guides**: `6_docs/user_guides/ID_AUTOMATION_COMPLETE.md`

---

## 🔧 Core Runtime Modules

### Allocators
- `P_01999000042260124031_unified_id_allocator.py` - Core 20-digit ID allocator
- `P_01999000042260125006_id_allocator_facade.py` - Simplified API

### Handlers
- `P_01999000042260125068_dir_id_handler.py` - .dir_id file operations
- `P_01260207233100000070_dir_identity_resolver.py` - Directory resolution

### Validators
- `P_01999000042260125000_gate_id_canonicality.py` - Canonicality enforcement
- `P_01999000042260124521_id_format_scanner.py` - Format validation

### Watchers
- `P_01999000042260125105_dir_id_watcher.py` - Filesystem monitoring
- `P_01999000042260125104_dir_id_auto_repair.py` - Auto-repair corrupted IDs

---

## 📋 Configuration

- **Active Config**: `4_config/idpkg_active_config.json`
- **ID Types**: `4_config/01260207201000000123_DOC-CONFIG-1208__ChatGPT-Stable ID Types.json`
- **Identity Config**: `4_config/01260207201000000175_IDENTITY_CONFIG (1).yaml`

---

## 🧪 Testing

```bash
# Run unit tests
python -m pytest 5_tests/unit/

# Run integration tests
python -m pytest 5_tests/integration/
```

---

## 📚 Related Folders

- **Registry**: `C:\Users\richg\Gov_Reg\01260207201000001250_REGISTRY`
- **Evidence**: `C:\Users\richg\Gov_Reg\01260207201000001148_evidence`
- **Core Governance**: `C:\Users\richg\Gov_Reg\01260207201000001173_govreg_core`

---

## 🗑️ Archived Files

Legacy and deprecated files have been moved to:
`C:\Users\richg\Gov_Reg\01260207201000001133_backups\ID_archived_files_20260222_030902\`

---

**Reorganization Date:** 2026-02-22  
**Total Active Files:** 47 (14 runtime, 9 CLI tools, 6 schemas, 4 config, 4 tests, 8 docs)  
**Archived Files:** 44 files moved to backups
