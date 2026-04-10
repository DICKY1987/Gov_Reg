# Architecture Reference: Column Runtime Engine & File Intake Pipeline
## Detailed Implementation Design for PLAN-20260305-UNIFIED-V3-MERGED

> **Role:** Architecture appendix — implementation-level pseudocode for Phase 0 and Week 2 components.
> **Active execution plan:** `UNIFIED_SOLUTION_PLAN_V3_MERGED.md`
> **Machine-readable tasks:** `UNIFIED_SOLUTION_PLAN_V3_REMAINING_STEPS.json`
> **Relocated:** Moved from repo root `COMPLETE_REGISTRY_AUTOMATION_PLAN.md` on 2026-03-06.

**Original Plan ID:** `PLAN-20260305-COMPLETE-AUTOMATION-V1`
**Created:** 2026-03-05T06:53:09Z
**Updated:** 2026-03-06
**Status:** ARCHITECTURE REFERENCE — Superseded as a standalone plan by V3-MERGED
**Owner:** Gov_Reg Governance System

---

## Executive Summary

This plan unifies **three incomplete efforts** into one deterministic automation system:

1. **Capability Mapping** (37 `py_*` columns) - currently 75% complete, Step 3 missing
2. **51 Inconsistent Columns** - formula_sheet shows 42 "manual_or_automated requires derivation but none found" + 9 "immutable but no derivation"
3. **File Intake Pipeline** - no end-to-end "file added → registry populated" automation exists

### What You Currently Have

✅ **Strong Foundation:**
- 185-column registry schema with write policies
- 30+ mapp_py analyzer scripts (AST, imports, I/O, complexity)
- 4-step capability mapping pipeline (Steps 1-2 complete)
- Column dictionary + formula sheet + write policy (governance layer)
- Evidence hashing + RFC-6902 patch infrastructure

❌ **Critical Gaps:**
- No unified runtime that enforces write policies + derivation triggers
- File ID mismatch blocks py_* promotion (SHA-256 vs 20-digit IDs)
- 51 columns marked "inconsistent" - update policies don't match derivation reality
- No "on file add" orchestrator that runs scan→analyze→promote deterministically
- Lookup layer incomplete (registry-to-registry joins)

### What This Plan Delivers

**Phase 0: Column Runtime Engine** (Foundation)
- Unified runtime that reads: column dict + write policy + formula sheet + py mapping
- Dependency scheduler (topological ordering via `depends_on`)
- Trigger dispatcher (`recompute_on_scan`, `recompute_on_build`, `manual_patch_only`)
- Evidence-backed derivation executor

**Phase 1: File Intake Pipeline** (The "Add File" Automation)
- S1: Identity allocation (file_id, dir_id, SHA-256)
- S2: Filesystem primitives (path, size, mtime, extension)
- S3: Scan-trigger derivations (artifact_kind, canonical_path, lookups)
- S4: Python analyzer dispatch (mapp_py orchestration)
- S5: Promotion bridge (SHA-256 → file_id mapping)
- S6: Evidence bundle emission

**Phase 2: Resolve 51 Inconsistent Columns** (Close Governance Gaps)
- Fix 42 "manual_or_automated requires derivation" columns
- Fix 9 "immutable but no derivation" columns
- Validate against write policy rules

**Phase 3: Complete Capability Mapping** (Finish Existing Work)
- Execute Step 3 (purpose mapping)
- Apply Step 4 patches to SSOT
- Integrate with unified runtime

**Phase 4: Convergent Evidence Integration** (Advanced Features)
- Timestamp clustering
- AI provenance linking
- Multi-signal confidence scoring

---

## Architecture Overview

### The Column Runtime Engine (Core Innovation)

```
┌─────────────────────────────────────────────────────────────┐
│                   COLUMN RUNTIME ENGINE                      │
│                                                              │
│  Inputs:                                                     │
│  - COLUMN_DICTIONARY.json (types, modes, presence)         │
│  - WRITE_POLICY.yaml (update_policy, writable_by)          │
│  - formula_sheet_classification.csv (triggers, depends_on) │
│  - PY_COLUMN_PIPELINE_MAPPING.csv (py_* producers)         │
│                                                              │
│  Components:                                                 │
│  1. Schema Loader (validates + merges 4 sources)            │
│  2. Dependency Scheduler (topological sort by depends_on)   │
│  3. Trigger Dispatcher (on_create, on_scan, on_build)       │
│  4. Derivation Executor (runs formulas + analyzers)         │
│  5. Lookup Resolver (registry-to-registry joins)            │
│  6. Patch Generator (RFC-6902 operations)                   │
│  7. Evidence Writer (SHA-256 hashes, run manifests)         │
│                                                              │
│  Output: Deterministic patches + evidence per trigger event │
└─────────────────────────────────────────────────────────────┘
```

### File Intake Pipeline (Uses Runtime Engine)

