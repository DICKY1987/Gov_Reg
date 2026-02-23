# Comprehensive Deprecated ID Files Archival Strategy

**Document ID**: DOC-ARCHIVAL-STRATEGY-20260213  
**Created**: 2026-02-13T06:36:39Z  
**Purpose**: Complete strategy for archiving all deprecated ID-related files safely without breaking production

---

## Executive Summary

The ID canonicality system has identified **3 INTERNAL allocator backends** that must be handled before comprehensive archival can complete:

1. `scripts/P_01999000042260124027_id_allocator.py` (20-digit, thread-based)
2. `govreg_core/P_01999000042260124031_unified_id_allocator.py` (22-digit, COUNTER_STORE)
3. `src/registry_writer/P_01260207233100000333_id_allocator.py` (registry-embedded)

**Current Status**: These are marked `INTERNAL` (not `DEPRECATED`) because they have **active import references** that would break if archived immediately.

---

## Analysis Results

### Active Import References Found

#### 1. `govreg_core/P_01999000042260124031_unified_id_allocator.py`

**Live Importers** (2 files):
- `govreg_core/P_01999000042260125006_id_allocator_facade.py` (line 21) - **CANONICAL FACADE**
- `tests/P_01999000042260124040_test_reservation_system.py` (line 22) - **TEST FILE**

**Import Pattern**:
```python
from govreg_core.P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator
```

**Status**: ✅ **LEGITIMATE INTERNAL USE** - The facade correctly imports this as a backend implementation. This is the intended architecture.

**Action Required**: **KEEP AS INTERNAL** - Do NOT archive. This is a legitimate backend that the facade depends on.

---

#### 2. `scripts/P_01999000042260124027_id_allocator.py`

**Live Importers**: ❌ **NONE FOUND**

**Path References** (documentation/registry only):
- Multiple registry JSON entries (historical data)
- Documentation/analysis files
- `src/registry_writer/P_01260207233100000333_id_allocator.py` contains a comment referencing it (line 21)

**Status**: 🟡 **SAFE TO ARCHIVE** - No active Python imports detected. Only referenced in:
1. Historical registry data (safe)
2. Documentation (safe)
3. Comments (safe)

**Action Required**: Can be archived immediately.

---

#### 3. `src/registry_writer/P_01260207233100000333_id_allocator.py`

**Live Importers**: ❌ **NONE FOUND**

**Path References**: Only in registry metadata and documentation

**Status**: 🟡 **SAFE TO ARCHIVE** - No active Python imports detected.

**Action Required**: Can be archived immediately.

---

## Two Categories of "Deprecated" Files

### Category A: Safe-to-Archive "Dead Duplicates"

These files have NO active imports and can be moved immediately via `git mv`:

1. ✅ `scripts/P_01999000042260124027_id_allocator.py` - No imports found
2. ✅ `src/registry_writer/P_01260207233100000333_id_allocator.py` - No imports found
3. ✅ `REGISTRY/scripts/P_01999000042260124027_id_allocator.py` - Already archived (missing file)

### Category B: Backend Implementation (KEEP as INTERNAL)

These are actively used by the canonical facade and MUST remain:

1. ⚠️ `govreg_core/P_01999000042260124031_unified_id_allocator.py` - **KEEP**
   - Used by: `id_allocator_facade.py` (canonical)
   - Used by: test suite
   - **This is the correct architecture** - facade → backend pattern

---

## Corrected Architecture Understanding

### The Facade Pattern (CORRECT DESIGN)

```
Application Code
      ↓
[CANONICAL] govreg_core/P_01999000042260125006_id_allocator_facade.py
      ↓
[INTERNAL] govreg_core/P_01999000042260124031_unified_id_allocator.py
      ↓
COUNTER_STORE.json (state persistence)
```

**Why this is correct**:
- Facade provides stable public API
- Backend (INTERNAL) provides implementation
- Gate blocks direct imports of INTERNAL modules
- Only facade can import INTERNAL backends

**Mistake to avoid**: Archiving `P_01999000042260124031_unified_id_allocator.py` would break the facade and test suite.

---

## Corrected Inventory Classification

### Current Inventory (Correct)

```jsonl
{"file_id_numeric":"01999000042260124031","canonicality":"INTERNAL","role":"ALLOCATOR"}
```

**Status**: ✅ **CORRECT** - This should remain `INTERNAL`, not `DEPRECATED`.

### Files That Should Be Archived

```jsonl
{"file_id_numeric":"01999000042260124027","canonicality":"INTERNAL","role":"ALLOCATOR"}
{"file_id_numeric":"01260207233100000333","canonicality":"INTERNAL","role":"ALLOCATOR"}
```

