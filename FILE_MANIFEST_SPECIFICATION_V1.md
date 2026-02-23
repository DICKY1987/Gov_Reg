# File Manifest System Specification v1.0

**Purpose**: Reusable file manifest generator for Gov_Reg repository with clear auto-derived vs curated field boundaries.

---

## Executive Summary

### Answers to Key Questions

**Q: Do you want the manifest to drive renames, or just record metadata?**  
**A:** Record metadata only. The `file_id` is stored in the manifest, not enforced in filenames. **Physical files keep their current names on disk.** Collision handling (suffix/skip) applies only to `file_id` values within the manifest, not filesystem renames.

**Q: Which fields are "must-have" vs "nice-to-have" for the first iteration?**  
**A:** 
- **Must-have (V1 - Enforced by schema)**: file_id, relative_path, filename, derivation_method, file_size_bytes, file_type, modified_timestamp
- **Recommended (V1 - Auto-derived but optional)**: sha256_hash, encoding, line_count, git_info
- **Nice-to-have (V2)**: dependencies, ACL permissions, supersedes/superseded_by

**Q: Are owner/creator and dependencies expected to come from Git, filesystem metadata, or manual annotations?**  
**A:**
- **owner**: Git last-commit author (fallback to curated field)
- **dependencies**: Manual annotation (V2: static analysis for Python imports)
- **creator**: Not tracked (Git history is source-of-truth)

**Q: Is this strictly for newPhasePlanProcess, or should it be reusable across the repo?**  
**A:** **Reusable** across entire Gov_Reg repository with configurable ignore patterns per directory.

---

## 1. Manifest Schema Definition

### 1.1 Source of Truth
- **Schema File**: `schemas/file_manifest_schema_v1.json` (JSON Schema Draft-07)
- **Validation**: Pydantic models + jsonschema validation
- **Versioning**: Semantic versioning in `manifest_metadata.schema_version`

### 1.2 Required Fields (V1 - Auto-Derived)

| Field | Type | Derivation | Notes |
|-------|------|------------|-------|
| `file_id` | string | **Hybrid** | Extract from filename prefix pattern `^(P_\d+\|\d{20})_` OR generate path-based SHA256 hash (first 16 chars) |
| `relative_path` | string | Auto | Path relative to scan root |
| `filename` | string | Auto | File name with extension |
| `file_size_bytes` | integer | Auto | From `os.stat().st_size` |
| `file_type` | string | Auto | MIME type via `mimetypes` + `python-magic` fallback |
| `modified_timestamp` | number | Auto | Unix epoch from `st_mtime` |
| `derivation_method` | enum | Manual | `auto`, `curated`, or `hybrid` |

### 1.3 Optional Fields (Auto-Derived, Best-Effort)

| Field | Type | Derivation | Reliability |
|-------|------|------------|-------------|
| `is_text` | boolean | Auto | Check extension + magic bytes |
| `sha256_hash` | string\|null | Auto | Full content hash; `null` if >100MB (configurable) |
| `encoding` | string | Auto | Use `chardet` for text files |
| `line_count` | integer | Auto | Text files only |
| `created_timestamp` | number | Auto | Windows: unreliable; Unix: better |
| `accessed_timestamp` | number | Auto | Often disabled on Windows (best-effort) |
| `git_info` | object | Auto | If `.git` found; gracefully skip otherwise |

### 1.4 Curated Fields (Recommended but Not Schema-Enforced)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `category` | enum | **Recommended** | `source`, `test`, `config`, `documentation`, `schema`, `script`, `data`, `evidence`, `other` |
| `status` | enum | **Recommended** | `active`, `deprecated`, `archived`, `draft`, `unknown` |
| `owner` | string | No | Git `last_commit_author` fallback or manual |
| `version` | string | No | Manual; not derived |
| `gate_id` | string | No | Manual; links to governance gate |
| `phase_id` | string | No | Manual; links to phase/milestone |
| `dependencies` | array | No | Manual; V2: static analysis |
| `supersedes` | string | No | Manual; file_id of replaced file |
| `superseded_by` | string | No | Manual; file_id of replacement |
| `tags` | array | No | Manual; searchable keywords |
| `description` | string | No | Manual; human-readable purpose |

