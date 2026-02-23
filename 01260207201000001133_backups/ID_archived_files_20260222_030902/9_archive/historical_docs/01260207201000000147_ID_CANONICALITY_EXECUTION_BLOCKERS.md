# ID Canonicality - EXECUTION BLOCKERS (v2.1.3 → v2.1.3.1)

**Date:** 2026-02-12 20:58 UTC  
**Status:** 🚨 CRITICAL - v2.1.3 WILL FAIL WITHOUT THESE FIXES  
**Impact:** 8 hard blockers + policy bugs identified  

---

## 🚨 HARD BLOCKERS (Will Break Execution)

### Blocker 1: Facade filename inconsistency

**Problem:**
- Plan creates: `govreg_core/id_allocator_facade.py` (no prefix)
- Inventory claims: `doc_id="P_019...25006"`, `filename_prefix_kind=DOC_PREFIXED`
- **This is false** - filename doesn't start with `P_<20>_`
- Breaks prefix-first rules, makes inventory untrustworthy

**Fix:**
```python
# CREATE THIS FILE:
govreg_core/P_01999000042260125006_id_allocator_facade.py

# UPDATE INVENTORY:
{
  "file_id_numeric": "01999000042260125006",
  "doc_id": "P_01999000042260125006",
  "relative_path": "govreg_core/P_01999000042260125006_id_allocator_facade.py",
  "filename_prefix_kind": "DOC_PREFIXED",  # Now TRUE
  "import_module": "govreg_core.P_01999000042260125006_id_allocator_facade",
  ...
}
```

---

### Blocker 2: Canonical patterns module referenced but never created

**Problem:**
- Gate hardcodes: `self.canonical_patterns = 'govreg_core.P_...25002_canonical_id_patterns'`
- **File doesn't exist** - plan never creates it
- Gate will crash on startup

**Fix:**
```python
# CREATE THIS FILE:
# govreg_core/P_01999000042260125002_canonical_id_patterns.py

import re
from typing import Optional, Tuple

# Canonical ID patterns (SINGLE SOURCE OF TRUTH)
FILE_ID_PATTERN = re.compile(r'^\d{20}$')
DOC_ID_PATTERN = re.compile(r'^P_\d{20}$')
FILENAME_PREFIX_PATTERN = re.compile(r'^(?:(?P<doc_prefix>P_))?(?P<file_id>\d{20})_')

def extract_file_id_from_filename(filename: str) -> Tuple[bool, Optional[str], bool]:
    """
    Extract file_id from filename prefix.
    
    Returns:
        (has_prefix, file_id, is_doc_prefixed)
    """
    match = FILENAME_PREFIX_PATTERN.match(filename)
    if not match:
        return (False, None, False)
    
    file_id = match.group('file_id')
    is_doc = match.group('doc_prefix') is not None
    return (True, file_id, is_doc)

def is_valid_file_id(file_id: str) -> bool:
    """Validate 20-digit numeric file_id."""
    return FILE_ID_PATTERN.match(file_id) is not None

def is_valid_doc_id(doc_id: str) -> bool:
    """Validate P_<20digit> doc_id."""
    return DOC_ID_PATTERN.match(doc_id) is not None

def normalize_doc_id(file_id: str) -> str:
    """Convert file_id to doc_id format."""
    if not is_valid_file_id(file_id):
        raise ValueError(f"Invalid file_id: {file_id}")
    return f"P_{file_id}"
```

**Add to inventory:**
```json
{
  "file_id_numeric": "01999000042260125002",
  "doc_id": "P_01999000042260125002",
  "relative_path": "govreg_core/P_01999000042260125002_canonical_id_patterns.py",
  "filename_prefix_kind": "DOC_PREFIXED",
  "import_module": "govreg_core.P_01999000042260125002_canonical_id_patterns",
  "is_importable": true,
  "canonicality": "CANONICAL",
  "id_generation_mode": null,
  "alignment_status": "ALIGNS",
  "role": "PATTERN_LIBRARY",
  "id_type": null
}
```

---

### Blocker 3: `scripts.*` imports may not work

**Problem:**
- Facade imports: `from scripts.P_..._id_allocator import ...`
- Only works if:
  - `scripts/__init__.py` exists (package)
  - Repo root is on `PYTHONPATH`
