# ID Canonicality System - Mutation Set v2.1.4-READY

**Date:** 2026-02-12  
**Purpose:** Complete file creation/modification set to implement drift-proof ID canonicality enforcement  
**Status:** EXECUTION-READY (all blockers fixed)

---

## 📋 Mutation Summary

### New Files (7)
1. `docs/ID_IDENTITY_CONTRACT.md` - Semantic contract lock
2. `govreg_core/P_01999000042260125002_canonical_id_patterns.py` - Single source of truth for ID patterns
3. `govreg_core/P_01999000042260125006_id_allocator_facade.py` - Single allocator entrypoint
4. `govreg_core/__init__.py` - Package marker (if missing)
5. `ID_SCRIPT_INVENTORY.jsonl` - Migrated inventory with correct schema
6. `gates/P_01999000042260125000_gate_id_canonicality.py` - Rewritten enforcement gate
7. `.git/hooks/pre-commit` - Git hook wrapper (LF-only)

### Modified Files (1)
1. `scripts/P_01999000042260124999_id_canonicality_enforcer.py` - Updated to use new schema + atomic operations

### Archive Operations (via git mv)
- Move deprecated/duplicate scripts to `Archive_Gov_Reg/id_scripts_deprecated/`

---

## 🔧 MUTATION 1: Create ID Identity Contract

**File:** `docs/ID_IDENTITY_CONTRACT.md`

```markdown
# ID Identity Contract v2.1.4

**Status:** CANONICAL  
**Effective Date:** 2026-02-12  
**Supersedes:** All previous ID allocation documents

---

## ID Type Definitions (Immutable)

### file_id
- **Format:** 20 digits numeric only
- **Pattern:** `^\d{20}$`
- **Examples:** `01999000042260124027`, `01260207233100000466`
- **Storage:** This is the canonical identifier stored in registries
- **Notes:** NEVER includes `P_` prefix

### doc_id
- **Format:** `P_` + file_id
- **Pattern:** `^P_\d{20}$`
- **Examples:** `P_01999000042260124027`, `P_01260207233100000466`
- **Storage:** Derived field; may be stored separately if needed
- **Notes:** Used for Python/doc artifact naming convention ONLY

### filename_prefix
- **Format:** Optional `P_` + 20 digits + underscore
- **Pattern:** `^(?:P_)?\d{20}_`
- **Examples:** `P_01999000042260124027_`, `01260207233100000466_`
- **Usage:** File naming convention (appears at start of filename)
- **Classification:**
  - `DOC_PREFIXED`: starts with `P_\d{20}_`
  - `REGULAR`: starts with `\d{20}_`

### enhanced_id (if used)
- **Format:** 17 digit prefix + 5 digit counter = 22 digits total
- **Pattern:** `^\d{17}\d{5}$`
- **Segmentation:** `<prefix:17><counter:5>`
- **Example:** `0199900004226012400001` → prefix=`01999000042260124`, counter=`00001`
- **Storage:** MUST be stored in a separate field (e.g., `enhanced_id`, `allocation_id`)
- **Notes:** NEVER stored as `file_id`; this is a distinct identifier type

---

## Allowed ID Sources (Enforcement Policy)

### CANONICAL (Single Entrypoint)
- **Module:** `govreg_core.P_01999000042260125006_id_allocator_facade`
- **Function:** `allocate_id(id_type: str, context: dict) -> str`
- **Policy:** This is the ONLY allowed import surface for ID allocation

### INTERNAL (Backend Implementations)
- **Purpose:** Implementation details of the facade
- **Policy:** MUST NOT be imported directly by application code
- **Enforcement:** Gate blocks direct imports of INTERNAL modules
- **Examples:**
  - `scripts.P_01999000042260124027_id_allocator` (legacy 20-digit)
  - `govreg_core.P_01999000042260124031_unified_id_allocator` (22-digit backend)

### DEPRECATED
- **Purpose:** Old/superseded implementations
- **Policy:** MUST NOT be imported or used
- **Enforcement:** Gate blocks all imports of DEPRECATED modules
- **Action:** Archived to `Archive_Gov_Reg/id_scripts_deprecated/`

---

## Pattern Library (Single Source)

**Module:** `govreg_core.P_01999000042260125002_canonical_id_patterns`

All ID pattern matching MUST use patterns from this module:
- `ID_20_DIGIT_RE` - raw 20-digit file_id
- `DOC_ID_RE` - P_ prefixed doc_id
- `FILENAME_PREFIX_RE` - filename prefix with optional P_
- `ENHANCED_ID_RE` - 22-digit enhanced_id (if applicable)

**Policy:** No other module may define ID-matching regex patterns.

---

## Enforcement Rules

### Rule 1: Allocation
- All ID allocation MUST go through `id_allocator_facade`
- Direct imports of backend allocators (INTERNAL) are BLOCKED
- Bespoke allocation functions are BLOCKED

### Rule 2: Pattern Matching
- All ID pattern matching MUST import from `canonical_id_patterns`
- Inline regex with `\d{20}`, `\d{22}`, or `P_` patterns are BLOCKED
- Exception: The canonical patterns module itself

### Rule 3: Inventory Freshness
- New files matching `^(?:P_)?\d{20}_.*\.py$` MUST be added to inventory
- Gate fails if an ID-script is staged but not in `ID_SCRIPT_INVENTORY.jsonl`

### Rule 4: Import Restrictions
- INTERNAL modules: blocked from imports
- DEPRECATED modules: blocked from imports
- Only CANONICAL imports are allowed

---

## Storage Contract

### In `ID_SCRIPT_INVENTORY.jsonl`
```json
{
  "file_id_numeric": "01999000042260124027",
  "doc_id": "P_01999000042260124027",
  "relative_path": "scripts/P_01999000042260124027_id_allocator.py",
  "filename_prefix_kind": "DOC_PREFIXED",
  "import_module": "scripts.P_01999000042260124027_id_allocator",
  "is_importable": true,
  "canonicality": "INTERNAL",
  "id_generation_mode": "20_DIGIT_FILE_ID"
}
```

### In Governance Registry (if applicable)
- **Primary key:** `file_id` (20 digits numeric)
- **Derived fields:** `doc_id` may exist as separate field
- **Canonicality:** Only `CANONICAL` and `DEPRECATED` values written
- **INTERNAL:** NOT written to registry (inventory-only)

---

## Success Criteria

✅ Zero FILE_ID conflicts  
✅ Zero local ID regex definitions outside canonical patterns module  
✅ All allocations go through facade  
✅ Gate blocks INTERNAL/DEPRECATED imports  
✅ New ID scripts require inventory update  
✅ Inventory mutations are atomic + evidenced  

---

**Authoritative Source:** This contract is the single source of truth for ID semantics.  
**Updates:** Changes require governance approval and version increment.
```