### 1.5 Provenance Fields (Manifest-Level)

```json
{
  "manifest_metadata": {
    "schema_version": "1.0.0",
    "scan_timestamp": "2026-02-21T21:12:00.000Z",
    "scanner_version": "1.0.0",
    "root_path": "C:\\Users\\richg\\Gov_Reg",
    "scan_host": "DESKTOP-XYZ",
    "ignore_patterns": [".git", "__pycache__", "*.pyc"],
    "collision_handling": "suffix",
    "errors": [
      {
        "file_path": "broken_symlink.txt",
        "error_type": "FileNotFoundError",
        "error_message": "Symlink target does not exist"
      }
    ]
  }
}
```

---

## 2. File ID Generation Strategy

### 2.1 ID Extraction (Preferred)
```python
import re

def extract_file_id(filename: str) -> str | None:
    """Extract existing ID from Gov_Reg filename prefix."""
    pattern = r'^(P_\d+|\d{20})_'  # P_ + any digits, or exactly 20 digits
    match = re.match(pattern, filename)
    return match.group(1) if match else None
```

### 2.2 ID Generation (Fallback)
```python
import hashlib

def generate_file_id(relative_path: str) -> str:
    """Generate stable path-based ID."""
    normalized_path = relative_path.replace('\\', '/').lower()
    hash_hex = hashlib.sha256(normalized_path.encode()).hexdigest()
    return f"FID_{hash_hex[:16]}"  # FID_<16-char-hex>
```

### 2.3 Collision Handling
**Clarification**: "No renaming" means physical files keep their original names on disk. Collision handling applies only to `file_id` values in the manifest.

- **Error Mode (default)**: Raise exception and abort if duplicate `file_id` detected
- **Suffix Mode**: Append `_dup2`, `_dup3` suffix to duplicate `file_id` entries in manifest only
- **Skip Mode**: Log warning and skip duplicate files (omit from manifest)

---

## 3. Output Format & Location

### 3.1 Primary Output: JSON
```json
{
  "manifest_metadata": { /* ... */ },
  "files": {
    "P_01260207233100000252": {
      "file_id": "P_01260207233100000252",
      "relative_path": "newPhasePlanProcess/01260207201000001225_scripts/P_01260207233100000252_validate_file_manifest.py",
      "filename": "P_01260207233100000252_validate_file_manifest.py",
      "derivation_method": "auto",
      "file_size_bytes": 4532,
      "sha256_hash": "abc123...",
      "file_type": "text/x-python",
      "is_text": true,
      "encoding": "utf-8",
      "line_count": 142,
      "modified_timestamp": 1708546320.123,
      "git_info": {
        "last_commit_sha": "a1b2c3d",
        "last_commit_author": "user@example.com",
        "last_commit_date": "2026-02-20T10:30:00Z",
        "is_tracked": true,
        "is_modified": false
      },
      "category": "script",
      "status": "active"
    }
  }
}
```

### 3.2 Alternative Outputs
- **CSV**: Flattened structure for Excel analysis (via pandas)
- **YAML**: Human-editable format for curated fields
- **SQLite**: Queryable database for large manifests

### 3.3 Incremental Updates
- **Regenerate Mode (default)**: Fresh scan every time
- **Incremental Mode**: Load existing manifest → update changed files → preserve curated fields

---

## 4. Ignore Patterns & Scope

### 4.1 Default Ignore List
```yaml
ignore_patterns:
  - ".git"
  - "__pycache__"
  - "*.pyc"
  - ".pytest_cache"
  - ".mypy_cache"
  - "node_modules"
  - ".venv"
  - "*.egg-info"
  - "dist"
  - "build"
  - ".dir_id"
  - ".state"
  - "*.lock"
```

### 4.2 Symlink Handling
- **Skip Mode (default)**: Ignore symlinks
- **Follow Mode**: Treat as regular files (risk: infinite loops)
- **Record Mode**: Store symlink target in metadata

### 4.3 Error Reporting
All scan errors logged in `manifest_metadata.errors[]`:
```json
{
  "file_path": "inaccessible_file.dat",
  "error_type": "PermissionError",
  "error_message": "Access denied"
}
```