```
FILE_ADDED_EVENT
    ↓
┌───────────────────────────────────────────────────────────┐
│ S1: IDENTITY ALLOCATION                                   │
│ - Allocate file_id (20-digit)                            │
│ - Compute sha256                                          │
│ - Resolve/create dir_id                                   │
│ - Set allocated_at, created_utc                           │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ S2: FILESYSTEM PRIMITIVES                                 │
│ - Extract: absolute_path, relative_path, size_bytes      │
│ - Extract: mtime_utc, extension, filename                │
│ - Normalize: canonical_path                               │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ S3: SCAN-TRIGGER DERIVATIONS (via Runtime Engine)        │
│ - Trigger: recompute_on_scan                             │
│ - Run: artifact_kind inference                            │
│ - Run: all LOOKUP derivations (needs registry index)     │
│ - Run: simple DERIVED formulas (no external analyzers)   │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ S4: ANALYZER DISPATCH (artifact_kind routing)            │
│ - IF .py → Run mapp_py pipeline (Phase A/B/C)           │
│ - IF .json/.yaml → Run schema analyzer                   │
│ - IF .md → Run doc analyzer                              │
│ - Outputs: facts + SHA-256 evidence                      │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ S5: PROMOTION BRIDGE                                      │
│ - Map analyzer outputs (keyed by sha256)                 │
│ - Join to registry record (via SHA256_TO_FILE_ID.json)  │
│ - Transform PARTIAL columns → registry format            │
│ - Apply via Runtime Engine (recompute_on_scan trigger)   │
└───────────────────────────────────────────────────────────┘
    ↓
┌───────────────────────────────────────────────────────────┐
│ S6: EVIDENCE EMISSION                                     │
│ - Write run manifest (timestamp, tool versions, inputs)  │
│ - Write evidence bundle (all derivations + SHA-256)      │
│ - Write registry patches (RFC-6902)                      │
│ - Optional: Queue build-trigger derivations              │
└───────────────────────────────────────────────────────────┘
    ↓
REGISTRY_UPDATED (audit trail complete)
```

---

## Phase 0: Build Column Runtime Engine (5-7 days)

### 0.1 Schema Loader & Validator

**Goal:** Unify 4 governance sources into runtime-usable format

**Inputs:**
- `COLUMN_DICTIONARY.json` (185 columns)
- `WRITE_POLICY.yaml` (update policies per column)
- `formula_sheet_classification.csv` (triggers + depends_on)
- `PY_COLUMN_PIPELINE_MAPPING.csv` (py_* producers)

**Implementation:** `P_01999000042260305010_column_runtime_loader.py`

**Logic:**
```python
class ColumnRuntimeSchema:
    def __init__(self, col_dict_path, write_policy_path, formula_path, py_mapping_path):
        # Load all 4 sources
        col_dict = load_json(col_dict_path)
        write_policy = load_yaml(write_policy_path)
        formulas = load_csv(formula_path)
        py_mapping = load_csv(py_mapping_path)
        
        # Merge into unified column metadata
        self.columns = {}
        for col_name in col_dict.keys():
            self.columns[col_name] = {
                "name": col_name,
                "type": col_dict[col_name]["type"],
                "derivation_mode": col_dict[col_name]["derivation_mode"],
                "presence": col_dict[col_name]["presence"],
                "update_policy": write_policy.get(col_name, {}).get("update_policy"),
                "writable_by": write_policy.get(col_name, {}).get("writable_by"),
                "trigger": formulas[col_name]["trigger"],
                "depends_on": formulas[col_name]["depends_on"],
                "formula": formulas[col_name]["formula"],
                "py_producer": py_mapping.get(col_name, {}).get("pipeline_source"),
                "classification": formulas[col_name]["classification"],
            }
        
        # Validate consistency
        self.inconsistencies = self.validate_policies()
    
    def validate_policies(self):
        """Detect the 51 inconsistent columns"""
        issues = []
        for col_name, meta in self.columns.items():
            # Rule 1: manual_or_automated requires formula OR py_producer
            if meta["update_policy"] == "manual_or_automated":
                if not meta["formula"] and not meta["py_producer"]:
                    issues.append({
                        "column": col_name,
                        "issue": "manual_or_automated requires derivation but none found"
                    })
            
            # Rule 2: immutable with writable_by=tool_only requires on_create formula
            if meta["update_policy"] == "immutable" and meta["writable_by"] == "tool_only":
                if not meta["formula"] or meta["trigger"] != "on_create_only":
                    issues.append({
                        "column": col_name,
                        "issue": "immutable but no on_create derivation"
                    })
            
            # Rule 3: recompute_on_scan requires formula or EXTRACTED mode
            if meta["update_policy"] == "recompute_on_scan":
                if meta["derivation_mode"] not in ["EXTRACTED", "DERIVED", "LOOKUP", "HYBRID"]:
                    if not meta["formula"] and not meta["py_producer"]:
                        issues.append({
                            "column": col_name,
                            "issue": "recompute_on_scan requires derivation"
                        })
        
        return issues
```

**Validation:**
- Detects exactly 51 inconsistencies matching formula_sheet
- Outputs report: `.state/column_runtime/schema_validation_report.json`

---