- Otherwise: `ModuleNotFoundError`

**Fix Option 1 (RECOMMENDED):**
```python
# Move allocator implementations INTO govreg_core/
# Keep scripts/ as CLI wrappers only

# govreg_core/P_01999000042260124027_id_allocator_impl.py
# (move implementation here)

# scripts/P_01999000042260124027_id_allocator.py becomes:
from govreg_core.P_01999000042260124027_id_allocator_impl import main
if __name__ == '__main__':
    main()
```

**Fix Option 2 (MINIMUM VIABLE):**
```python
# Create scripts/__init__.py
# Ensure repo root on PYTHONPATH everywhere:
#   - Gate adds it at startup
#   - Enforcer adds it
#   - All CLI tools add it
#   - CI configures it

# In all entry points, add:
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
```

---

### Blocker 4: Gate repo-root detection breaks when installed as hook

**Problem:**
- Gate uses: `repo_root = Path(__file__).parent.parent`
- Works in `gates/` (2 parents up = repo root)
- **Breaks when copied to** `.git/hooks/pre-commit` (points to `.git/`)

**Fix:**
```python
def get_repo_root() -> Path:
    """Robustly detect repository root."""
    import subprocess
    
    # Try git command first
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Fallback: walk up to find .git/
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    
    raise RuntimeError("Cannot determine repository root")

# In gate __init__:
self.repo_root = get_repo_root()
```

---

### Blocker 5: Installing gate by copying `.py` to `.git/hooks/` won't execute

**Problem:**
- Git hooks must be executable scripts
- Copying `.py` file directly often won't run (no shebang, wrong permissions)
- Windows Git particularly problematic

**Fix:**
```bash
# CREATE: .git/hooks/pre-commit (shell wrapper)
#!/usr/bin/env bash
python gates/P_01999000042260125000_gate_id_canonicality.py "$@"
exit $?
```

**Installation command:**
```powershell
# Phase 6 revised:
$hookContent = @"
#!/usr/bin/env bash
python gates/P_01999000042260125000_gate_id_canonicality.py "`$@"
exit `$?
"@

Set-Content -Path ".git\hooks\pre-commit" -Value $hookContent -Encoding UTF8
# No need for chmod on Windows Git Bash (respects file content)
```

---

## 🐛 POLICY BUGS (Will Cause Drift)

### Bug 6: "Gate allows CANONICAL only" is wrong

**Problem:**
- Gate cannot whitelist "CANONICAL imports only" globally
- Would break normal Python development (`import json`, `from pathlib import Path`)

**Correct Rule:**
```python
# Block imports of ID INVENTORY MODULES that are:
#   - DEPRECATED
#   - INTERNAL
# Allow all other imports (normal Python code)

def check_imports(self, tree: ast.AST, filepath: Path) -> List[str]:
    violations = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module_name = self._get_module_name(node)
            
            # Check if this is an ID inventory module
            inventory_entry = self._find_inventory_entry_by_import(module_name)
            
            if inventory_entry:
                # This IS an ID module - enforce rules
                canonicality = inventory_entry.get('canonicality')
                
                if canonicality == 'DEPRECATED':
                    violations.append(
                        f"Import of DEPRECATED module: {module_name}"
                    )
                elif canonicality == 'INTERNAL':
                    violations.append(
                        f"Import of INTERNAL module: {module_name} "
                        f"(use facade instead)"
                    )
            # else: not an ID module, allow (normal Python imports)
    
    return violations
```

---

### Bug 7: Inventory migration guesses `import_module` from path

**Problem:**
```python
# Current naive derivation:
import_module = path.replace('/', '.').replace('\\', '.').replace('.py', '')
# Produces strings like: "scripts.P_019...27_id_allocator"
# But "scripts" may not be a package!
```

**Fix:**
```python
def derive_import_module(relative_path: str) -> Optional[str]:
    """
    Derive import module string ONLY if in a real package.
    
    Rules:
    - Must be under a directory with __init__.py
    - Must be a .py file
    - Returns None if not importable
    """
    path = Path(relative_path)
    
    # Not a Python file
    if path.suffix != '.py':
        return None
    
    # Check if parent is a package
    parent = path.parent
    if not (parent / '__init__.py').exists():
        # Not in a package - not importable
        return None
    
    # Build module path
    parts = []
    current = path
    
    while current.parent != Path('.'):
        if current.suffix == '.py':
            parts.insert(0, current.stem)
        else:
            parts.insert(0, current.name)
        
        current = current.parent
        
        # Stop if we leave the package tree
        if not (current / '__init__.py').exists():
            break
    
    return '.'.join(parts) if parts else None

# In migrate_inventory():
import_module = derive_import_module(entry['relative_path'])
is_importable = import_module is not None
```