---

## 5. Performance Considerations

### 5.1 Hashing Optimization
- Skip hashing for files >100MB (configurable)
- Use chunked reading (8KB buffer) for memory efficiency
- Parallel processing with `concurrent.futures` (4 workers default)

### 5.2 Text File Detection
```python
TEXT_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.yaml', '.toml', '.sh', '.bat'}

def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    # Fallback: check first 512 bytes for null bytes
    try:
        with open(path, 'rb') as f:
            chunk = f.read(512)
            return b'\x00' not in chunk
    except:
        return False
```

### 5.3 Encoding Detection (Best-Effort)
```python
import chardet

def detect_encoding(path: Path) -> str | None:
    try:
        with open(path, 'rb') as f:
            raw = f.read(10000)  # Sample first 10KB
            result = chardet.detect(raw)
            return result['encoding'] if result['confidence'] > 0.7 else None
    except:
        return None
```

---

## 6. Windows-Specific Issues

### 6.1 Access Timestamp (Unreliable)
- **Issue**: `st_atime` often disabled for performance
- **Solution**: Mark as optional; set to `null` if unavailable

### 6.2 Permissions (ACL Complexity)
- **V1 Approach**: Skip ACL extraction (requires pywin32)
- **V2 Enhancement**: Optional ACL parsing via `icacls` subprocess
- **V1 Field**: Store basic `os.stat().st_mode` only

### 6.3 Long Paths (>260 chars)
```python
import sys
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.SetDllDirectoryW(None)
    # Enable long path support in Windows 10+
```

---

## 7. Git Integration

### 7.1 Repository Detection
```python
from git import Repo, InvalidGitRepositoryError

def get_git_info(file_path: Path) -> dict | None:
    try:
        repo = Repo(file_path, search_parent_directories=True)
        commits = list(repo.iter_commits(paths=file_path, max_count=1))
        if not commits:
            return None
        commit = commits[0]
        return {
            "last_commit_sha": commit.hexsha[:7],
            "last_commit_author": commit.author.email,
            "last_commit_date": commit.committed_datetime.isoformat(),
            "last_commit_message": commit.message.strip(),
            "is_tracked": str(file_path) not in repo.untracked_files,
            "is_modified": file_path.name in [item.a_path for item in repo.index.diff(None)]
        }
    except (InvalidGitRepositoryError, Exception):
        return None
```

### 7.2 Fallback Strategy
- If `.git` not found → skip `git_info` field entirely
- No Git dependency required → pure filesystem mode

---

## 8. Validation Strategy

### 8.1 Schema Validation (jsonschema)
```python
import jsonschema

def validate_manifest(manifest_data: dict) -> tuple[bool, list[str]]:
    schema = json.load(open('schemas/file_manifest_schema_v1.json'))
    try:
        jsonschema.validate(instance=manifest_data, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [str(e)]
```

### 8.2 Pydantic Models (Runtime Validation)
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class ManifestMetadata(BaseModel):
    schema_version: Literal["1.0.0"]
    scan_timestamp: datetime
    scanner_version: str
    root_path: str
    scan_host: str
    ignore_patterns: list[str] = []
    errors: list[dict] = []

class FileEntry(BaseModel):
    file_id: str = Field(pattern=r'^[0-9A-Za-z_-]+$')
    relative_path: str
    filename: str
    derivation_method: Literal["auto", "curated", "hybrid"]
    file_size_bytes: int
    sha256_hash: Optional[str] = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    file_type: str
    # ... (all other fields)
```

---

## 9. Tool Architecture

### 9.1 Command-Line Interface (Typer)
```bash
# Basic scan
manifest-gen scan /path/to/Gov_Reg

# Custom config
manifest-gen scan /path/to/Gov_Reg --config custom_config.yaml

# Incremental update
manifest-gen update /path/to/Gov_Reg --manifest existing_manifest.json

# Validate existing manifest
manifest-gen validate manifest.json