### 0.2 Dependency Scheduler

**Goal:** Topological ordering of derivations based on `depends_on`

**Implementation:** `P_01999000042260305011_dependency_scheduler.py`

**Algorithm:**
```python
def compute_derivation_order(columns_meta):
    """Topological sort by depends_on."""
    from collections import defaultdict, deque
    
    # Build dependency graph
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    
    for col_name, meta in columns_meta.items():
        if not meta["depends_on"]:
            in_degree[col_name] = 0
        for dep in meta["depends_on"]:
            graph[dep].append(col_name)
            in_degree[col_name] += 1
    
    # Kahn's algorithm
    queue = deque([col for col in columns_meta if in_degree[col] == 0])
    order = []
    
    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Detect cycles
    if len(order) != len(columns_meta):
        raise ValueError("Circular dependency detected in column formulas")
    
    return order
```

**Validation:**
- No circular dependencies
- All LOOKUP columns ordered after their dependencies
- Test with known dependency chains (e.g., `canonical_path` depends on `relative_path`)

---

### 0.3 Trigger Dispatcher

**Goal:** Route derivations by trigger type (`on_create`, `recompute_on_scan`, `recompute_on_build`)

**Implementation:** `P_01999000042260305012_trigger_dispatcher.py`

**Logic:**
```python
class TriggerDispatcher:
    def __init__(self, columns_schema):
        self.schema = columns_schema
        self.triggers = {
            "on_create_only": [],
            "recompute_on_scan": [],
            "recompute_on_build": [],
            "manual_patch_only": [],
        }
        
        # Group columns by trigger
        for col_name, meta in columns_schema.columns.items():
            trigger = meta["trigger"] or "manual_patch_only"
            self.triggers[trigger].append(col_name)
    
    def dispatch(self, event_type, record, context):
        """
        event_type: "file_create", "scan_event", "build_event"
        record: current registry record (may be partial)
        context: event data (paths, hashes, analyzer outputs)
        
        Returns: list of (column_name, derivation_callable)
        """
        if event_type == "file_create":
            return [(col, self._get_derivation(col)) 
                    for col in self.triggers["on_create_only"]]
        
        elif event_type == "scan_event":
            return [(col, self._get_derivation(col)) 
                    for col in self.triggers["recompute_on_scan"]]
        
        elif event_type == "build_event":
            return [(col, self._get_derivation(col)) 
                    for col in self.triggers["recompute_on_build"]]
        
        else:
            return []
```

**Validation:**
- `on_create_only` runs exactly once per file
- `recompute_on_scan` runs every intake
- `manual_patch_only` never auto-triggers

---

### 0.4 Derivation Executor

**Goal:** Execute formulas + call py analyzers

**Implementation:** `P_01999000042260305013_derivation_executor.py`

**Supported Operations:**
```python
class DerivationExecutor:
    def execute(self, column_name, formula, record, context):
        """
        formula: string like "NORMALIZE_PATH(INPUT.observed_absolute_path)"
        record: current values
        context: event data
        
        Returns: (new_value, evidence_dict)
        """
        if formula.startswith("NORMALIZE_PATH("):
            return self._normalize_path(formula, context)
        elif formula.startswith("LOOKUP_REGISTRY("):
            return self._lookup_registry(formula, record)
        elif formula.startswith("INFER_ARTIFACT_KIND("):
            return self._infer_artifact_kind(formula, record)
        elif formula.startswith("IF("):
            return self._eval_conditional(formula, record)
        elif formula.startswith("PY_ANALYZER("):
            return self._call_py_analyzer(formula, context)
        else:
            return None, {"error": "Unsupported formula type"}
    
    def _call_py_analyzer(self, formula, context):
        """Bridge to mapp_py scripts."""
        # Extract analyzer name from formula
        # e.g., "PY_ANALYZER(component_extractor)"
        analyzer_name = extract_analyzer_name(formula)
        
        # Load FILE_INVENTORY.jsonl entry for file
        inventory_entry = context.get("inventory_entry")
        
        # Map to py_* column via PY_COLUMN_PIPELINE_MAPPING
        py_columns = self.py_mapping[analyzer_name]
        
        # Return analyzer output + evidence
        return inventory_entry["facts"][py_columns[0]], {
            "analyzer": analyzer_name,
            "sha256": inventory_entry["content_sha256"]
        }
```

**Validation:**
- Test 10 sample formulas (NORMALIZE_PATH, LOOKUP_REGISTRY, IF)
- Evidence dict always includes derivation method
- NULL handling (missing dependencies → NULL + evidence note)

---

### 0.5 Lookup Resolver

**Goal:** Registry-to-registry joins (LOOKUP mode columns)

**Implementation:** `P_01999000042260305014_lookup_resolver.py`

