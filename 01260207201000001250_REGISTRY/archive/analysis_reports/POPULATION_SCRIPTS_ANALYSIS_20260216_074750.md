# Registry Column Population Scripts Analysis
**Generated:** 2026-02-16 07:47:50

## Overview

Total active population scripts found: 9

---

## Core Population Scripts
| Script | Purpose | Columns Handled |
|--------|---------|-----------------|
| `P_01260207201000000199_sync_registry_recursive.py` | Synchronize filesystem to registry | file_id, relative_path, geu_ids, geu_role, bundle_id, bundle_key, layer, artifact_kind, depends_on_file_ids, test_file_ids |
| `P_01999000042260125110_populate_registry_dir_ids_enhanced.py` | Populate directory IDs and module assignments | file_id, relative_path, dir_id, module_id |
| `P_01999000042260125104_update_registry_paths.py` | Update file paths in registry | file_id, relative_path, dir_id, module_id |
| `P_01999000042260125102_populate_registry_dir_ids.py` | Populate directory IDs and module assignments | file_id, relative_path, dir_id, module_id |
| `P_01260207233100000335_registry_writer_service_v2.py` | Registry write service (primary) | file_id, sha256 |
| `P_01260207233100000325_registry_writer.py` | Registry write operations | file_id |
| `P_01999000042260125108_registry_fs_reconciler.py` | Reconcile filesystem with registry | file_id, relative_path, dir_id, module_id |
| `P_01999000042260124023_scanner.py` | Scan filesystem and extract metadata | file_id, relative_path, dir_id, module_id, sha256, bundle_id, bundle_key, layer, artifact_kind, depends_on_file_ids, test_file_ids |
| `P_01260207233100000073_unified_ingest_engine.py` | Unified data ingestion engine | file_id, relative_path, dir_id, module_id |

---
## Detailed Script Analysis

### `P_01260207201000000199_sync_registry_recursive.py`

**Purpose:** Synchronize filesystem to registry
**Lines of Code:** 194
**Columns Handled:** file_id, relative_path, geu_ids, geu_role, bundle_id, bundle_key, layer, artifact_kind, depends_on_file_ids, test_file_ids
**Location:** `C:\Users\richg\Gov_Reg\P_01260207201000000199_sync_registry_recursive.py`

### `P_01999000042260125110_populate_registry_dir_ids_enhanced.py`

**Purpose:** Populate directory IDs and module assignments
**Lines of Code:** 357
**Columns Handled:** file_id, relative_path, dir_id, module_id
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001276_scripts\P_01999000042260125110_populate_registry_dir_ids_enhanced.py`

### `P_01999000042260125104_update_registry_paths.py`

**Purpose:** Update file paths in registry
**Lines of Code:** 230
**Columns Handled:** file_id, relative_path, dir_id, module_id
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001276_scripts\P_01999000042260125104_update_registry_paths.py`

### `P_01999000042260125102_populate_registry_dir_ids.py`

**Purpose:** Populate directory IDs and module assignments
**Lines of Code:** 146
**Columns Handled:** file_id, relative_path, dir_id, module_id
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001276_scripts\P_01999000042260125102_populate_registry_dir_ids.py`

### `P_01260207233100000335_registry_writer_service_v2.py`

**Purpose:** Registry write service (primary)
**Lines of Code:** 268
**Columns Handled:** file_id, sha256
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001289_src\01260207201000001297_registry_writer\P_01260207233100000335_registry_writer_service_v2.py`

### `P_01260207233100000325_registry_writer.py`

**Purpose:** Registry write operations
**Lines of Code:** 190
**Columns Handled:** file_id
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001289_src\01260207201000001296_registry_transition\P_01260207233100000325_registry_writer.py`

### `P_01999000042260125108_registry_fs_reconciler.py`

**Purpose:** Reconcile filesystem with registry
**Lines of Code:** 479
**Columns Handled:** file_id, relative_path, dir_id, module_id
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001173_govreg_core\P_01999000042260125108_registry_fs_reconciler.py`

### `P_01999000042260124023_scanner.py`

**Purpose:** Scan filesystem and extract metadata
**Lines of Code:** 313
**Columns Handled:** file_id, relative_path, dir_id, module_id, sha256, bundle_id, bundle_key, layer, artifact_kind, depends_on_file_ids, test_file_ids
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001173_govreg_core\P_01999000042260124023_scanner.py`

### `P_01260207233100000073_unified_ingest_engine.py`

**Purpose:** Unified data ingestion engine
**Lines of Code:** 297
**Columns Handled:** file_id, relative_path, dir_id, module_id
**Location:** `C:\Users\richg\Gov_Reg\01260207201000001173_govreg_core\P_01260207233100000073_unified_ingest_engine.py`


---
## Column Population Coverage

### Core Columns (27 original + critical new)

| Column | Populated By |
|--------|--------------|
| `artifact_kind` | scanner, ingest_engine |
| `bundle_id` | bundle_detector, writer_service |
| `bundle_key` | bundle_detector, writer_service |
| `depends_on_file_ids` | dependency_analyzer (if exists) |
| `dir_id` | populate_dir_ids scripts |
| `file_id` | scanner, writer_service, sync |
| `geu_ids` | ingest_engine, writer_service |
| `geu_role` | ingest_engine, writer_service |
| `layer` | scanner, ingest_engine |
| `module_id` | populate_dir_ids_enhanced |
| `mtime_utc` | scanner |
| `relative_path` | scanner, sync, reconciler |
| `sha256` | scanner |
| `size_bytes` | scanner |
| `test_file_ids` | test_discoverer (if exists) |

---
## Missing Column Population

### Columns needing population scripts:

- `record_id` - ⚠️ No dedicated script found
- `record_kind` - ⚠️ No dedicated script found
- `entity_id` - ⚠️ No dedicated script found
- `entity_kind` - ⚠️ No dedicated script found
- `created_by` - ⚠️ No dedicated script found
- `created_utc` - ⚠️ No dedicated script found
- `updated_by` - ⚠️ No dedicated script found
- `updated_utc` - ⚠️ No dedicated script found
- `status` - ⚠️ No dedicated script found
- `edge_id` - ⚠️ No dedicated script found
- `rel_type` - ⚠️ No dedicated script found
- `confidence` - ⚠️ No dedicated script found
- `evidence_*` - ⚠️ No dedicated script found
- `generator_*` - ⚠️ No dedicated script found
- `process_*` - ⚠️ No dedicated script found

**Note:** These may be populated by writer_service_v2 during write operations.

---
## Recommendations

1. **Primary Population Path:**
   - Run scanner → extract file metadata (sha256, size, paths)
   - Run populate_dir_ids_enhanced → add dir_id, module_id
   - Run ingest_engine → classify (layer, artifact_kind, geu_ids)
   - Use writer_service_v2 → write to registry with all columns

2. **Missing Scripts to Create:**
   - Entity/Edge population (record_id, entity_id, edge_id)
   - Audit trail population (created_by, updated_by timestamps)
   - Evidence tracking population
   - Process/generator metadata population

3. **Sync Operations:**
   - sync_registry_recursive.py keeps registry aligned with filesystem
   - Run periodically or on file system changes