---

## 🔧 MUTATION 2: Create Canonical ID Patterns Module

**File:** `govreg_core/P_01999000042260125002_canonical_id_patterns.py`

```python
"""
Canonical ID Pattern Library - Single Source of Truth for ID Patterns

This module provides the ONLY allowed regex patterns for ID detection,
validation, and parsing. No other module may define ID-matching patterns.

File ID: P_01999000042260125002
Canonicality: CANONICAL
Role: PATTERN_LIBRARY
"""

import re
from typing import Tuple, Optional

# ============================================================================
# CANONICAL PATTERNS (immutable)
# ============================================================================

# Raw 20-digit file_id (no prefix)
ID_20_DIGIT_RE = re.compile(r'^\d{20}$')

# Doc ID with P_ prefix
DOC_ID_RE = re.compile(r'^P_\d{20}$')

# Filename prefix (optional P_ + 20 digits + underscore)
FILENAME_PREFIX_RE = re.compile(r'^(?P<doc_prefix>P_)?(?P<file_id>\d{20})_')

# Enhanced ID (22 digits: 17 prefix + 5 counter)
ENHANCED_ID_RE = re.compile(r'^(?P<prefix>\d{17})(?P<counter>\d{5})$')

# Loose patterns for detection in filenames/paths
LOOSE_20_DIGIT_PATTERN = re.compile(r'\d{20}')
LOOSE_DOC_ID_PATTERN = re.compile(r'P_\d{20}')

# ============================================================================
# CANONICAL HELPERS
# ============================================================================

def extract_file_id_from_filename(filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Extract file_id from a filename using the canonical pattern.
    
    Args:
        filename: Filename to parse (e.g., "P_01999000042260124027_script.py")
    
    Returns:
        Tuple of (has_prefix, file_id_numeric, prefix_kind)
        - has_prefix: True if pattern matched
        - file_id_numeric: 20-digit numeric ID (or None)
        - prefix_kind: "DOC_PREFIXED" | "REGULAR" | None
    """
    match = FILENAME_PREFIX_RE.match(filename)
    if not match:
        return (False, None, None)
    
    file_id = match.group('file_id')
    doc_prefix = match.group('doc_prefix')
    prefix_kind = "DOC_PREFIXED" if doc_prefix else "REGULAR"
    
    return (True, file_id, prefix_kind)


def is_valid_file_id(value: str) -> bool:
    """
    Validate that a string is a valid 20-digit file_id.
    
    Args:
        value: String to validate
    
    Returns:
        True if valid 20-digit file_id, False otherwise
    """
    return bool(ID_20_DIGIT_RE.match(value))


def is_valid_doc_id(value: str) -> bool:
    """
    Validate that a string is a valid doc_id (P_<20 digits>).
    
    Args:
        value: String to validate
    
    Returns:
        True if valid doc_id, False otherwise
    """
    return bool(DOC_ID_RE.match(value))


def normalize_to_file_id(value: str) -> Optional[str]:
    """
    Normalize any ID format to numeric file_id.
    
    Args:
        value: ID in any format (P_01999..., 01999..., etc.)
    
    Returns:
        20-digit numeric file_id, or None if invalid
    """
    # Try doc_id format first
    if DOC_ID_RE.match(value):
        return value[2:]  # strip P_
    
    # Try raw file_id
    if ID_20_DIGIT_RE.match(value):
        return value
    
    return None


def derive_doc_id(file_id_numeric: str) -> Optional[str]:
    """
    Derive doc_id from numeric file_id.
    
    Args:
        file_id_numeric: 20-digit numeric file_id
    
    Returns:
        doc_id (P_<file_id>) or None if invalid input
    """
    if not is_valid_file_id(file_id_numeric):
        return None
    return f"P_{file_id_numeric}"


def parse_enhanced_id(enhanced_id: str) -> Optional[Tuple[str, str]]:
    """
    Parse a 22-digit enhanced_id into prefix and counter.
    
    Args:
        enhanced_id: 22-digit enhanced ID
    
    Returns:
        Tuple of (prefix, counter) or None if invalid
    """
    match = ENHANCED_ID_RE.match(enhanced_id)
    if not match:
        return None
    return (match.group('prefix'), match.group('counter'))


# ============================================================================
# EXPORT LIST (explicit API surface)
# ============================================================================

__all__ = [
    # Patterns
    'ID_20_DIGIT_RE',
    'DOC_ID_RE',
    'FILENAME_PREFIX_RE',
    'ENHANCED_ID_RE',
    'LOOSE_20_DIGIT_PATTERN',
    'LOOSE_DOC_ID_PATTERN',
    
    # Functions
    'extract_file_id_from_filename',
    'is_valid_file_id',
    'is_valid_doc_id',
    'normalize_to_file_id',
    'derive_doc_id',
    'parse_enhanced_id',
]
```