# Export to CSV
manifest-gen export manifest.json --format csv --output manifest.csv
```

### 9.2 Module Structure
```
src/govreg_manifest/
├── __init__.py
├── cli.py              # Typer CLI entry point
├── scanner.py          # Main scanning logic
├── models.py           # Pydantic models
├── file_id.py          # ID generation/extraction
├── analyzers/
│   ├── file_analyzer.py   # Hash, size, type detection
│   ├── git_analyzer.py    # Git integration
│   └── text_analyzer.py   # Encoding, line count
├── exporters/
│   ├── json_exporter.py
│   ├── csv_exporter.py
│   └── yaml_exporter.py
└── validators/
    ├── schema_validator.py
    └── integrity_validator.py
```

---

## 10. Implementation Phases

### Phase 1 (MVP - Week 1)
- ✅ JSON schema definition
- ✅ Config file structure
- ✅ Basic scanner (auto-derived fields only)
- ✅ File ID extraction/generation
- ✅ JSON output
- ✅ Validation (jsonschema)

### Phase 2 (Enhancement - Week 2)
- Git integration (GitPython)
- Text file analysis (encoding, line count)
- CSV/YAML export
- Incremental update mode
- Parallel processing

### Phase 3 (Polish - Week 3)
- Rich CLI output (progress bars, tables)
- Error recovery & logging
- Dependency analysis (Python imports)
- Documentation & examples
- Unit tests (pytest)

### Phase 4 (Future)
- ACL permissions (Windows)
- Multi-language static analysis (tree-sitter)
- Web UI for manifest browsing
- Integration with Gov_Reg gates

---

## 11. Usage Examples

### Example 1: Scan newPhasePlanProcess
```bash
manifest-gen scan C:\Users\richg\Gov_Reg\newPhasePlanProcess \
  --output npp_manifest.json \
  --config schemas/file_manifest_config.yaml
```

### Example 2: Repo-Wide Scan
```bash
manifest-gen scan C:\Users\richg\Gov_Reg \
  --output gov_reg_manifest.json \
  --exclude "EVIDENCE_BUNDLE" "01260207201000001133_backups"
```

### Example 3: Incremental Update
```bash
manifest-gen update C:\Users\richg\Gov_Reg \
  --manifest gov_reg_manifest.json \
  --preserve-curated
```

---

## 12. Design Decisions (Resolved)

All design decisions have been finalized for MVP implementation:

1. **File ID Prefix**: ✅ Accept both `P_<digits>_` and `<20digits>_` patterns (extract as-is from existing files; generate path-based hash for files without prefixes)
   - Rationale: Preserves backward compatibility with existing Gov_Reg file naming conventions
   - No file renaming required on disk

2. **Curated Field Management**: ✅ Direct JSON editing with schema validation (MVP)
   - Users edit manifest JSON directly using any text editor
   - Generator supports `incremental_update: true` to preserve curated fields on re-scan
   - Advanced tooling (YAML overlay, curation CLI) deferred to Phase 2

3. **Dependency Analysis**: ✅ Manual annotation only (MVP)
   - `dependencies` field is curated-only; no auto-population in Phase 1
   - Auto-parsing via AST analysis deferred to Phase 2
   - Explicit manual annotation ensures accuracy

4. **Manifest Location**: ✅ Single repo-wide manifest at `file_manifest.json`
   - Single Source of Truth principle (no sync issues)
   - Simpler queries and version control
   - Per-directory manifests with rollup deferred to Phase 3 (if repo scales >10k files)

5. **Validator Integration**: ✅ Extend existing `validate_file_manifest.py`
   - New package provides validation library
   - Existing script updated to use new package under the hood
   - Preserves backward compatibility with existing workflows/CI
   - Gradual deprecation path: script becomes thin wrapper to `manifest-gen validate`

**Decision Authority**: Approved 2026-02-22  
**Full Rationale**: See `A11_DESIGN_DECISIONS_RESOLVED.md`

---

## Appendices

### A. Example Manifest Output
See: `examples/sample_manifest.json`

### B. Configuration Reference
See: `schemas/file_manifest_config.yaml`

### C. API Reference
See: `docs/api_reference.md` (TBD)

---

**Status**: ✅ Specification Complete - All Design Decisions Resolved  
**Last Updated**: 2026-02-22  
**Next Step**: Begin Phase 1 MVP Implementation (`GOVREG_MANIFEST_IMPLEMENTATION_PLAN_V1.json`)