**Index Structure:**
```python
class RegistryIndex:
    def __init__(self, registry_path):
        registry = load_json(registry_path)
        
        # Build indices
        self.by_file_id = {r["file_id"]: r for r in registry["files"]}
        self.by_sha256 = {r["sha256"]: r for r in registry["files"] if "sha256" in r}
        self.by_relative_path = {r["relative_path"]: r for r in registry["files"]}
        
        # Relationship indices
        self.dependencies = self._build_dependency_index(registry)
        self.contracts = self._build_contract_index(registry)
    
    def lookup(self, lookup_type, key):
        """
        lookup_type: "file_by_id", "file_by_sha256", "dependencies_of", etc.
        key: lookup value
        
        Returns: matched record(s) or None
        """
        if lookup_type == "file_by_id":
            return self.by_file_id.get(key)
        elif lookup_type == "file_by_sha256":
            return self.by_sha256.get(key)
        elif lookup_type == "dependencies_of":
            return self.dependencies.get(key, [])
        # ... more lookup types
```

**Validation:**
- Lookup by file_id (primary key)
- Lookup by sha256 (content identity)
- Lookup by relative_path (ambiguity detection)
- Performance: <10ms per lookup on 5000-file registry

---

### 0.6 Patch Generator

**Goal:** Convert derivation results to RFC-6902 operations

**Implementation:** `P_01999000042260305015_patch_generator.py`

**Logic:**
```python
def generate_patch(file_idx, column_name, old_value, new_value, evidence):
    """
    Generate RFC-6902 JSON Patch operation.
    
    Returns: patch operation + evidence record
    """
    if old_value is None and new_value is not None:
        op = {
            "op": "add",
            "path": f"/files/{file_idx}/{column_name}",
            "value": new_value
        }
    elif old_value != new_value:
        op = {
            "op": "replace",
            "path": f"/files/{file_idx}/{column_name}",
            "value": new_value
        }
    else:
        return None, None  # No change
    
    evidence_record = {
        "operation": op,
        "column": column_name,
        "derivation_method": evidence.get("method"),
        "depends_on_columns": evidence.get("dependencies", []),
        "computed_at_utc": datetime.utcnow().isoformat() + 'Z',
        "sha256": hashlib.sha256(json.dumps(op, sort_keys=True).encode()).hexdigest()
    }
    
    return op, evidence_record
```

**Validation:**
- Patches valid RFC-6902 JSON
- Evidence SHA-256 traceable
- No duplicate operations for same path

---

### 0.7 Evidence Writer

**Goal:** Deterministic run manifests + evidence bundles

**Implementation:** `P_01999000042260305016_evidence_writer.py`

**Output Schema:**
```json
{
  "run_manifest": {
    "run_id": "RUN-20260305-153045-a3f2e1",
    "trigger_event": "file_create",
    "file_id": "01234567890123456789",
    "sha256": "abc123...",
    "started_utc": "2026-03-05T15:30:45Z",
    "finished_utc": "2026-03-05T15:31:02Z",
    "columns_derived": 47,
    "patches_generated": 47,
    "evidence_bundle_sha256": "def456..."
  },
  "derivations": [
    {
      "column": "artifact_kind",
      "method": "INFER_ARTIFACT_KIND(extension, relative_path)",
      "dependencies": ["extension", "relative_path"],
      "old_value": null,
      "new_value": "python_module",
      "evidence_sha256": "xyz789..."
    }
  ],
  "analyzer_runs": [
    {
      "analyzer": "component_extractor",
      "analyzer_version": "1.0",
      "input_sha256": "abc123...",
      "output_columns": ["py_component_count", "py_defs_classes_count"],
      "evidence_path": ".state/evidence/mapp_py/component_extractor_abc123.json"
    }
  ]
}
```

**Validation:**
- Run manifest SHA-256 covers entire evidence bundle
- Timestamps ISO 8601 UTC
- All patches traceable to derivations

---

## Phase 1: File Intake Pipeline (3-5 days)

### 1.1 Intake Orchestrator

**Goal:** Unified "file added" automation using Runtime Engine

**Implementation:** `P_01999000042260305020_file_intake_orchestrator.py`

**Command:**
```powershell
python P_01999000042260305020_file_intake_orchestrator.py --file "src/example.py" --event-type "file_create"
```