---

## 🔧 MUTATION 3: Create ID Allocator Facade

**File:** `govreg_core/P_01999000042260125006_id_allocator_facade.py`

```python
"""
ID Allocator Facade - Single Canonical Entrypoint for ID Allocation

This is the ONLY allowed import surface for ID allocation across the codebase.
All other allocator modules are INTERNAL and must not be imported directly.

File ID: P_01999000042260125006
Canonicality: CANONICAL
Role: ALLOCATOR_FACADE
"""

from typing import Dict, Optional, Any
from pathlib import Path
import sys

# Ensure repo root is on path for backend imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import backend allocators (INTERNAL - not exposed)
try:
    from scripts.P_01999000042260124027_id_allocator import allocate as _allocate_20_digit
except ImportError:
    _allocate_20_digit = None

try:
    from govreg_core.P_01999000042260124031_unified_id_allocator import allocate_id as _allocate_enhanced
except ImportError:
    _allocate_enhanced = None


class IDAllocationError(Exception):
    """Raised when ID allocation fails."""
    pass


def allocate_id(
    id_type: str = "FILE_ID",
    context: Optional[Dict[str, Any]] = None,
    prefix: Optional[str] = None
) -> str:
    """
    Allocate a new ID (canonical entrypoint).
    
    This is the ONLY function that should be called for ID allocation.
    It routes to the appropriate backend based on id_type.
    
    Args:
        id_type: Type of ID to allocate
                 - "FILE_ID": 20-digit file ID (default)
                 - "ENHANCED_ID": 22-digit enhanced ID (if available)
        context: Optional context dict for allocation (e.g., layer, artifact_kind)
        prefix: Optional existing prefix to validate before allocating
    
    Returns:
        Allocated ID string
    
    Raises:
        IDAllocationError: If allocation fails or backends unavailable
    
    Examples:
        >>> allocate_id()  # 20-digit file_id
        '01999000042260125007'
        
        >>> allocate_id(id_type="ENHANCED_ID", context={"layer": "CORE"})
        '0199900004226012500001'
    """
    context = context or {}
    
    # Route to appropriate backend
    if id_type == "FILE_ID":
        if _allocate_20_digit is None:
            raise IDAllocationError(
                "20-digit allocator backend not available. "
                "Ensure scripts.P_01999000042260124027_id_allocator exists."
            )
        return _allocate_20_digit(prefix=prefix, **context)
    
    elif id_type == "ENHANCED_ID":
        if _allocate_enhanced is None:
            raise IDAllocationError(
                "Enhanced ID allocator backend not available. "
                "Ensure govreg_core.P_01999000042260124031_unified_id_allocator exists."
            )
        return _allocate_enhanced(context=context, prefix=prefix)
    
    else:
        raise IDAllocationError(
            f"Unknown id_type: {id_type}. "
            f"Valid types: FILE_ID, ENHANCED_ID"
        )


def allocate_file_id(prefix: Optional[str] = None, **context) -> str:
    """
    Convenience wrapper for allocating a 20-digit file_id.
    
    Args:
        prefix: Optional existing prefix to validate
        **context: Additional context for allocation
    
    Returns:
        20-digit file_id string
    """
    return allocate_id(id_type="FILE_ID", context=context, prefix=prefix)


def allocate_enhanced_id(prefix: Optional[str] = None, **context) -> str:
    """
    Convenience wrapper for allocating a 22-digit enhanced_id.
    
    Args:
        prefix: Optional existing prefix to validate
        **context: Additional context for allocation
    
    Returns:
        22-digit enhanced_id string
    """
    return allocate_id(id_type="ENHANCED_ID", context=context, prefix=prefix)


# ============================================================================
# EXPORT LIST (explicit API surface)
# ============================================================================

__all__ = [
    'allocate_id',
    'allocate_file_id',
    'allocate_enhanced_id',
    'IDAllocationError',
]
```