---

### Bug 8: Gate missing "freshness" enforcement

**Problem:**
- New `P_<20>_*.py` files can be added without inventory update
- Bypass classification until later manual cleanup

**Fix:**
```python
def check_inventory_freshness(self, staged_files: List[Path]) -> List[str]:
    """
    Fail if new ID-prefixed scripts are not in inventory.
    """
    violations = []
    
    # Pattern for ID-prefixed Python files
    id_prefix_pattern = re.compile(r'^(?:P_)?\d{20}_.*\.py$')
    
    for filepath in staged_files:
        filename = filepath.name
        
        if id_prefix_pattern.match(filename):
            # This is an ID script - must be inventoried
            relative_path = str(filepath.relative_to(self.repo_root))
            
            if not self._is_in_inventory(relative_path):
                violations.append(
                    f"New ID script not in inventory: {relative_path}\n"
                    f"  Run: python scripts/P_..._id_canonicality_enforcer.py "
                    f"--action analyze"
                )
    
    return violations

def _is_in_inventory(self, relative_path: str) -> bool:
    """Check if path exists in inventory."""
    for entry in self.inventory_entries:
        if entry.get('relative_path') == relative_path:
            return True
    return False
```

---

## 📋 MINIMAL PATCH CHECKLIST

Apply these in order before executing v2.1.3:

### 1. Create Missing Files
- [ ] `govreg_core/P_01999000042260125002_canonical_id_patterns.py`
- [ ] `govreg_core/P_01999000042260125006_id_allocator_facade.py` (correct name)
- [ ] `govreg_core/__init__.py` (if missing)
- [ ] `scripts/__init__.py` (if using Option 2 for imports)

### 2. Fix Inventory
- [ ] Update facade entry: correct filename, import_module
- [ ] Add patterns module entry
- [ ] Fix `derive_import_module()` to check for packages

### 3. Fix Gate
- [ ] Replace `repo_root = Path(__file__).parent.parent` with `get_repo_root()`
- [ ] Update import blocking: use `import_module` from inventory
- [ ] Add `check_inventory_freshness()` enforcement
- [ ] Fix policy wording (no "CANONICAL only" global rule)

### 4. Fix Hook Installation
- [ ] Create shell wrapper script (not copy `.py` directly)
- [ ] Update Phase 6 installation command

### 5. Verify Execution Path
- [ ] Test gate runs from `gates/` directory
- [ ] Test gate runs from `.git/hooks/pre-commit`
- [ ] Test facade can import backend allocators
- [ ] Test canonical patterns module can be imported

---

## ⏱️ Time Impact

```
Fix Time:         1.5 hours
  - Create files    30 min
  - Fix inventory   15 min
  - Fix gate        30 min
  - Fix install     15 min

Original v2.1.3:  7.5 hours
Hardening Deltas: 2 hours
Tests:            30 min
─────────────────────────
New Total:        11.5 hours
```

---

## 🎯 Updated Execution Order

1. **Apply Execution Blockers** (this document) - 1.5 hours
2. **Execute v2.1.3 Plan** (revised) - 7.5 hours
3. **Apply Hardening Deltas** - 2 hours
4. **Run Acceptance Tests** - 30 min

**Total: 11.5 hours** (was 10 hours)

---

## ✅ Success Criteria (Post-Fix)

After applying these fixes, v2.1.3 will be truly executable:

- [ ] All referenced files exist
- [ ] Inventory entries match actual filenames
- [ ] Imports work from gate, enforcer, and facade
- [ ] Gate detects repo root correctly (gates/ and hooks/)
- [ ] Hook installation works and executes
- [ ] Policy rules are accurate (no false positives on normal Python)
- [ ] Freshness enforcement prevents untracked ID scripts

---

**STATUS: Apply these 8 fixes BEFORE executing v2.1.3**

**CONFIDENCE: 99.9% → After fixes applied**