**Stages:**
```python
class FileIntakeOrchestrator:
    def __init__(self, runtime_engine, registry_index, allocator):
        self.engine = runtime_engine
        self.index = registry_index
        self.allocator = allocator
    
    def ingest_file(self, file_path, event_type="file_create"):
        """Full pipeline: S1 → S6."""
        
        # S1: Identity allocation
        file_id = self.allocator.allocate_file_id()
        sha256 = compute_sha256(file_path)
        dir_id = self._resolve_dir_id(file_path.parent)
        
        identity = {
            "file_id": file_id,
            "sha256": sha256,
            "dir_id": dir_id,
            "allocated_at": datetime.utcnow().isoformat() + 'Z'
        }
        
        # S2: Filesystem primitives
        fs_data = {
            "absolute_path": str(file_path.resolve()),
            "relative_path": str(file_path.relative_to(repo_root)),
            "size_bytes": file_path.stat().st_size,
            "mtime_utc": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() + 'Z',
            "extension": file_path.suffix,
            "filename": file_path.name
        }
        
        # Build initial record
        record = {**identity, **fs_data, "record_kind": "entity", "entity_kind": "file"}
        
        # S3: Scan-trigger derivations (via Runtime Engine)
        scan_patches, scan_evidence = self.engine.derive_columns(
            trigger="recompute_on_scan",
            record=record,
            context={"event_type": event_type}
        )
        
        # Apply patches to record
        for patch in scan_patches:
            apply_patch(record, patch)
        
        # S4: Analyzer dispatch (if artifact_kind determined)
        if record.get("artifact_kind") == "python_module":
            analyzer_outputs = self._run_mapp_py(file_path, sha256)
        else:
            analyzer_outputs = {}
        
        # S5: Promotion bridge (map analyzer outputs to registry columns)
        py_patches, py_evidence = self._promote_py_outputs(
            file_id, sha256, analyzer_outputs
        )
        
        for patch in py_patches:
            apply_patch(record, patch)
        
        # S6: Evidence emission
        run_manifest = {
            "run_id": self.engine.run_id,
            "file_id": file_id,
            "sha256": sha256,
            "patches_count": len(scan_patches) + len(py_patches),
            "evidence": {**scan_evidence, **py_evidence}
        }
        
        write_evidence(run_manifest)
        
        # Write record to registry
        self._append_to_registry(record)
        
        return record, run_manifest
```

**Validation:**
- Run on 10 test files (Python, JSON, Markdown)
- All mandatory columns populated
- Evidence SHA-256 chains complete
- Registry schema validation passes

---

### 1.2 Mapp_Py Bridge

**Goal:** Integrate existing 30-module mapp_py library

**Implementation:** Part of orchestrator

**Logic:**
```python
def _run_mapp_py(self, file_path, sha256):
    """Execute mapp_py analyzers and return outputs."""
    
    # Load FILE_INVENTORY.jsonl entry (if exists from Step 2)
    inventory_entry = self._load_inventory_entry(sha256)
    
    if not inventory_entry:
        # Run Step 2 file_inventory_builder for this file only
        inventory_entry = self._build_inventory_single(file_path)
    
    # Extract facts from inventory
    facts = inventory_entry.get("facts", {})
    
    # Map facts to py_* columns using transformer
    transformer = PyColumnTransformer()
    py_columns = transformer.transform(facts, inventory_entry)
    
    return py_columns
```

**Validation:**
- Reuses existing FILE_INVENTORY.jsonl when available
- Falls back to on-demand analysis
- Transformation layer tested with 20 sample files

---

### 1.3 File ID Reconciliation

**Goal:** Bridge SHA-256 (analyzer key) ↔ 20-digit file_id (registry key)

**Implementation:** `P_01999000042260305001_file_id_reconciler.py` (from earlier plan)

**Used By:** Orchestrator in S5 (promotion bridge)

**Logic:**
```python
def _promote_py_outputs(self, file_id, sha256, analyzer_outputs):
    """Map analyzer outputs (keyed by sha256) to registry record."""
    
    # Load reconciliation map
    sha_to_id = load_json('.state/purpose_mapping/SHA256_TO_FILE_ID.json')
    
    # Verify this file is in the map
    if sha256 not in sha_to_id["sha256_to_file_id"]:
        # Add to map (file is newly allocated)
        sha_to_id["sha256_to_file_id"][sha256] = file_id
        write_json('.state/purpose_mapping/SHA256_TO_FILE_ID.json', sha_to_id)
    
    # Generate patches for py_* columns
    patches = []
    evidence = {}
    
    for py_col, value in analyzer_outputs.items():
        if value is not None:
            patch = {
                "op": "add",
                "path": f"/files/{file_id}/{py_col}",
                "value": value
            }
            patches.append(patch)
            evidence[py_col] = {"source": "mapp_py", "sha256": sha256}
    
    return patches, evidence
```

**Validation:**
- Mapping persistent across runs
- No file_id collisions
- All mapp_py outputs findable

---

## Phase 2: Resolve 51 Inconsistent Columns (2-4 days)

### Strategy: Classify & Resolve Each Column Type

#### 2.1 Type A: Editorial Columns (→ reclassify to `manual_patch_only`)

**Columns (18):**
- `description`, `one_line_purpose`, `short_description`
- `notes`
- `function_code_1`, `function_code_2`, `function_code_3`
- `deliverables`, `inputs`, `outputs`
- `tags`, `step_refs`
- `superseded_by`
- `validation_rules`
- `bundle_key`, `bundle_role`, `bundle_version`
- `resolver_hint`

**Resolution:**
```yaml
# Update WRITE_POLICY.yaml
description:
  update_policy: manual_patch_only  # was: manual_or_automated
  writable_by: user_only
  rationale: "Human-authored field; no reliable auto-inference"

# Repeat for all 18 columns
```

**Validation:**
- formula_sheet consistency check passes
- No more "requires derivation but none found" errors for these

---

#### 2.2 Type B: Inferrable with Defaults (→ add safe formulas)