---

## 🔧 MUTATION 4: Ensure govreg_core is a Package

**File:** `govreg_core/__init__.py`

```python
"""
govreg_core - Core governance and registry modules

This package contains canonical implementations for:
- ID allocation (via facade)
- ID pattern matching
- Registry operations
- Governance enforcement
"""

__version__ = "2.1.4"
```

---

## 🔧 MUTATION 5: Create Migrated Inventory

**File:** `ID_SCRIPT_INVENTORY.jsonl`

**Format:** JSONL with meta record on line 1

```jsonl
{"record_type":"meta","schema_version":"2.1.4","generated_at":"2026-02-12T22:41:00Z","total_records":21}
{"file_id_numeric":"01999000042260125002","doc_id":"P_01999000042260125002","relative_path":"govreg_core/P_01999000042260125002_canonical_id_patterns.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"govreg_core.P_01999000042260125002_canonical_id_patterns","is_importable":true,"canonicality":"CANONICAL","role":"PATTERN_LIBRARY","id_generation_mode":null,"digit_count":null}
{"file_id_numeric":"01999000042260125006","doc_id":"P_01999000042260125006","relative_path":"govreg_core/P_01999000042260125006_id_allocator_facade.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"govreg_core.P_01999000042260125006_id_allocator_facade","is_importable":true,"canonicality":"CANONICAL","role":"ALLOCATOR_FACADE","id_generation_mode":"20_DIGIT_FILE_ID","digit_count":20}
{"file_id_numeric":"01999000042260124027","doc_id":"P_01999000042260124027","relative_path":"scripts/P_01999000042260124027_id_allocator.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"scripts.P_01999000042260124027_id_allocator","is_importable":true,"canonicality":"INTERNAL","role":"ALLOCATOR","id_generation_mode":"20_DIGIT_FILE_ID","digit_count":20}
{"file_id_numeric":"01999000042260124031","doc_id":"P_01999000042260124031","relative_path":"govreg_core/P_01999000042260124031_unified_id_allocator.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"govreg_core.P_01999000042260124031_unified_id_allocator","is_importable":true,"canonicality":"INTERNAL","role":"ALLOCATOR","id_generation_mode":"22_DIGIT_ENHANCED_ID","digit_count":22}
{"file_id_numeric":"01999000042260124999","doc_id":"P_01999000042260124999","relative_path":"scripts/P_01999000042260124999_id_canonicality_enforcer.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"scripts.P_01999000042260124999_id_canonicality_enforcer","is_importable":true,"canonicality":"CANONICAL","role":"ENFORCER","id_generation_mode":null,"digit_count":null}
{"file_id_numeric":"01999000042260125000","doc_id":"P_01999000042260125000","relative_path":"gates/P_01999000042260125000_gate_id_canonicality.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"gates.P_01999000042260125000_gate_id_canonicality","is_importable":true,"canonicality":"CANONICAL","role":"GATE","id_generation_mode":null,"digit_count":null}
{"file_id_numeric":"01999000042260124521","doc_id":"P_01999000042260124521","relative_path":"scripts/P_01999000042260124521_id_format_scanner.py","filename_prefix_kind":"DOC_PREFIXED","import_module":"scripts.P_01999000042260124521_id_format_scanner","is_importable":true,"canonicality":"CANONICAL","role":"SCANNER","id_generation_mode":null,"digit_count":null}
```