**Status**: 🔄 **UPDATE TO DEPRECATED** - These have no active imports and should be archived.

---

## Safe Archival Workflow

### Phase 1: Update Inventory Classifications

**Modify** `ID_SCRIPT_INVENTORY.jsonl`:

**Change line 5** (P_01999000042260124027):
```json
{"file_id_numeric":"01999000042260124027","doc_id":"P_01999000042260124027","relative_path":"scripts/P_01999000042260124027_id_allocator.py","import_module":"scripts.P_01999000042260124027_id_allocator","is_importable":true,"filename_prefix_kind":"DOC_PREFIXED","id_generation_mode":"20_DIGIT_FILE_ID","role":"ALLOCATOR","canonicality":"DEPRECATED","superseded_by_path":"govreg_core/P_01999000042260125006_id_allocator_facade.py","archive_reason":"No active imports; superseded by facade"}
```

**Change line 7** (P_01260207233100000333):
```json
{"file_id_numeric":"01260207233100000333","doc_id":"P_01260207233100000333","relative_path":"src/registry_writer/P_01260207233100000333_id_allocator.py","import_module":"src.registry_writer.P_01260207233100000333_id_allocator","is_importable":true,"filename_prefix_kind":"DOC_PREFIXED","id_generation_mode":"20_DIGIT_FILE_ID","role":"ALLOCATOR","canonicality":"DEPRECATED","superseded_by_path":"govreg_core/P_01999000042260125006_id_allocator_facade.py","archive_reason":"No active imports; superseded by facade"}
```

**Keep line 6 unchanged** (P_01999000042260124031):
```json
{"file_id_numeric":"01999000042260124031","doc_id":"P_01999000042260124031","relative_path":"govreg_core/P_01999000042260124031_unified_id_allocator.py","import_module":"govreg_core.P_01999000042260124031_unified_id_allocator","is_importable":true,"filename_prefix_kind":"DOC_PREFIXED","id_generation_mode":"22_DIGIT_ENHANCED_ID","role":"ALLOCATOR","canonicality":"INTERNAL","superseded_by_path":"govreg_core/P_01999000042260125006_id_allocator_facade.py","retention_reason":"Backend implementation used by canonical facade"}
```

---

### Phase 2: Archive Dead Files

**Execute**:

```powershell
# Create archive directory if needed
New-Item -ItemType Directory -Force "Archive_Gov_Reg\id_scripts_deprecated\allocators" | Out-Null

# Archive P_01999000042260124027
git mv "scripts/P_01999000042260124027_id_allocator.py" "Archive_Gov_Reg/id_scripts_deprecated/allocators/"

# Archive P_01260207233100000333
git mv "src/registry_writer/P_01260207233100000333_id_allocator.py" "Archive_Gov_Reg/id_scripts_deprecated/allocators/"

# Commit with evidence
git commit -m "Archive deprecated ID allocators (no active imports)

- Archived: P_01999000042260124027_id_allocator.py
- Archived: P_01260207233100000333_id_allocator.py
- Retained: P_01999000042260124031_unified_id_allocator.py (INTERNAL backend)

Evidence: No active Python imports detected via AST scan
Superseded by: id_allocator_facade.py (CANONICAL)"
```

---

### Phase 3: Verification Tests

**After archival, verify**:

```powershell
# 1. Gate still works
python gates/P_01999000042260125000_gate_id_canonicality.py

# 2. Facade still imports backend successfully
python -c "from govreg_core.P_01999000042260125006_id_allocator_facade import allocate_id; print('✅ Facade import successful')"

# 3. Test suite still passes
pytest tests/P_01999000042260124040_test_reservation_system.py

# 4. Verify archived files are inaccessible
python -c "from scripts.P_01999000042260124027_id_allocator import allocate_id" 2>&1 | Select-String "ModuleNotFoundError"
# Should output: ModuleNotFoundError (expected)
```

---

## Why P_01999000042260124031 Must Stay

### Legitimate Backend Architecture

**The facade pattern requires**:
1. **Public API layer** (facade) - `P_01999000042260125006_id_allocator_facade.py`
2. **Implementation layer** (backend) - `P_01999000042260124031_unified_id_allocator.py`

**Facade code (line 21)**:
```python
from govreg_core.P_01999000042260124031_unified_id_allocator import UnifiedIDAllocator
```