**Columns (14):**
- `artifact_kind` (✅ already has formula)
- `entity_kind`, `record_kind` (inferrable from record structure)
- `status` (default: "active")
- `canonicality` (default: "primary", unless duplicate detected)
- `expires_utc`, `ttl_seconds` (default: NULL for non-transient)
- `optional_roles`, `required_roles` (default: empty array)
- `scope`, `ns_code`, `role`, `role_code` (inferrable from path structure)
- `type_code` (alias for artifact_kind)

**Resolution - Example:**
```yaml
# Add to formula_sheet_classification.csv
entity_kind:
  formula: |
    IF(EQUALS(record_kind, "entity"), 
       INFER_ENTITY_KIND(artifact_kind, relative_path),
       NULL)
  trigger: on_create_only
  depends_on: ['record_kind', 'artifact_kind', 'relative_path']

status:
  formula: "'active'"
  trigger: on_create_only
  depends_on: []
```

**Implementation:**
- Add formulas to `DerivationExecutor`
- Test with 10 sample files
- Ensure NULL when dependencies missing

---

#### 2.3 Type C: Immutable Identity Fields (→ set on_create via record constructor)

**Columns (9):**
- `created_by`
- `source_file_id`, `target_file_id`
- `source_entity_id`, `target_entity_id`
- `directionality`, `rel_type`, `edge_type`
- `record_kind`

**Resolution:**
```python
# In FileIntakeOrchestrator.__init__()
def _create_entity_record(self, identity, fs_data):
    """Set immutable fields at record creation."""
    return {
        **identity,
        **fs_data,
        "record_kind": "entity",  # IMMUTABLE: set on create
        "entity_kind": "file",    # IMMUTABLE: set on create
        "created_by": "file_intake_orchestrator_v1",  # IMMUTABLE
        "created_utc": datetime.utcnow().isoformat() + 'Z',
        # ... rest from fs_data
    }

# For edge records (different constructor)
def _create_edge_record(self, source_id, target_id, edge_type):
    return {
        "record_kind": "edge",
        "edge_type": edge_type,
        "source_file_id": source_id,  # IMMUTABLE
        "target_file_id": target_id,  # IMMUTABLE
        "directionality": "directed",  # IMMUTABLE (or param)
        "created_by": "edge_generator_v1",
        # ...
    }
```

**Validation:**
- Write policy allows these fields only on create
- Subsequent scans/builds cannot modify
- Evidence shows "on_create_only" trigger

---

#### 2.4 Type D: Lookup-Dependent (→ implement lookup layer first)

**Columns (10):**
- `asset_id`, `asset_family`, `asset_version`
- `external_ref`, `external_system`
- `declared_dependencies`
- `path_aliases`
- `metadata` (structured config/annotation lookups)
- `input_filters`, `output_path_pattern` (generator-specific)

**Resolution:**
```python
# Add to LookupResolver
def lookup_asset_metadata(self, relative_path):
    """Join to asset registry."""
    asset_records = self.index.lookup("asset_by_path", relative_path)
    if asset_records:
        return {
            "asset_id": asset_records[0]["asset_id"],
            "asset_family": asset_records[0]["family"],
            "asset_version": asset_records[0]["version"]
        }
    return {"asset_id": None, "asset_family": None, "asset_version": None}

# Add formula
asset_id:
  formula: "LOOKUP_REGISTRY('asset_by_path', relative_path).asset_id"
  trigger: recompute_on_scan
  depends_on: ['relative_path']
```

**Validation:**
- Lookup returns NULL when no match (not error)
- Evidence shows "lookup_miss" vs "lookup_hit"
- Ambiguous matches → store candidates array

---

### 2.5 Consolidation: Update Governance Files

**Actions:**
1. Update `WRITE_POLICY.yaml` with 18 reclassifications
2. Add 14 new formulas to `formula_sheet_classification.csv`
3. Document 9 on_create fields in `REGISTRY_COLUMN_HEADERS.md`
4. Implement 10 lookup formulas in `LookupResolver`

**Validation Command:**
```powershell
python P_01999000042260305010_column_runtime_loader.py --validate-only
```

**Expected Output:**
```
✅ All 185 columns pass consistency checks
✅ 0 "manual_or_automated requires derivation" errors
✅ 0 "immutable but no derivation" errors
✅ Dependency graph is acyclic
```

---

## Phase 3: Complete Capability Mapping (1-2 days)

### 3.1 Integrate with Runtime Engine

**Goal:** Run Steps 3-4 using unified runtime instead of standalone

**Changes:**
```python
# In FileIntakeOrchestrator, add S7
def ingest_file(self, file_path, event_type="file_create"):
    # ... S1-S6 as before ...
    
    # S7: Capability tagging (if Step 3 complete)
    if self.capability_registry_exists():
        capability_tags = self._lookup_capabilities(file_path)
        record["py_capability_tags"] = capability_tags
        record["py_capability_facts_hash"] = self._hash_capabilities(capability_tags)
    
    return record, run_manifest
```