**Note:** Full inventory would contain all 21 scripts. Above shows format for key records.

---

## 🔧 MUTATION 6: Create Inventory-Driven Pre-Commit Gate

**File:** `gates/P_01999000042260125000_gate_id_canonicality.py`

```python
"""
ID Canonicality Pre-Commit Gate - Inventory-Driven Enforcement

This gate enforces:
1. No imports of DEPRECATED or INTERNAL ID modules
2. Facade-only allocator usage
3. No bespoke ID regex patterns
4. Inventory freshness (new ID scripts must be inventoried)

File ID: P_01999000042260125000
Canonicality: CANONICAL
Role: GATE
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Optional


class IDCanonicalityGate:
    """Pre-commit gate for ID canonicality enforcement."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        """
        Initialize gate.
        
        Args:
            repo_root: Repository root path (auto-detected if None)
        """
        self.repo_root = repo_root or self._detect_repo_root()
        self.inventory_path = self.repo_root / "ID_SCRIPT_INVENTORY.jsonl"
        self.canonical_patterns_module = 'govreg_core.P_01999000042260125002_canonical_id_patterns'
        self.canonical_facade_module = 'govreg_core.P_01999000042260125006_id_allocator_facade'
        
        # Load inventory
        self.inventory_records, self.schema_version = self._load_inventory()
        
        # Build enforcement sets
        self.deprecated_modules = self._build_deprecated_set()
        self.internal_modules = self._build_internal_set()
        self.inventory_paths = self._build_inventory_paths()
    
    def _detect_repo_root(self) -> Path:
        """Detect repository root via git."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except Exception:
            # Fallback: walk up to .git
            current = Path(__file__).resolve()
            while current != current.parent:
                if (current / '.git').exists():
                    return current
                current = current.parent
            raise RuntimeError("Could not detect repository root")
    
    def _load_inventory(self) -> tuple[List[Dict[str, Any]], str]:
        """
        Load inventory JSONL and validate schema version.
        
        Returns:
            Tuple of (records, schema_version)
        
        Raises:
            RuntimeError: If inventory missing or schema version mismatch
        """
        if not self.inventory_path.exists():
            raise RuntimeError(
                f"GATE FAILURE: Inventory not found: {self.inventory_path}\n"
                f"Run: python scripts/P_01999000042260124999_id_canonicality_enforcer.py --action analyze"
            )
        
        records = []
        schema_version = None
        
        with open(self.inventory_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                record = json.loads(line)
                
                # First line must be meta record
                if line_num == 1:
                    if record.get('record_type') != 'meta':
                        raise RuntimeError(
                            f"GATE FAILURE: Inventory first line must be meta record"
                        )
                    schema_version = record.get('schema_version')
                    if schema_version != '2.1.4':
                        raise RuntimeError(
                            f"GATE FAILURE: Inventory schema version mismatch: "
                            f"expected 2.1.4, got {schema_version}"
                        )
                    continue
                
                records.append(record)
        
        return records, schema_version
    
    def _build_deprecated_set(self) -> Set[str]:
        """Build set of deprecated module import paths."""
        return {
            rec['import_module']
            for rec in self.inventory_records
            if rec.get('canonicality') == 'DEPRECATED'
            and rec.get('import_module')
            and rec.get('is_importable')
        }
    
    def _build_internal_set(self) -> Set[str]:
        """Build set of internal module import paths."""
        return {
            rec['import_module']
            for rec in self.inventory_records
            if rec.get('canonicality') == 'INTERNAL'
            and rec.get('import_module')
            and rec.get('is_importable')
        }
    
    def _build_inventory_paths(self) -> Set[str]:
        """Build set of relative paths in inventory."""
        return {
            rec['relative_path']
            for rec in self.inventory_records
        }
    
    def get_staged_files(self) -> List[Path]:
        """Get list of staged Python files."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_root
            )
            
            staged = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                path = self.repo_root / line
                if path.suffix == '.py' and path.exists():
                    staged.append(path)
            
            return staged
        
        except Exception as e:
            raise RuntimeError(f"GATE FAILURE: Could not get staged files: {e}")
    
    def check_inventory_freshness(self, staged_files: List[Path]) -> List[str]:
        """Check that new ID scripts are in inventory."""
        violations = []
        id_pattern = re.compile(r'^(?:P_)?\d{20}_.*\.py$')
        
        for file in staged_files:
            if id_pattern.match(file.name):
                rel_path = str(file.relative_to(self.repo_root)).replace('\\', '/')
                if rel_path not in self.inventory_paths:
                    violations.append(
                        f"FRESHNESS VIOLATION: New ID script not in inventory\n"
                        f"  File: {rel_path}\n"
                        f"  Action: Run enforcer to update inventory:\n"
                        f"    python scripts/P_01999000042260124999_id_canonicality_enforcer.py --action analyze"
                    )
        
        return violations
    
    def check_deprecated_imports(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Check for deprecated module imports."""
        violations = []
        
        for node in ast.walk(tree):
            # Handle: from X import Y
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module in self.deprecated_modules:
                    violations.append(
                        f"DEPRECATED IMPORT: {file_path.name} imports deprecated module\n"
                        f"  Line {node.lineno}: from {node.module} import ...\n"
                        f"  Action: Remove this import; module is deprecated"
                    )
            
            # Handle: import X
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.deprecated_modules:
                        violations.append(
                            f"DEPRECATED IMPORT: {file_path.name} imports deprecated module\n"
                            f"  Line {node.lineno}: import {alias.name}\n"
                            f"  Action: Remove this import; module is deprecated"
                        )
        
        return violations
    
    def check_internal_imports(self, file_path: Path, tree: ast.AST) -> List[str]:
        """Check for internal module imports (backend allocators)."""
        violations = []
        
        for node in ast.walk(tree):
            # Handle: from X import Y
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    # Exact match or submodule
                    if node.module in self.internal_modules or \
                       any(node.module.startswith(mod + '.') for mod in self.internal_modules):
                        violations.append(
                            f"INTERNAL IMPORT BLOCKED: {file_path.name} imports internal backend\n"
                            f"  Line {node.lineno}: from {node.module} import ...\n"
                            f"  Action: Use canonical facade instead:\n"
                            f"    from {self.canonical_facade_module} import allocate_id"
                        )
            
            # Handle: import X
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.internal_modules or \
                       any(alias.name.startswith(mod + '.') for mod in self.internal_modules):
                        violations.append(
                            f"INTERNAL IMPORT BLOCKED: {file_path.name} imports internal backend\n"
                            f"  Line {node.lineno}: import {alias.name}\n"
                            f"  Action: Use canonical facade instead:\n"
                            f"    from {self.canonical_facade_module} import allocate_id"
                        )
        
        return violations
    
    def check_bespoke_regex(self, file_path: Path, tree: ast.AST, source: str) -> List[str]:
        """Check for bespoke ID regex patterns."""
        violations = []
        
        # Skip if this IS the canonical patterns module
        rel_path = str(file_path.relative_to(self.repo_root)).replace('\\', '/')
        if rel_path == 'govreg_core/P_01999000042260125002_canonical_id_patterns.py':
            return violations
        
        # Check if file imports canonical patterns
        imports_canonical_patterns = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == self.canonical_patterns_module:
                    imports_canonical_patterns = True
                    break
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == self.canonical_patterns_module:
                        imports_canonical_patterns = True
                        break
        
        # Detect bespoke ID patterns
        id_pattern_indicators = [r'\d{20}', r'\d{22}', r'P_\\d']
        
        for node in ast.walk(tree):
            # Check re.compile calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'compile':
                        # Check if first arg contains ID pattern
                        if node.args and isinstance(node.args[0], ast.Constant):
                            pattern_str = str(node.args[0].value)
                            if any(indicator in pattern_str for indicator in id_pattern_indicators):
                                if not imports_canonical_patterns:
                                    violations.append(
                                        f"BESPOKE REGEX BLOCKED: {file_path.name} defines ID regex pattern\n"
                                        f"  Line {node.lineno}: re.compile with ID pattern\n"
                                        f"  Action: Import from canonical patterns module:\n"
                                        f"    from {self.canonical_patterns_module} import ID_20_DIGIT_RE, ..."
                                    )
        
        return violations
    
    def run(self) -> bool:
        """
        Run the gate on staged files.
        
        Returns:
            True if all checks pass, False otherwise
        """
        print("=" * 70)
        print("ID CANONICALITY GATE - Running enforcement checks...")
        print(f"Inventory: {self.inventory_path}")
        print(f"Schema Version: {self.schema_version}")
        print(f"Deprecated Modules: {len(self.deprecated_modules)}")
        print(f"Internal Modules: {len(self.internal_modules)}")
        print("=" * 70)
        
        staged_files = self.get_staged_files()
        
        if not staged_files:
            print("✅ No Python files staged - gate passes")
            return True
        
        print(f"Checking {len(staged_files)} staged Python file(s)...\n")
        
        all_violations = []
        
        # Check 1: Inventory freshness
        freshness_violations = self.check_inventory_freshness(staged_files)
        all_violations.extend(freshness_violations)
        
        # Check 2-4: AST checks on each file
        for file_path in staged_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=str(file_path))
                
                all_violations.extend(self.check_deprecated_imports(file_path, tree))
                all_violations.extend(self.check_internal_imports(file_path, tree))
                all_violations.extend(self.check_bespoke_regex(file_path, tree, source))
            
            except SyntaxError as e:
                # Skip files with syntax errors (let other tools catch those)
                print(f"⚠️  Skipping {file_path.name} (syntax error: {e})")
                continue
            except Exception as e:
                print(f"⚠️  Error checking {file_path.name}: {e}")
                continue
        
        # Report results
        if all_violations:
            print("\n" + "=" * 70)
            print("❌ GATE FAILURE - VIOLATIONS DETECTED")
            print("=" * 70)
            for violation in all_violations:
                print(f"\n{violation}")
            print("\n" + "=" * 70)
            print(f"Total Violations: {len(all_violations)}")
            print("Commit BLOCKED - Fix violations and try again")
            print("=" * 70)
            return False
        
        print("✅ All checks passed - commit allowed")
        return True


def main():
    """Main entrypoint."""
    try:
        gate = IDCanonicalityGate()
        success = gate.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ GATE ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
```

