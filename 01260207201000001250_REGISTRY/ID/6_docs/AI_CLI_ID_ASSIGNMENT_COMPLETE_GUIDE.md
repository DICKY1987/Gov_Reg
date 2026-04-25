# Complete Guide: AI CLI File and Directory ID Assignment

**Document ID:** DOC-GUIDE-AI-CLI-ID-ASSIGNMENT-001  
**Created:** 2026-03-09  
**Purpose:** Provide complete context and instructions for AI CLI apps to add file and directory IDs  
**Status:** ACTIVE  

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [System Architecture](#system-architecture)
4. [ID Format Specifications](#id-format-specifications)
5. [Prerequisites & Dependencies](#prerequisites--dependencies)
6. [Step-by-Step Instructions](#step-by-step-instructions)
7. [Code Examples](#code-examples)
8. [Validation & Testing](#validation--testing)
9. [Error Handling](#error-handling)
10. [Reference Files](#reference-files)

---

## Overview

### What This System Does

The Gov_Reg repository uses a **unified ID allocation system** that assigns unique 20-digit identifiers to:
- **Directories** (via `.dir_id` anchor files)
- **Files** (via filename prefixes)

### Why IDs Are Needed

**Before IDs:**
- 34 directories named "src" - which one?
- 31 directories named "tests" - which one?
- 11 directories named "automation" - which one?
- Non-deterministic path resolution
- Ambiguous references in code and documentation

**After IDs:**
- Each directory has a unique physical identity (20-digit dir_id)
- Each file has a unique identifier in its name
- Zero ambiguity in references
- Automated validation ensures compliance

---

## Core Concepts

### 1. Two-Layer Identity Model

```
DIRECTORIES:
├─ Physical Identity: .dir_id file with 20-digit ID
│  Example: 01999000042260124550
│  Purpose: Inventory, forensics, drift detection
│  Storage: .dir_id JSON file in directory
│
└─ Semantic Identity: Human-readable keys (optional)
   Example: runtime:doc_id:root
   Purpose: Code references that survive refactoring
   Storage: path_index.yaml registry

FILES:
└─ Physical Identity: ID in filename
   Python: P_01999000042260125100_script_name.py
   Other:  01999000042260125101_document.md
```

### 2. Governance Zones

Not all directories/files need IDs. The system uses **zones**:

| Zone | Depth | ID Required? | Examples |
|------|-------|--------------|----------|
| **Governed** | ≥ 1 | ✅ Yes | `src/`, `docs/`, `scripts/` |
| **Excluded** | Any | ❌ No | `.git/`, `__pycache__/`, `node_modules/` |
| **Root** | 0 | ⚠️ Special | Project root only |

### 3. ID Allocation Source

**Single Source of Truth:** All IDs come from `COUNTER_STORE.json`

```json
{
  "schema_version": "COUNTER-STORE-1.0",
  "scope": "012602",
  "counters": {
    "012602:072:01": 1234
  }
}
```

The counter is atomically incremented for each new ID allocation.

---

## System Architecture

### File Structure

```
Gov_Reg/
├── 01260207201000001250_REGISTRY/
│   ├── .idpkg/
│   │   └── config.json  ← Runtime IDPKG configuration
│   │   └── contracts/   ← Runtime contract bundle
│   └── ID/
│       ├── 1_runtime/
│       │   ├── allocators/
│       │   │   └── P_01999000042260124031_unified_id_allocator.py  ← Core allocator
│       │   ├── handlers/
│       │   │   └── P_01999000042260125068_dir_id_handler.py  ← .dir_id file operations
│       │   └── validators/
│       │       └── P_01999000042260125067_zone_classifier.py  ← Zone detection
│       ├── 2_cli_tools/
│       │   ├── file_id/
│       │   │   └── P_01260207201000000198_add_ids_recursive.py  ← File ID tool
│       │   └── hooks/
│       ├── 3_schemas/
│       │   └── 01260207201000000877_DIR_ID_ANCHOR.schema.json  ← .dir_id schema
│       ├── 7_automation/
│       │   ├── P_01999000042260125100_generate_dir_ids_gov_reg.py  ← Dir ID generator
│       │   ├── P_01999000042260125101_validate_dir_ids.py  ← Dir ID validator
│       │   └── P_01999000042260125102_populate_registry_dir_ids.py  ← Registry updater
│       └── 6_docs/
│           └── 01260207201000000122_DIR_ID_SYSTEM_DOCUMENTATION.md  ← Full docs
│
├── 01260207201000001173_govreg_core/  ← Core runtime modules
│   ├── P_01999000042260124031_unified_id_allocator.py
│   ├── P_01260207233100000068_zone_classifier.py
│   ├── P_01260207233100000069_dir_id_handler.py
│   └── P_01999000042260126000__idpkg_runtime.py
│
└── [COUNTER_STORE file - find using glob]
    └── XXXXXXXXXXXXXXXXXXXXXX_COUNTER_STORE.json  ← ID counter SSOT
```

---

## ID Format Specifications

### Directory ID Format

**20-digit numeric string**

```
Format: 01260207201000001234
        └─────┬─────┘└───┬───┘
         Prefix(11)  Counter(9)

Components:
- Scope:     012602 (6 digits)
- Namespace: 072 (3 digits)
- Type:      01 (2 digits)
- Counter:   000001234 (9 digits, zero-padded)
```

**Validation Pattern:** `^\d{20}$`

### File ID Format

**Same 20-digit format, but in filename:**

```python
# Python files
P_01260207201000001234_filename.py
  └────────┬─────────────┘
       20-digit ID

# Other files
01260207201000001234_filename.md
└────────┬─────────────┘
     20-digit ID
```

### .dir_id File Format (JSON)

```json
{
  "dir_id": "01999000042260124550",
  "allocated_at_utc": "2026-03-09T19:30:00Z",
  "allocator_version": "1.0.0",
  "project_root_id": "01999000042260124068",
  "relative_path": "src/module_a",
  "depth": 2,
  "zone": "governed",
  "parent_dir_id": "01999000042260124549"
}
```

**Required fields:**
- `dir_id` (string, 20 digits)
- `allocated_at_utc` (ISO 8601 timestamp)
- `allocator_version` (string)
- `project_root_id` (string, 20 digits)
- `relative_path` (string, forward slashes)

---

## Prerequisites & Dependencies

### 1. Locate COUNTER_STORE.json

```python
from pathlib import Path

# Find counter store
counter_stores = list(Path('.').glob('*COUNTER_STORE.json'))
counter_stores = [f for f in counter_stores if not f.name.endswith('.lock')]

if not counter_stores:
    raise FileNotFoundError("COUNTER_STORE.json not found in repository")

counter_store = counter_stores[0]
print(f"Using: {counter_store}")
```

### 2. Required Python Modules

```python
# Core Python (stdlib)
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Project modules (add to sys.path)
from govreg_core.P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator
from govreg_core.P_01260207233100000068_zone_classifier import ZoneClassifier
from govreg_core.P_01260207233100000069_dir_id_handler import DirIdManager
from govreg_core.P_01999000042260126000__idpkg_runtime import IdpkgConfig
```

### 3. Configuration File

Location: `01260207201000001250_REGISTRY/.idpkg/config.json`

Contains:
- Project root path
- Project root ID
- Registry path
- Exclusion patterns

---

## Step-by-Step Instructions

### TASK 1: Add Directory IDs

#### Step 1: Initialize the System

```python
from pathlib import Path
import sys

# Add required paths
registry_id_path = Path(__file__).resolve().parent.parent / "01260207201000001250_REGISTRY" / "ID"
core_path = Path(__file__).resolve().parent.parent / "01260207201000001173_govreg_core"

sys.path.insert(0, str(core_path))
sys.path.insert(0, str(registry_id_path))

from P_01999000042260126000__idpkg_runtime import IdpkgConfig, IdpkgEngine
from P_01260207233100000068_zone_classifier import ZoneClassifier
```

#### Step 2: Load Configuration

```python
# Load IDPKG config
config_path = Path("01260207201000001250_REGISTRY/.idpkg/config.json")
config = IdpkgConfig.load(config_path)

print(f"Project root: {config.project_root_path}")
print(f"Project root ID: {config.project_root_id}")
```

#### Step 3: Scan and Identify Directories Needing IDs

```python
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver

zone_classifier = ZoneClassifier(exclusions=config.exclusions)
resolver = DirectoryIdentityResolver(
    project_root=config.project_root_path,
    project_root_id=config.project_root_id,
    zone_classifier=zone_classifier,
)

# Find directories missing .dir_id
missing_ids = []

for directory in config.project_root_path.rglob("*"):
    if not directory.is_dir():
        continue
    
    rel_path = str(directory.relative_to(config.project_root_path)).replace("\\", "/")
    
    # Skip excluded directories
    if zone_classifier.should_skip(rel_path):
        continue
    
    # Check if governed
    zone = zone_classifier.compute_zone(rel_path)
    if zone != "governed":
        continue
    
    # Check for existing .dir_id
    dir_id_file = directory / ".dir_id"
    if not dir_id_file.exists():
        missing_ids.append(directory)
        print(f"Missing .dir_id: {rel_path}")

print(f"\nTotal directories needing IDs: {len(missing_ids)}")
```

#### Step 4: Generate .dir_id Files

```python
# Option A: Use the provided script (recommended)
import subprocess

result = subprocess.run([
    "python",
    "01260207201000001250_REGISTRY/ID/7_automation/P_01999000042260125100_generate_dir_ids_gov_reg.py",
    "--config", str(config_path)
], capture_output=True, text=True)

print(result.stdout)

# Option B: Manual allocation
for directory in missing_ids:
    result = resolver.resolve_identity(directory, allocate_if_missing=True)
    if result.status == "allocated":
        print(f"Created: {directory} -> {result.dir_id}")
    else:
        print(f"Error: {directory}: {result.error_message}")
```

#### Step 5: Validate Generated IDs

```python
# Run validation
result = subprocess.run([
    "python",
    "01260207201000001250_REGISTRY/ID/7_automation/P_01999000042260125101_validate_dir_ids.py",
    "--config", str(config_path)
], capture_output=True, text=True)

print(result.stdout)

if result.returncode != 0:
    print("❌ Validation failed - review errors above")
else:
    print("✅ All .dir_id files valid")
```

---

### TASK 2: Add File IDs

#### Step 1: Find Counter Store

```python
from pathlib import Path

counter_stores = list(Path('.').glob('*COUNTER_STORE.json'))
counter_stores = [f for f in counter_stores if not f.name.endswith('.lock')]

if not counter_stores:
    raise FileNotFoundError("COUNTER_STORE.json not found")

counter_store = counter_stores[0]
print(f"Using counter store: {counter_store}")
```

#### Step 2: Initialize ID Allocator

```python
from govreg_core.P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator

allocator = UnifiedIDAllocator(counter_store)
```

#### Step 3: Scan for Files Needing IDs

```python
# Define target extensions
target_extensions = {'.md', '.txt', '.py', '.ps1', '.yaml', '.json', '.yml'}

# Skip these directories
skip_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', '.mypy_cache', 
             'htmlcov', 'out', '.runs', '.state', '.coverage'}

def has_file_id(filename: str) -> bool:
    """Check if filename already has an ID."""
    # Python files: P_XXXXXXXXXXXXXXXXXXXX_filename.py
    if filename.startswith('P_') and len(filename) > 22 and filename[2:22].isdigit():
        return True
    # Other files: XXXXXXXXXXXXXXXXXXXX_filename.ext
    if len(filename) > 20 and filename[:20].isdigit():
        return True
    return False

files_needing_ids = []

for file_path in Path('.').rglob('*'):
    # Skip if not a file
    if not file_path.is_file():
        continue
    
    # Skip if wrong extension
    if file_path.suffix not in target_extensions:
        continue
    
    # Skip if already has ID
    if has_file_id(file_path.name):
        continue
    
    # Skip excluded directories
    if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
        continue
    
    files_needing_ids.append(file_path)

print(f"Found {len(files_needing_ids)} files needing IDs")
```

#### Step 4: Allocate and Rename Files

```python
from collections import defaultdict

# Group by directory for reporting
by_dir = defaultdict(list)
for f in files_needing_ids:
    rel_dir = str(f.parent.relative_to('.'))
    by_dir[rel_dir].append(f)

print(f"\nFiles by directory (top 10):")
for dir_path in sorted(by_dir.keys())[:10]:
    print(f"  {dir_path}: {len(by_dir[dir_path])} files")

# Confirm action
print(f"\n⚠️  About to rename {len(files_needing_ids)} files")
response = input("Continue? (y/N): ")
if response.lower() != 'y':
    print("Aborted.")
    sys.exit(0)

print("\nAllocating IDs and renaming files...\n")

success_count = 0
error_count = 0
errors = []

for i, file_path in enumerate(sorted(files_needing_ids), 1):
    try:
        # Allocate new ID
        new_id = allocator.allocate_single_id(
            purpose="file_id_assignment",
            allocated_by="ai_cli_automation"
        )
        
        # Determine prefix based on extension
        if file_path.suffix == '.py':
            prefix = f"P_{new_id}_"
        else:
            prefix = f"{new_id}_"
        
        # Create new filename
        new_name = prefix + file_path.name
        new_path = file_path.parent / new_name
        
        # Rename file
        file_path.rename(new_path)
        success_count += 1
        
        # Progress update every 50 files
        if i % 50 == 0 or i == len(files_needing_ids):
            print(f"  Progress: {i}/{len(files_needing_ids)} "
                  f"({success_count} success, {error_count} errors)")
    
    except Exception as exc:
        error_count += 1
        errors.append(f"{file_path}: {exc}")
        print(f"  ❌ Error: {file_path}: {exc}")

print("\n" + "=" * 70)
print("FILE ID ASSIGNMENT SUMMARY")
print("=" * 70)
print(f"Total files processed: {len(files_needing_ids)}")
print(f"Successfully renamed: {success_count}")
print(f"Errors: {error_count}")

if errors:
    print("\nErrors encountered:")
    for error in errors[:10]:
        print(f"  - {error}")
```

---

### TASK 3: Update Registry

After adding directory IDs, update the central registry:

```python
import subprocess

result = subprocess.run([
    "python",
    "01260207201000001250_REGISTRY/ID/7_automation/P_01999000042260125102_populate_registry_dir_ids.py",
    "--config", "01260207201000001250_REGISTRY/.idpkg/config.json"
], capture_output=True, text=True)

print(result.stdout)

if result.returncode != 0:
    print("❌ Registry update failed")
else:
    print("✅ Registry updated successfully")
```

---

## Code Examples

### Complete Directory ID Assignment Script

```python
#!/usr/bin/env python3
"""
AI CLI: Add directory IDs to all governed directories.
"""
from pathlib import Path
import sys
import subprocess

# Setup paths
repo_root = Path(__file__).resolve().parent
registry_root = repo_root / "01260207201000001250_REGISTRY"
registry_id = registry_root / "ID"
config_file = registry_root / ".idpkg" / "config.json"

if not config_file.exists():
    print(f"❌ Config not found: {config_file}")
    sys.exit(1)

print("=" * 70)
print("DIRECTORY ID ASSIGNMENT")
print("=" * 70)

# Step 1: Generate dir_ids (dry run first)
print("\n[1/4] Dry run - preview changes...")
result = subprocess.run([
    "python",
    str(registry_id / "7_automation" / "P_01999000042260125100_generate_dir_ids_gov_reg.py"),
    "--config", str(config_file),
    "--dry-run"
], capture_output=True, text=True)
print(result.stdout)

# Confirm
response = input("\nProceed with actual generation? (y/N): ")
if response.lower() != 'y':
    print("Aborted.")
    sys.exit(0)

# Step 2: Generate for real
print("\n[2/4] Generating .dir_id files...")
result = subprocess.run([
    "python",
    str(registry_id / "7_automation" / "P_01999000042260125100_generate_dir_ids_gov_reg.py"),
    "--config", str(config_file)
], capture_output=True, text=True)
print(result.stdout)

if result.returncode != 0:
    print("❌ Generation failed")
    sys.exit(1)

# Step 3: Validate
print("\n[3/4] Validating .dir_id files...")
result = subprocess.run([
    "python",
    str(registry_id / "7_automation" / "P_01999000042260125101_validate_dir_ids.py"),
    "--config", str(config_file)
], capture_output=True, text=True)
print(result.stdout)

if result.returncode != 0:
    print("❌ Validation failed")
    sys.exit(1)

# Step 4: Update registry
print("\n[4/4] Updating registry...")
result = subprocess.run([
    "python",
    str(registry_id / "7_automation" / "P_01999000042260125102_populate_registry_dir_ids.py"),
    "--config", str(config_file)
], capture_output=True, text=True)
print(result.stdout)

print("\n" + "=" * 70)
print("✅ DIRECTORY ID ASSIGNMENT COMPLETE")
print("=" * 70)
```

### Complete File ID Assignment Script

```python
#!/usr/bin/env python3
"""
AI CLI: Add file IDs to all files recursively.
"""
from pathlib import Path
import sys

# Find counter store
counter_stores = list(Path('.').glob('*COUNTER_STORE.json'))
counter_stores = [f for f in counter_stores if not f.name.endswith('.lock')]

if not counter_stores:
    print("❌ COUNTER_STORE.json not found")
    sys.exit(1)

counter_store = counter_stores[0]
print(f"Using counter store: {counter_store.name}\n")

# Add to path and import
core_path = Path(__file__).resolve().parent / "01260207201000001173_govreg_core"
sys.path.insert(0, str(core_path))

from P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator

# Initialize allocator
allocator = UnifiedIDAllocator(counter_store)

# Define targets
target_extensions = {'.md', '.txt', '.py', '.ps1', '.yaml', '.json', '.yml'}
skip_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', 
             '.mypy_cache', 'htmlcov', 'out', '.runs', '.state'}

def has_id(name: str) -> bool:
    if name.startswith('P_') and len(name) > 22 and name[2:22].isdigit():
        return True
    if len(name) > 20 and name[:20].isdigit():
        return True
    return False

# Scan files
print("Scanning for files needing IDs...\n")
files_to_process = []

for file_path in Path('.').rglob('*'):
    if not file_path.is_file():
        continue
    if file_path.suffix not in target_extensions:
        continue
    if has_id(file_path.name):
        continue
    if any(skip in file_path.parts for skip in skip_dirs):
        continue
    
    files_to_process.append(file_path)

print(f"Found {len(files_to_process)} files needing IDs\n")

if not files_to_process:
    print("✅ All files have IDs")
    sys.exit(0)

# Confirm
response = input(f"⚠️  Rename {len(files_to_process)} files? (y/N): ")
if response.lower() != 'y':
    print("Aborted.")
    sys.exit(0)

# Process files
print("\nProcessing files...\n")
success = 0
errors = []

for i, file_path in enumerate(sorted(files_to_process), 1):
    try:
        new_id = allocator.allocate_single_id(
            purpose="file_id_batch",
            allocated_by="ai_cli"
        )
        
        prefix = f"P_{new_id}_" if file_path.suffix == '.py' else f"{new_id}_"
        new_path = file_path.parent / (prefix + file_path.name)
        
        file_path.rename(new_path)
        success += 1
        
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(files_to_process)}")
    
    except Exception as exc:
        errors.append(f"{file_path}: {exc}")

print(f"\n✅ Complete: {success} files renamed")
if errors:
    print(f"❌ Errors: {len(errors)}")
    for err in errors[:5]:
        print(f"  - {err}")
```

---

## Validation & Testing

### Validate Directory IDs

```bash
python 01260207201000001250_REGISTRY/ID/7_automation/P_01999000042260125101_validate_dir_ids.py \
  --config 01260207201000001250_REGISTRY/.idpkg/config.json
```

**Expected output:**
```
Valid: src/module_a
Valid: docs/guides
...
✅ All .dir_id files are valid
```

### Validate File IDs

```python
from pathlib import Path

def validate_file_id(filename: str) -> tuple[bool, str]:
    """Validate file ID format."""
    # Python files
    if filename.startswith('P_'):
        if len(filename) < 23:
            return False, "Python file ID too short"
        id_part = filename[2:22]
        if not id_part.isdigit() or len(id_part) != 20:
            return False, f"Invalid ID format: {id_part}"
        return True, "Valid"
    
    # Other files
    if len(filename) < 21:
        return False, "File ID too short"
    id_part = filename[:20]
    if not id_part.isdigit() or len(id_part) != 20:
        return False, f"Invalid ID format: {id_part}"
    return True, "Valid"

# Test
test_files = [
    "P_01260207201000001234_script.py",
    "01260207201000001235_document.md",
    "invalid_file.txt"
]

for filename in test_files:
    valid, msg = validate_file_id(filename)
    print(f"{filename}: {msg}")
```

### Check for Duplicates

```python
from pathlib import Path
from collections import Counter

# Check directory IDs
dir_ids = []
for dir_id_file in Path('.').rglob('.dir_id'):
    with open(dir_id_file) as f:
        data = json.load(f)
        dir_ids.append(data['dir_id'])

duplicates = [id for id, count in Counter(dir_ids).items() if count > 1]
if duplicates:
    print(f"❌ Duplicate dir_ids found: {duplicates}")
else:
    print("✅ All dir_ids are unique")

# Check file IDs
file_ids = []
for file_path in Path('.').rglob('*'):
    if not file_path.is_file():
        continue
    
    name = file_path.name
    if name.startswith('P_') and len(name) > 22:
        file_ids.append(name[2:22])
    elif len(name) > 20 and name[:20].isdigit():
        file_ids.append(name[:20])

duplicates = [id for id, count in Counter(file_ids).items() if count > 1]
if duplicates:
    print(f"❌ Duplicate file_ids found: {duplicates}")
else:
    print("✅ All file_ids are unique")
```

---

## Error Handling

### Common Errors and Solutions

#### Error: "COUNTER_STORE.json not found"

**Solution:**
```python
# Search in parent directories
from pathlib import Path

for parent in [Path('.'), Path('..'), Path('../..')]:
    stores = list(parent.glob('*COUNTER_STORE.json'))
    if stores:
        print(f"Found: {stores[0]}")
        break
```

#### Error: "Config not found"

**Solution:**
```python
config_path = Path("01260207201000001250_REGISTRY/.idpkg/config.json")
if not config_path.exists():
    print(f"❌ Config not found at: {config_path}")
    print("Available configs:")
    for cfg in Path('.').rglob('idpkg*.json'):
        print(f"  - {cfg}")
```

#### Error: "Module not found"

**Solution:**
```python
import sys
from pathlib import Path

# Add all required paths
paths_to_add = [
    "01260207201000001173_govreg_core",
    "01260207201000001250_REGISTRY/ID/1_runtime",
    "01260207201000001276_scripts"
]

for path in paths_to_add:
    full_path = Path(__file__).resolve().parent / path
    if full_path.exists():
        sys.path.insert(0, str(full_path))
        print(f"Added to path: {full_path}")
```

#### Error: "Permission denied" (Windows)

**Solution:**
```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        file_path.rename(new_path)
        break
    except PermissionError:
        if attempt < max_retries - 1:
            time.sleep(0.5)
            continue
        raise
```

#### Error: "dir_id already exists"

**Solution:**
```python
# Check existing .dir_id before creating
dir_id_file = directory / ".dir_id"
if dir_id_file.exists():
    with open(dir_id_file) as f:
        existing = json.load(f)
    print(f"Directory already has ID: {existing['dir_id']}")
    # Skip or update as needed
```

---

## Reference Files

### Key Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| **Dir ID Generator** | `ID/7_automation/P_01999000042260125100_generate_dir_ids_gov_reg.py` | Creates .dir_id files |
| **Dir ID Validator** | `ID/7_automation/P_01999000042260125101_validate_dir_ids.py` | Validates .dir_id files |
| **Registry Updater** | `ID/7_automation/P_01999000042260125102_populate_registry_dir_ids.py` | Updates registry |
| **File ID Tool** | `ID/2_cli_tools/file_id/P_01260207201000000198_add_ids_recursive.py` | Adds file IDs |
| **Unified Allocator** | `govreg_core/P_01999000042260124031_unified_id_allocator.py` | Core ID allocator |

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| **IDPKG Config** | `.idpkg/config.json` | System configuration |
| **Runtime Contracts** | `.idpkg/contracts/` | Runtime-owned IDPKG contract bundle |
| **Counter Store** | `*COUNTER_STORE.json` (root) | ID counter SSOT |
| **Dir ID Schema** | `ID/3_schemas/01260207201000000877_DIR_ID_ANCHOR.schema.json` | .dir_id validation |

### Documentation

| Document | Location | Content |
|----------|----------|---------|
| **System Docs** | `01260207201000000122_DIR_ID_SYSTEM_DOCUMENTATION.md` | Complete reference |
| **Quick Start** | `ID/00_README.md` | Quick reference |
| **ID Contract** | `ID/6_docs/contracts/01260207201000000174_ID_IDENTITY_CONTRACT.md` | Design contract |

---

## Quick Command Reference

### Directory IDs

```bash
# Dry run (preview)
python ID/7_automation/P_01999000042260125100_generate_dir_ids_gov_reg.py --dry-run

# Generate IDs
python ID/7_automation/P_01999000042260125100_generate_dir_ids_gov_reg.py

# Validate IDs
python ID/7_automation/P_01999000042260125101_validate_dir_ids.py

# Update registry
python ID/7_automation/P_01999000042260125102_populate_registry_dir_ids.py
```

### File IDs

```bash
# Add IDs recursively
python ID/2_cli_tools/file_id/P_01260207201000000198_add_ids_recursive.py
```

### Verification

```powershell
# Count .dir_id files
(Get-ChildItem -Recurse -Filter ".dir_id" -File).Count

# Find directories without .dir_id
Get-ChildItem -Recurse -Directory | Where-Object { -not (Test-Path "$($_.FullName)\.dir_id") }

# Check for duplicate IDs (PowerShell)
Get-ChildItem -Recurse -Filter ".dir_id" | ForEach-Object { 
    (Get-Content $_ | ConvertFrom-Json).dir_id 
} | Group-Object | Where-Object { $_.Count -gt 1 }
```

---

## Best Practices

### DO ✅

1. **Always use the provided scripts** - they handle edge cases
2. **Run in dry-run mode first** - preview changes before applying
3. **Validate after generation** - ensure IDs are correct
4. **Check for duplicates** - verify uniqueness
5. **Update the registry** - keep central registry in sync
6. **Commit .dir_id files** - they're part of source control

### DON'T ❌

1. **Don't manually edit .dir_id files** - use the tools
2. **Don't skip validation** - always validate after changes
3. **Don't reuse IDs** - each ID is unique and permanent
4. **Don't delete .dir_id files** - they track directory identity
5. **Don't modify the counter store manually** - use the allocator
6. **Don't add IDs to excluded directories** - respect zone rules

---

## Troubleshooting Checklist

- [ ] COUNTER_STORE.json exists and is readable
- [ ] Config file exists at expected location
- [ ] Python paths include govreg_core and ID/1_runtime
- [ ] Target directories are "governed" (depth ≥ 1, not excluded)
- [ ] No file locks preventing writes
- [ ] Sufficient permissions to rename files/create directories
- [ ] No duplicate IDs in system
- [ ] Validation scripts run without errors

---

**END OF GUIDE**

For additional help, consult:
- Full documentation: `01260207201000000122_DIR_ID_SYSTEM_DOCUMENTATION.md`
- Quick reference: `ID/00_README.md`
- Schema definitions: `ID/3_schemas/` for `.dir_id` anchors and `.idpkg/contracts/` for runtime contracts

**Last Updated:** 2026-03-09T19:30:00Z  
**Document Status:** ACTIVE - Ready for AI CLI integration