**Validation:**
- Step 3 output (`FILE_PURPOSE_REGISTRY.json`) loaded into LookupResolver
- `py_capability_tags` populated for Python files
- Evidence links to Step 3 mapping

---

### 3.2 Apply Step 4 Patches

**Goal:** Promote capability mappings to SSOT registry

**Command:**
```powershell
# Backup first
Copy-Item "REGISTRY\01999000042260124503_REGISTRY_file.json" `
          "REGISTRY\01260207201000001133_backups\REGISTRY_file_pre_unified_automation_20260305.json"

# Apply via Runtime Engine
python P_01999000042260305020_file_intake_orchestrator.py --mode backfill-capabilities
```

**Validation:**
- 574 files get `py_capability_tags` arrays
- Registry schema validation passes
- Evidence manifest shows "capability_promotion" run

---

## Phase 4: Convergent Evidence (2-3 days, optional)

### 4.1 Timestamp Clustering

**Integration:**
```python
# Add to FileIntakeOrchestrator
def _add_temporal_context(self, record, run_manifest):
    """Link file to time-burst clusters."""
    clusters = load_json('.state/purpose_mapping/TIMESTAMP_CLUSTERS.json')
    
    for cluster in clusters["clusters"]:
        if record["mtime_utc"] in cluster["time_window"]:
            record["temporal_cluster_id"] = cluster["cluster_id"]
            run_manifest["temporal_cluster"] = cluster["cluster_id"]
            break
```

**Validation:**
- Cluster IDs stable across runs
- Files in same burst share cluster_id

---

### 4.2 AI Provenance Integration

**Integration:**
```python
# Add to FileIntakeOrchestrator
def _link_provenance(self, record, run_manifest):
    """Query AI CLI provenance DB."""
    prov_db = sqlite3.connect('.state/provenance/ai_cli_events.db')
    
    result = prov_db.execute(
        "SELECT session_id, tool FROM file_events WHERE file_path = ?",
        (record["relative_path"],)
    ).fetchone()
    
    if result:
        record["provenance_session_id"] = result[0]
        record["provenance_tool"] = result[1]
        run_manifest["provenance"] = {"session_id": result[0], "tool": result[1]}
```

**Validation:**
- Provenance DB exists and queryable
- Session IDs link to tool logs

---

### 4.3 Multi-Signal Confidence Report

**Implementation:** `P_01999000042260305003_timestamp_cluster_analyzer.py` (enhanced)

**Scoring:**
```python
def compute_convergence_score(record):
    """Multi-signal confidence."""
    signals = {
        "fs_primitives": record.get("sha256") is not None,  # +1
        "artifact_kind_inferred": record.get("artifact_kind") is not None,  # +1
        "py_analysis_complete": record.get("py_analysis_success") == True,  # +2
        "capability_tagged": len(record.get("py_capability_tags", [])) > 0,  # +2
        "temporal_clustered": record.get("temporal_cluster_id") is not None,  # +1
        "provenance_linked": record.get("provenance_session_id") is not None,  # +3
    }
    
    score = sum(signals.values())
    
    if score >= 8:
        return "HIGH"
    elif score >= 5:
        return "MEDIUM"
    else:
        return "LOW"