**This is correct design** because:
- Application code imports facade only
- Gate blocks direct INTERNAL imports by application code
- Facade is allowed to import INTERNAL backends (it's the only authorized consumer)

### Marking as DEPRECATED Would Be Wrong

If we marked `P_01999000042260124031_unified_id_allocator.py` as `DEPRECATED`:
1. ❌ Gate would block facade from importing it
2. ❌ Facade would break at import time
3. ❌ All ID allocation would fail
4. ❌ Test suite would fail

**Correct classification**: `INTERNAL` (backend implementation, facade-only access)

---

## Updated Archival Summary

### Files Archived (2)
1. ✅ `scripts/P_01999000042260124027_id_allocator.py` → `Archive_Gov_Reg/id_scripts_deprecated/allocators/`
2. ✅ `src/registry_writer/P_01260207233100000333_id_allocator.py` → `Archive_Gov_Reg/id_scripts_deprecated/allocators/`

### Files Retained as INTERNAL (1)
3. ⚠️ `govreg_core/P_01999000042260124031_unified_id_allocator.py` - **KEEP** (legitimate backend)

### Files Already Missing (1)
4. ℹ️ `REGISTRY/scripts/P_01999000042260124027_id_allocator.py` - Already removed (not found in repo)

---

## Gate Enforcement After Archival

**The gate will block**:
- ❌ Direct imports of archived/deprecated modules
- ❌ Direct imports of INTERNAL backends (except by facade)
- ❌ New ID scripts not in inventory

**The gate will allow**:
- ✅ Facade imports (CANONICAL)
- ✅ Canonical patterns module imports
- ✅ Facade importing INTERNAL backends (authorized use)

---

## Long-Term Architecture

### Current State (Post-Archival)

```
[CANONICAL] id_allocator_facade.py
     ↓ (imports)
[INTERNAL] unified_id_allocator.py (backend)
     ↓ (uses)
[DATA] COUNTER_STORE.json

[ARCHIVED] P_01999000042260124027 (old 20-digit allocator)
[ARCHIVED] P_01260207233100000333 (registry-embedded allocator)
```

### Enforcement Model

| Module Type | Import Rules | Archival Status |
|------------|--------------|-----------------|
| CANONICAL | Importable by all application code | Active |
| INTERNAL | Importable only by CANONICAL modules | Active (backend) |
| DEPRECATED | Import blocked by gate | Archived |
| REFERENCE | Read-only, no gate block | Active (documentation) |

---

## Acceptance Criteria

### ✅ Success Conditions
1. 2 files archived (P_...27, P_...333)
2. 1 file retained as INTERNAL (P_...31)
3. Facade still imports backend successfully
4. Test suite passes
5. Gate blocks imports of archived files
6. Gate allows facade to import INTERNAL backend
7. No runtime import errors

### ❌ Failure Conditions (Avoid)
- Archiving P_...31 (would break facade)
- Missing verification tests
- Breaking test suite
- Creating import errors

---

## Evidence Trail

### Before Archival
- Import scan: 2 files have no active imports
- AST analysis: Only facade + tests import P_...31
- Gate enforcement: Ready to block deprecated imports

### After Archival
- Files moved via `git mv` (history preserved)
- Inventory updated with `DEPRECATED` status
- Verification tests pass
- Gate blocks archived file imports
- No runtime errors

---

## Recommendation

**Execute Phase 1-3 in sequence**:

1. ✅ Update inventory classifications (P_...27 and P_...333 to DEPRECATED)
2. ✅ Archive 2 safe files via `git mv`
3. ✅ Run verification tests
4. ✅ Commit with evidence

**Do NOT archive** `P_01999000042260124031_unified_id_allocator.py` - it is a legitimate backend implementation used by the canonical facade.

---

## Questions & Clarifications

### Q: Why not archive all 3 INTERNAL files?
**A**: Only P_...27 and P_...333 have zero imports. P_...31 is actively used by the facade (correct architecture).

### Q: Isn't having INTERNAL allocators a problem?
**A**: No - the facade pattern requires backend implementations. The gate prevents direct imports by application code, forcing all access through the facade.

### Q: What if we want to remove P_...31 later?
**A**: You would need to:
1. Rewrite facade to use a different backend
2. Update tests
3. Then archive P_...31
4. But this is unnecessary - the current architecture is correct.

### Q: How do we prevent new INTERNAL allocators?
**A**: Gate already enforces:
- No new allocator definitions without facade import
- No bespoke ID regex patterns
- All new ID scripts must be in inventory

---

**Document Status**: ✅ READY FOR EXECUTION  
**Next Action**: Execute Phase 1 (update inventory) → Phase 2 (archive) → Phase 3 (verify)