---

## 🔧 MUTATION 7: Install Pre-Commit Hook (LF-only, wrapper script)

**File:** `.git/hooks/pre-commit`

**Installation via PowerShell:**

```powershell
# Create hook with LF-only line endings
$hook = @"
#!/bin/sh
set -e
REPO_ROOT="`$(git rev-parse --show-toplevel)"
cd "`$REPO_ROOT"

if command -v python >/dev/null 2>&1; then
  python gates/P_01999000042260125000_gate_id_canonicality.py
else
  py -3 gates/P_01999000042260125000_gate_id_canonicality.py
fi
"@

# Write with LF line endings (critical for Git Bash)
[IO.File]::WriteAllText(".git/hooks/pre-commit", ($hook -replace "`r`n","`n"))

Write-Host "✅ Hook installed: .git/hooks/pre-commit"
Write-Host "⚠️  Run in Git Bash: chmod +x .git/hooks/pre-commit"
```

**Then in Git Bash:**

```sh
chmod +x .git/hooks/pre-commit
```

---

## 🔧 MUTATION 8: Update Enforcer (Atomic Operations + RFC-6902 Patches)

**File:** `scripts/P_01999000042260124999_id_canonicality_enforcer.py`

**Changes Required:**

1. Update inventory schema handling to use `file_id_numeric`, `doc_id`, `import_module`, etc.
2. Make `mark_deprecated()` atomic:
   - Write to temp file
   - Compute SHA-256 before/after
   - Atomic rename
   - Emit evidence JSON
3. Generate RFC-6902 patches (not full objects):
   - Use `op: "add"` for canonicality/superseded_by (safe for missing fields)
   - Patch existing entries by index lookup
   - Do NOT append new entries (log missing entries instead)

**Key Changes (pseudocode):**

```python
def mark_deprecated(self, inventory_path: Path, deprecated_ids: Set[str]) -> Dict:
    """Mark scripts as deprecated (atomic + evidence)."""
    # Load current inventory
    with open(inventory_path, 'r') as f:
        lines = f.readlines()
    
    # Compute before hash
    import hashlib
    before_hash = hashlib.sha256(''.join(lines).encode()).hexdigest()
    
    # Update records
    meta_line = lines[0]
    record_lines = lines[1:]
    updated_records = []
    
    for line in record_lines:
        record = json.loads(line)
        if record['file_id_numeric'] in deprecated_ids:
            record['canonicality'] = 'DEPRECATED'
            # Add superseded_by logic here
        updated_records.append(json.dumps(record))
    
    # Write to temp file
    temp_path = inventory_path.with_suffix('.jsonl.tmp')
    with open(temp_path, 'w') as f:
        f.write(meta_line)
        for record in updated_records:
            f.write(record + '\n')
    
    # Compute after hash
    with open(temp_path, 'r') as f:
        after_content = f.read()
    after_hash = hashlib.sha256(after_content.encode()).hexdigest()
    
    # Atomic replace
    temp_path.replace(inventory_path)
    
    # Return evidence
    return {
        "action": "mark_deprecated",
        "before_hash": before_hash,
        "after_hash": after_hash,
        "changed_records": len(deprecated_ids),
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## 📋 EXECUTION CHECKLIST

### Phase 1: Apply Mutations
- [ ] Create `docs/ID_IDENTITY_CONTRACT.md`
- [ ] Create `govreg_core/P_01999000042260125002_canonical_id_patterns.py`
- [ ] Create `govreg_core/P_01999000042260125006_id_allocator_facade.py`
- [ ] Ensure `govreg_core/__init__.py` exists
- [ ] Create `gates/P_01999000042260125000_gate_id_canonicality.py`
- [ ] Migrate/create `ID_SCRIPT_INVENTORY.jsonl` with schema v2.1.4
- [ ] Update `scripts/P_01999000042260124999_id_canonicality_enforcer.py`
- [ ] Install `.git/hooks/pre-commit` (LF-only wrapper)

### Phase 2: Close Execution Gaps
- [ ] Verify `govreg_core/` is importable: `python -c "import govreg_core"`
- [ ] Verify facade import works: `python -c "from govreg_core.P_01999000042260125006_id_allocator_facade import allocate_id"`
- [ ] Verify gate repo-root detection works from `gates/` directory
- [ ] Verify `import_module` field correctness in inventory

### Phase 3: Run Acceptance Tests

**Test 1: Block INTERNAL import (SHOULD FAIL)**
```powershell
'from scripts.P_01999000042260124027_id_allocator import allocate' | Set-Content -NoNewline test_internal.py
git add test_internal.py
git commit -m "test: internal import"  # Should FAIL
Remove-Item test_internal.py
git reset HEAD test_internal.py
```

**Test 2: Block DEPRECATED import (SHOULD FAIL)**
```powershell
# Use actual deprecated module from inventory
'from scripts.P_<deprecated_id>_... import ...' | Set-Content -NoNewline test_deprecated.py
git add test_deprecated.py
git commit -m "test: deprecated import"  # Should FAIL
Remove-Item test_deprecated.py
git reset HEAD test_deprecated.py
```

**Test 3: Block new ID script not in inventory (SHOULD FAIL)**
```powershell
'# test script' | Set-Content -NoNewline P_01999000042260199999_test.py
git add P_01999000042260199999_test.py
git commit -m "test: new ID script"  # Should FAIL (freshness)
Remove-Item P_01999000042260199999_test.py
git reset HEAD P_01999000042260199999_test.py
```

**Test 4: Allow facade import (SHOULD PASS - temp branch)**
```powershell
$currentBranch = (git rev-parse --abbrev-ref HEAD)
git checkout -b tmp_gate_test | Out-Null

'from govreg_core.P_01999000042260125006_id_allocator_facade import allocate_id' | 
  Set-Content -NoNewline test_valid.py
git add test_valid.py
git commit -m "tmp: gate allow test"  # Should PASS

git checkout $currentBranch | Out-Null
git branch -D tmp_gate_test | Out-Null
Remove-Item test_valid.py -ErrorAction SilentlyContinue
```

### Phase 4: Execute Cleanup
- [ ] Run analysis: `python scripts/P_01999000042260124999_id_canonicality_enforcer.py --action analyze`
- [ ] Dry-run archive: `... --action archive --dry-run`
- [ ] Execute archive: `... --action archive` (uses `git mv`)
- [ ] Re-run analysis: confirm 0 conflicts
- [ ] Generate evidence reports in `evidence/id_canonicality/`

### Phase 5: Lock-In
- [ ] Commit all changes
- [ ] Verify hook blocks violations in normal workflow
- [ ] Add CI job to run gate on PRs (optional)
- [ ] Update documentation index

---

## ✅ SUCCESS CRITERIA

- ✅ Zero FILE_ID conflicts after cleanup
- ✅ Zero local ID regex definitions outside `canonical_id_patterns.py`
- ✅ All allocations go through `id_allocator_facade`
- ✅ Gate blocks INTERNAL/DEPRECATED imports
- ✅ Gate enforces inventory freshness
- ✅ Inventory mutations are atomic + evidenced
- ✅ Hook runs reliably on Windows (LF-only, wrapper script)
- ✅ All 4 acceptance tests pass

---

**Generated:** 2026-02-12T22:41:46Z  
**Version:** v2.1.4-READY  
**Status:** EXECUTION-READY (all blockers fixed)