```

**Output:** `.state/purpose_mapping/CONVERGENT_MAPPING_REPORT.md`

---

## Success Criteria

### Phase 0 (Column Runtime Engine)
- [ ] Schema loader validates 185 columns
- [ ] Detects exactly 51 inconsistencies (before resolution)
- [ ] Dependency scheduler produces acyclic order
- [ ] Derivation executor runs 10 test formulas
- [ ] Lookup resolver handles file_by_id, file_by_sha256
- [ ] Patch generator produces valid RFC-6902
- [ ] Evidence writer creates deterministic SHA-256 hashes

### Phase 1 (File Intake Pipeline)
- [ ] Orchestrator runs S1-S6 without errors
- [ ] 10 test files ingested successfully
- [ ] All mandatory columns populated
- [ ] Mapp_py bridge calls existing analyzers
- [ ] File ID reconciliation map persists
- [ ] Evidence bundles complete

### Phase 2 (Resolve 51 Inconsistencies)
- [ ] 18 editorial columns reclassified to manual_patch_only
- [ ] 14 inferrable columns have formulas
- [ ] 9 immutable columns set on_create
- [ ] 10 lookup columns implemented
- [ ] Schema validation reports 0 inconsistencies

### Phase 3 (Capability Mapping)
- [ ] Step 3 runs via runtime engine
- [ ] Step 4 applies 796 patches to SSOT
- [ ] `py_capability_tags` populated for 574 files
- [ ] Evidence chains complete

### Phase 4 (Convergent Evidence)
- [ ] Timestamp clusters generated
- [ ] Provenance DB queryable
- [ ] Convergent report shows ≥300 HIGH confidence files

---

## Timeline & Resources

### Phased Execution (2-3 weeks)

| Phase | Duration | Team | Dependencies |
|-------|----------|------|--------------|
| 0: Runtime Engine | 5-7 days | 1 engineer | None |
| 1: File Intake | 3-5 days | 1 engineer | Phase 0 complete |
| 2: Resolve Inconsistencies | 2-4 days | 1 engineer | Phase 0 complete (parallel with Phase 1) |
| 3: Capability Mapping | 1-2 days | 1 engineer | Phase 1 complete |
| 4: Convergent Evidence | 2-3 days | 1 engineer | Phase 1, 3 complete (optional) |

**Total:** 13-21 days (2-3 weeks if serial; 2 weeks if phases 1-2 parallel)

### Critical Path
Phase 0 → Phase 1 → Phase 3 (must be serial)  
Phase 2 can run parallel with Phase 1  
Phase 4 is optional enhancement

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Circular dependencies in formulas | HIGH | Dependency scheduler will detect; fail-fast |
| Performance (185 derivations per file) | MEDIUM | Phase in: run 10 columns first, measure, then scale |
| Mapp_py integration breaks | HIGH | Fallback: run Steps 1-2 separately, join results |
| Registry corruption | CRITICAL | Mandatory backups before any write; schema validation gate |
| 51 inconsistencies grow during resolution | MEDIUM | Lock governance files during Phase 2; version control |

---

## File Manifest (New Scripts Created)

### Phase 0: Runtime Engine (7 files)
- `P_01999000042260305010_column_runtime_loader.py`
- `P_01999000042260305011_dependency_scheduler.py`
- `P_01999000042260305012_trigger_dispatcher.py`
- `P_01999000042260305013_derivation_executor.py`
- `P_01999000042260305014_lookup_resolver.py`
- `P_01999000042260305015_patch_generator.py`
- `P_01999000042260305016_evidence_writer.py`

### Phase 1: File Intake (2 files + 1 from earlier plan)
- `P_01999000042260305020_file_intake_orchestrator.py`
- `P_01999000042260305021_py_column_transformer.py`
- `P_01999000042260305001_file_id_reconciler.py` (reused)

### Phase 2: Governance Updates
- Updated: `WRITE_POLICY.yaml`, `formula_sheet_classification.csv`
- New formulas in `DerivationExecutor`

### Phase 3: Integration
- Modified: `capability_mapper.py` (integrate with runtime)

### Phase 4: Convergent Evidence (1 file)
- `P_01999000042260305003_timestamp_cluster_analyzer.py` (enhanced)

**Total New Scripts:** 11  
**Total Modified Scripts:** 3  
**Total Governance Files Updated:** 2

---

## Appendix: Column Classification Summary

### By Resolution Strategy

| Strategy | Count | Examples |
|----------|-------|----------|
| Reclassify to manual_patch_only | 18 | description, notes, tags |
| Add safe formula with defaults | 14 | status, entity_kind, canonicality |
| Set on_create in constructor | 9 | created_by, record_kind, edge fields |
| Implement lookup layer | 10 | asset_id, external_ref, metadata |
| **Total Resolved** | **51** | |

### By Update Policy (After Resolution)

| Policy | Count | Trigger |
|--------|-------|---------|
| immutable | 25 | on_create_only |
| recompute_on_scan | 78 | every intake |
| recompute_on_build | 15 | post-analysis queue |
| manual_patch_only | 30 | never auto |
| manual_or_automated | 37 | optional auto (py_*) |

---

## Next Steps

### Immediate Actions
1. **Review this plan** with system owner
2. **Approve Phase 0** (foundational, no registry writes)
3. **Allocate 1 engineer for 5-7 days** to build runtime engine

### Week 1 Goals
- Complete Phase 0 (runtime engine)
- Begin Phase 1 (file intake orchestrator)
- Begin Phase 2 (resolve inconsistencies) in parallel

### Week 2 Goals
- Complete Phase 1 (intake tested with 50+ files)
- Complete Phase 2 (all 51 inconsistencies resolved)
- Begin Phase 3 (capability mapping integration)

### Week 3 Goals
- Complete Phase 3 (SSOT updated with capabilities)
- Optional: Complete Phase 4 (convergent evidence)
- Documentation updates
- End-to-end validation

---

**Plan Status:** ✅ READY FOR EVALUATION  
**Supersedes:** PLAN-20260305-CAPABILITY-MAPPING-V1  
**Approval Required:** System Owner + Technical Lead  
**Expected Completion:** 2026-03-19 to 2026-03-26 (2-3 weeks)

---

## Evaluation Checklist

When evaluating this plan, verify:

- [ ] **Unifies three incomplete efforts** (py_* columns + 51 inconsistencies + file intake)
- [ ] **Foundational runtime engine** enforces governance policies
- [ ] **Deterministic automation** with evidence trails
- [ ] **Incremental execution** (phases independent where possible)
- [ ] **Safe rollback** (no registry writes until Phase 1 complete)
- [ ] **Measurable success** (0 inconsistencies, 185 columns governed)
- [ ] **Reuses existing work** (mapp_py, capability Steps 1-2, write policies)
- [ ] **Closes promotion blocker** (file ID reconciliation)
- [ ] **Enables future work** (convergent evidence, multi-signal confidence)

