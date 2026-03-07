# Registry Relationship Columns - Detailed Reference

**Purpose:** Documents every column header that describes how a file relates to other files or to system features/capabilities.
**Source Schema:** `01999000042260124012_governance_registry_schema.v3.json`
**Source Dictionary:** `01260207233100000463_2026012816000001_COLUMN_DICTIONARY.json`
**Registry Data:** `01999000042260124503_REGISTRY_file.json`
**Generated:** 2026-03-05

---

# Part 1: File-to-File Relationship Columns

These columns create a dependency/linkage graph between individual file records. They answer: *"How does this file connect to other files?"*

---

## 1.1 `depends_on_file_ids`

**What it does:** Lists the `file_id` values of every file this entity explicitly depends on. Represents a hard, declared dependency -- if any of these files change, this file may need to be re-evaluated.

**Type:** `array|null` of 20-digit `file_id` strings
**Derivation:** LOOKUP -- resolved from the registry by matching `file_id`
**Scope:** All record kinds

**Codebase example** (`REGISTRY_file.json`, entries section, line ~11217):
```json
{
  "file_id": "01999000042260124056",
  "relative_path": "DOC-REPORT-EXECUTION-SUMMARY-0199900004226012456__EXECUTION_SUMMARY.md",
  "depends_on_file_ids": [],
  "artifact_kind": "MARKDOWN_DOC",
  "layer": "DOCUMENTATION"
}
```
A documentation report with no declared dependencies. When populated, this would look like:
```json
"depends_on_file_ids": ["01999000042260124051", "01999000042260124057"]
```
This means the file cannot be fully understood without the two referenced files.

**Schema constraint:** Each element must match `^[0-9]{20}$`.

---

## 1.2 `source_file_id`

**What it does:** In an edge (relationship) record, identifies the **originator** side of the relationship. This is the file that *does something to* the target.

**Type:** `string|null` (20-digit ID)
**Derivation:** LOOKUP
**Scope:** All record kinds, primarily edges

**Schema definition** (`governance_registry_schema.v3.json`, line ~518):
```json
"EdgeRecord": {
  "properties": {
    "source_file_id": {
      "type": "string",
      "pattern": "^[0-9]{20}$"
    }
  }
}
```

**Conceptual example from the edge schema:**
```json
{
  "source_file_id": "01999000042260125006",
  "edge_type": "VALIDATES",
  "target_file_id": "01999000042260124051"
}
```
Means: *"The validator script (source) VALIDATES the config file (target)."*

---

## 1.3 `target_file_id`

**What it does:** In an edge record, identifies the **recipient** side of the relationship -- the file being acted upon.

**Type:** `string|null` (20-digit ID)
**Derivation:** LOOKUP
**Scope:** All record kinds, primarily edges

**Schema definition** (`governance_registry_schema.v3.json`, line ~542):
```json
"target_file_id": {
  "type": "string",
  "pattern": "^[0-9]{20}$"
}
```

See the `source_file_id` example above -- `source_file_id` and `target_file_id` always appear as a pair on edge records to define who does what to whom.

---

## 1.4 `source_entity_id`

**What it does:** Like `source_file_id`, but uses the internal `entity_id` instead of `file_id`. Used when the source of an edge is a non-file entity (e.g., a generator, a transient record, or an external reference).

**Type:** `string|null`
**Derivation:** LOOKUP (from `INPUT.source_entity_id`)
**Scope:** entity, edge records

**Derivation formula** (`UNIFIED_SSOT_REGISTRY_DERIVATIONS.corrected.v1.0.0.json`, line ~1395):
```json
{
  "source_entity_id": {
    "formula": "INPUT.source_entity_id",
    "rationale": "Source entity reference",
    "trigger": "on_create_only"
  }
}
```

---

## 1.5 `target_entity_id`

**What it does:** The counterpart to `source_entity_id` -- identifies the target of an edge using entity_id. Used when the target is not a simple file.

**Type:** `string|null`
**Derivation:** LOOKUP
**Scope:** edge records (CONDITIONAL -- required when record_kind is "edge")

---

## 1.6 `anchor_file_id`

**What it does:** Points to the `file_id` of the "anchor" or primary key file for a parent record/document context. For bundle groupings, this is the SSOT/schema file that everything else in the bundle is defined relative to.

**Type:** `string|null` (20-digit ID)
**Derivation:** LOOKUP
**Scope:** All record kinds

**Codebase example** (`REGISTRY_file.json`, entries section, line ~11184):
```json
{
  "file_id": "01999000042260124051",
  "relative_path": "DOC-CONFIG-PRE-COMMIT-0199900004226012451__.pre-commit-config.yaml",
  "anchor_file_id": "01999000042260124051",
  "bundle_key": "PRE-COMMIT-0199900004226012451_MODULE",
  "bundle_role": null
}
```
Here `anchor_file_id` equals its own `file_id` -- this file IS the anchor for its bundle. Other files in the same bundle would reference this anchor to indicate they are subordinate to it.

---

## 1.7 `generated_by_file_id`

**What it does:** If this file was auto-generated (not hand-written), this points to the `file_id` of the generator script that produced it.

**Type:** `string|null` (20-digit ID)
**Derivation:** LOOKUP
**Scope:** All record kinds

**Schema definition** (`governance_registry_schema.v3.json`, line ~325):
```json
"generated_by_file_id": {
  "type": "string",
  "pattern": "^[0-9]{20}$",
  "description": "file_id of generator source (if is_generated=true)"
}
```

**Conceptual example:**
```json
{
  "file_id": "00020260130170000003",
  "relative_path": ".state/evidence/final/determinism_score.json",
  "is_generated": true,
  "generated_by_file_id": "01999000042260125007"
}
```
Means: *"The determinism_score.json evidence artifact was produced by the runner script."*

---

## 1.8 `test_file_ids`

**What it does:** Lists all `file_id` values of test files that test/validate this entity. Creates a direct link from production code to its test coverage.

**Type:** `array|null` of 20-digit strings
**Derivation:** LOOKUP via `LOOKUP_REGISTRY('tests_for', file_id, relative_path)`
**Scope:** All record kinds

**Codebase example** (`REGISTRY_file.json`, entries section, line ~11218):
```json
{
  "file_id": "01999000042260124056",
  "relative_path": "DOC-REPORT-EXECUTION-SUMMARY-0199900004226012456__EXECUTION_SUMMARY.md",
  "test_file_ids": [],
  "has_tests": false
}
```
Empty array with `has_tests: false` -- this report has no tests. When populated:
```json
"test_file_ids": ["01999000042260125050", "01999000042260125051"]
```

---

## 1.9 `enforced_by_file_ids`

**What it does:** Lists the `file_id` values of validator/runner/gate scripts that enforce rules on this file. This is the inverse of `enforces_rule_ids` -- it points *upward* to enforcers.

**Type:** `array|null` of 20-digit strings
**Derivation:** LOOKUP
**Scope:** All record kinds

**Codebase example** (`REGISTRY_file.json`, entries section, line ~11185):
```json
{
  "file_id": "01999000042260124051",
  "relative_path": "DOC-CONFIG-PRE-COMMIT-0199900004226012451__.pre-commit-config.yaml",
  "enforced_by_file_ids": []
}
```
When populated, this means specific validator scripts check this file for correctness:
```json
"enforced_by_file_ids": ["01999000042260125006"]
```

---

## 1.10 `superseded_by`

**What it does:** When a file has been replaced by a newer version, this field points to the `file_id` of the replacement. Creates a version lineage chain. Files with this field populated typically have `canonicality: "SUPERSEDED"`.

**Type:** `string|null` (20-digit ID)
**Derivation:** INPUT
**Scope:** All record kinds

**Codebase example** (`REGISTRY_file.json`, line ~12300):
```json
{
  "file_id": "01999000042260125192",
  "relative_path": "src/repo_autoops/automation_descriptor/01999000042260125192___init__.py",
  "superseded_by": "01999000042260125003",
  "canonicality": "SUPERSEDED"
}
```
Means: *"This __init__.py has been replaced by file 01999000042260125003. Use that one instead."*

---

## 1.11 `supersedes_entity_id`

**What it does:** The inverse of `superseded_by` -- this field, on the *newer* record, points back to the entity_id of the record it replaced.

**Type:** `string|null`
**Derivation:** `COALESCE(INPUT.supersedes_entity_id, NULL)` -- user-supplied at record creation
**Scope:** entity records

Together with `superseded_by`, these two columns create a bidirectional version lineage:
```
File A (old) --superseded_by--> File B (new)
File B (new) --supersedes_entity_id--> File A (old)
```

---

## 1.12 `py_overlap_best_match_file_id`

**What it does:** When the Python analysis pipeline detects that this file is substantially similar to another file (potential duplicate/refactor candidate), this points to the `file_id` of the best match.

**Type:** `string|null` (20-digit ID)
**Derivation:** DERIVED from Python analysis pipeline output
**Scope:** entity:file (Python files only)

**Used in conjunction with:**
- `py_overlap_similarity_max` -- the similarity score (0.0-1.0)
- `py_overlap_group_id` -- groups all overlapping files together

**Conceptual example:**
```json
{
  "file_id": "01999000042260125004",
  "filename": "audit_logger.py",
  "py_overlap_best_match_file_id": "01999000042260125192",
  "py_overlap_similarity_max": 0.87,
  "py_overlap_group_id": "OVL-GROUP-0042"
}
```

---

## 1.13 `py_overlap_group_id`

**What it does:** Groups files that overlap with each other into a single cluster ID. All files in the same overlap group share a group_id, making it easy to find all near-duplicates as a set.

**Type:** `string|null`
**Derivation:** DERIVED from Python analysis pipeline
**Scope:** entity:file

---

## 1.14 `py_imports_local`

**What it does:** Lists local/project import statements found in a Python file. These represent *implicit* file-to-file dependencies discoverable through static analysis.

**Type:** `array|null`
**Derivation:** DERIVED from AST parsing via `INPUT.facts.imports.local`
**Scope:** entity:file (Python files only)

**Derivation formula** (`UNIFIED_SSOT_REGISTRY_DERIVATIONS`, line ~1669):
```json
{
  "py_imports_local": {
    "formula": "INPUT.facts.imports.local",
    "rationale": "Local import list from facts"
  }
}
```

**Conceptual example:**
```json
{
  "file_id": "01999000042260125004",
  "filename": "audit_logger.py",
  "py_imports_local": [
    "automation_descriptor.config",
    "automation_descriptor.evidence_writer"
  ]
}
```
Each import string maps to another Python file in the project -- resolving these to file_ids creates the import dependency graph.

---

# Part 2: Edge Relationship Qualifiers

Edge records are standalone relationship objects stored in the `edges` array of the registry. They connect two entities and describe the nature of their relationship.

---

## 2.1 `edge_type`

**What it does:** The primary classifier for what kind of relationship exists between source and target. Drawn from a fixed enumeration.

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** All record kinds
**Normalization:** UPPERCASE

**Allowed values** (from `governance_registry_schema.v3.json`, line ~524):

| Value | Meaning |
|-------|---------|
| `VALIDATES` | Source validates/checks the target |
| `EXECUTES` | Source executes/runs the target |
| `ENFORCES` | Source enforces rules on the target |
| `USES_SCHEMA` | Source uses the target as its schema definition |
| `GENERATES` | Source generates the target as output |
| `DEPENDS_ON` | Source depends on the target |
| `TESTS` | Source is a test for the target |
| `DOCUMENTS` | Source documents the target |
| `EMITS_EVENT` | Source emits events consumed by the target |
| `COLLECTS_EVIDENCE` | Source collects evidence about the target |
| `PRODUCES_REPORT` | Source produces a report about the target |
| `DERIVES` | Source is derived from the target |
| `PATCHES` | Source patches/modifies the target |
| `ATTESTS` | Source attests to properties of the target |
| `EMITS_EVIDENCE_FOR` | Source emits evidence artifacts for the target |

**Example edge record:**
```json
{
  "source_file_id": "01999000042260125006",
  "edge_type": "VALIDATES",
  "target_file_id": "01999000042260124051",
  "target_schema_id": "1000000000000002"
}
```
*"The validate_evidence_schema.py script VALIDATES the pre-commit config."*

---

## 2.2 `rel_type`

**What it does:** Legacy/backward-compatible mirror of `edge_type`. In the current schema, `rel_type` always equals `edge_type`.

**Type:** `string|null`
**Derivation:** `COALESCE(edge_type, NULL)` -- derived from edge_type
**Scope:** edge records
**Normalization:** UPPERCASE

**From derivation spec** (line ~1340):
```json
{
  "rel_type": {
    "formula": "COALESCE(edge_type, NULL)",
    "rationale": "Relationship type identifier",
    "notes": "Deprecated: canonical field is edge_type; rel_type mirrors edge_type for backward compatibility."
  }
}
```

---

## 2.3 `directionality`

**What it does:** Explicitly declares the direction of the relationship. Most edges are unidirectional (source acts on target), but some may be bidirectional.

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** edge records (CONDITIONAL)
**Normalization:** LOWERCASE

**Typical values:** `"unidirectional"`, `"bidirectional"`

---

## 2.4 `confidence`

**What it does:** A numeric score (0.0 to 1.0) indicating how confident the system is that this edge relationship actually exists. Useful for edges inferred by automated analysis rather than declared manually.

**Type:** `number|null`
**Derivation:** INPUT
**Scope:** edge records (CONDITIONAL)

**Example:**
```json
{
  "source_file_id": "01999000042260125004",
  "edge_type": "DEPENDS_ON",
  "target_file_id": "01999000042260125192",
  "confidence": 0.85,
  "edge_flags": ["inferred"]
}
```
An inferred dependency with 85% confidence -- detected by import analysis but not manually verified.

---

## 2.5 `edge_flags`

**What it does:** Array of markers that qualify how the edge was created or its reliability. Enables filtering edges by provenance.

**Type:** `array|null`
**Derivation:** INPUT
**Scope:** edge records

**Common flag values:**
- `"inferred"` -- relationship detected automatically
- `"manual"` -- relationship declared by a human
- `"low_confidence"` -- automated detection was uncertain
- `"high_confidence"` -- strong signal from multiple sources

---

## 2.6 `edges`

**What it does:** A top-level array on the registry file that contains all edge (relationship) records. Each element is an `EdgeRecord` object with `source_file_id`, `edge_type`, `target_file_id`, and optional qualifiers.

**Type:** `array|null`
**Derivation:** INPUT
**Scope:** All record kinds (top-level registry structure)

**Codebase example** (`REGISTRY_file.json`, line ~34417):
```json
"edges": []
```
Currently empty in the live registry -- edges are defined in the schema but not yet populated with data. The schema (`governance_registry_schema.v3.json`) requires both `"files"` and `"edges"` arrays at the top level.

---

# Part 3: File-to-System Feature Columns

These columns describe how a file participates in the governance system's organizational taxonomy -- its role, domain, process stage, and functional classification.

---

## 3.1 `function_code_1`, `function_code_2`, `function_code_3`

**What they do:** Three-tier functional classification codes from the project's taxonomy. They categorize *what a file does* at increasing levels of specificity.

**Type:** `string|null` each
**Derivation:** INPUT (manually assigned)
**Scope:** entity:file

**From column dictionary:**
- `function_code_1` -- Broadest classification (e.g., "GOVERNANCE", "INFRASTRUCTURE")
- `function_code_2` -- Mid-level (e.g., "VALIDATION", "CONFIGURATION")
- `function_code_3` -- Most specific (e.g., "SCHEMA_VALIDATION", "PRE_COMMIT_HOOKS")

**Conceptual example:**
```json
{
  "file_id": "01999000042260125006",
  "filename": "validate_evidence_schema.py",
  "function_code_1": "GOVERNANCE",
  "function_code_2": "VALIDATION",
  "function_code_3": "SCHEMA_VALIDATION"
}
```

---

## 3.2 `geu_ids`

**What it does:** Lists all Governance Enforcement Unit (GEU) IDs this file participates in. A GEU is a logical grouping of files that together enforce a governance rule (schema + validator + runner + tests + evidence).

**Type:** `array|null`
**Derivation:** LOOKUP from `governance/geu_registry.json`
**Scope:** entity:file

**Codebase example** (`REGISTRY_file.json`, entries section, line ~32019):
```json
{
  "file_id": "01999000042260125006",
  "relative_path": "DOC-SCRIPT-0993__PROV-SOL_validate_evidence_schema.py",
  "geu_ids": ["99990000000000000002"],
  "geu_role": "VALIDATOR",
  "primary_geu_id": "99990000000000000002"
}
```
This validator script belongs to GEU `99990000000000000002`.

---

## 3.3 `geu_role`

**What it does:** Defines the specific role this file plays within its GEU. Each GEU type has required and optional role slots.

**Type:** `string|null`
**Derivation:** LOOKUP from GEU registry
**Scope:** entity:file (CONDITIONAL -- required when geu_ids is non-empty)
**Normalization:** UPPERCASE

**Allowed values** (from `geu_role_definitions` in `REGISTRY_file.json`, line ~193):

| Role | Description |
|------|-------------|
| `SCHEMA` | Formal definition of allowed structure. Registered and versioned. |
| `RULE` | SSOT definition or policy describing an invariant or lifecycle rule. |
| `VALIDATOR` | Code enforcing semantic rules beyond schema (cross-field constraints, uniqueness). |
| `RUNNER` | Gate orchestrator that invokes validators, checks schemas, enforces failure modes. |
| `FAILURE_MODE` | Declarative definition of failure classes and actions (block, warn, info). |
| `EVIDENCE` | Definitions/schemas for logs, diffs, manifests produced during execution. |
| `TEST` | Automated tests verifying the GEU. |
| `REPORT` | Scripts/templates producing human-readable reports from evidence. |

**Codebase examples** (`REGISTRY_file.json`, entries):
```json
// Validator
{
  "file_id": "01999000042260125006",
  "geu_role": "VALIDATOR",
  "geu_ids": ["99990000000000000002"]
}

// Runner
{
  "file_id": "01999000042260125007",
  "relative_path": "automation/test_runner/DOC-TEST-TEST-RUNNER-RUNNER-524__runner.py",
  "geu_role": "RUNNER",
  "geu_ids": ["99990000000000000002"]
}

// Rule
{
  "file_id": "01999000042260125008",
  "relative_path": "data/DOC-CONFIG-ID-REGISTRY-435__id_registry.json",
  "geu_role": "RULE",
  "geu_ids": ["99990000000000000004"]
}
```

---

## 3.4 `primary_geu_id`

**What it does:** The single primary GEU assignment for this file. When a file belongs to multiple GEUs, this identifies the main one.

**Type:** `string|null`
**Derivation:** LOOKUP
**Scope:** entity:file (CONDITIONAL)

**Codebase example** (`REGISTRY_file.json`, line ~32025):
```json
{
  "file_id": "01999000042260125006",
  "primary_geu_id": "99990000000000000002",
  "geu_ids": ["99990000000000000002"]
}
```

---

## 3.5 `owner_geu_id`

**What it does:** The GEU that "owns" this file. Differs from `primary_geu_id` when a shared file is used across GEUs -- `owner_geu_id` identifies who is ultimately responsible for it.

**Type:** `string|null`
**Derivation:** `COALESCE(primary_geu_id, LOOKUP_CONFIG('default_geu_by_path', relative_path))`
**Scope:** entity:file (CONDITIONAL)

Falls back to path-based lookup if no explicit `primary_geu_id` is set.

**Codebase example** (`REGISTRY_file.json`, entries section, line ~11178):
```json
{
  "file_id": "01999000042260124051",
  "owner_geu_id": null,
  "primary_geu_id": null,
  "is_shared": false
}
```
Null values indicate this file hasn't been assigned to a GEU yet.

---

## 3.6 `governance_domain`

**What it does:** Categorizes the file into a high-level governance subsystem. This is the broadest organizational classification.

**Type:** `string|null`
**Derivation:** LOOKUP from GEU registry
**Scope:** entity:file

**Allowed values** (from `governance_registry_schema.v3.json`, line ~55):

| Domain | Description |
|--------|-------------|
| `ROOT` | Repository root-level files |
| `CONFIGS` | Configuration files |
| `SCHEMAS` | Schema definitions |
| `REGISTRY` | Registry system files |
| `TASKS` | Task/work-unit files |
| `REMEDIES` | Remediation plans |
| `SRC` | Source code |
| `TESTS` | Test files |
| `EVIDENCE` | Evidence artifacts |
| `REPORTS` | Report outputs |
| `ARTIFACTS` | Build/generated artifacts |
| `EXTERNAL` | External references |

**Codebase examples** (`REGISTRY_file.json`, entries section):
```json
// Configuration file
{
  "file_id": "01999000042260124051",
  "governance_domain": "CONFIGS"
}

// Report file
{
  "file_id": "01999000042260124056",
  "governance_domain": "REPORTS"
}

// Root-level file
{
  "file_id": "01999000042260124060",
  "governance_domain": "ROOT"
}

// Evidence artifact
{
  "file_id": "01999000042260124065",
  "governance_domain": "EVIDENCE"
}
```

---

## 3.7 `module_id`

**What it does:** Assigns the file to a specific module within the project. Modules are logical groupings of related functionality (e.g., all files that make up the ID allocator).

**Type:** `string|null`
**Derivation:** LOOKUP
**Scope:** entity:file
**Normalization:** UPPERCASE

**Related columns:**
- `module_id_override` -- manual override if the inferred module is wrong
- `module_id_source` -- tracks whether the assignment came from `"rule"`, `"override"`, or `"inferred"`

---

## 3.8 `process_id`

**What it does:** Links the file to a phase/workstream process. Identifies *which process workflow* this file is part of.

**Type:** `string|null`
**Derivation:** `LOOKUP_CONFIG('process_by_path', relative_path)`
**Scope:** entity:file

**Derivation formula** (`UNIFIED_SSOT_REGISTRY_DERIVATIONS`, line ~297):
```json
{
  "process_id": {
    "depends_on": ["relative_path"],
    "formula": "LOOKUP_CONFIG('process_by_path', relative_path)",
    "rationale": "Associated process"
  }
}
```

**Conceptual example:**
```json
{
  "file_id": "01999000042260125004",
  "relative_path": "newPhasePlanProcess/scripts/gate_runner.py",
  "process_id": "NPP_GATE_PROCESS"
}
```

---

## 3.9 `process_step_id`

**What it does:** Within a process, identifies the specific step this file is associated with. More granular than `process_id`.

**Type:** `string|null`
**Derivation:** LOOKUP
**Scope:** entity:file

**Conceptual example:**
```json
{
  "process_id": "NPP_GATE_PROCESS",
  "process_step_id": "STEP_03_VALIDATE",
  "process_step_role": "EXECUTOR"
}
```

---

## 3.10 `process_step_role`

**What it does:** Defines what role this file plays within a specific process step (e.g., input, executor, output, gatekeeper).

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** entity:file

---

## 3.11 `step_refs`

**What it does:** Array of references to phase/workstream/gate steps linked to this file. Unlike `process_step_id` (which is a single step), `step_refs` can link a file to multiple steps.

**Type:** `array|null`
**Derivation:** INPUT
**Scope:** entity:file

**Conceptual example:**
```json
{
  "file_id": "01999000042260125006",
  "filename": "validate_evidence_schema.py",
  "step_refs": ["PH-00-VALIDATE", "PH-01-EVIDENCE-CHECK"]
}
```
This validator is used in two different phase steps.

---

## 3.12 `contracts_consumed`

**What it does:** Lists the contracts/specifications this file takes as input. A "contract" is a formal spec or schema that defines expected structure.

**Type:** `array|null`
**Derivation:** `LOOKUP_REGISTRY('contracts_consumed_by', file_id)`
**Scope:** entity:file

**Derivation formula** (line ~1425):
```json
{
  "contracts_consumed": {
    "formula": "LOOKUP_REGISTRY('contracts_consumed_by', file_id)",
    "rationale": "Contracts this file consumes"
  }
}
```

**Conceptual example:**
```json
{
  "file_id": "01999000042260125006",
  "filename": "validate_evidence_schema.py",
  "contracts_consumed": [
    "EVIDENCE_SCHEMA_v1.0.0",
    "REGISTRY_RECORD_SCHEMA_v4.0"
  ]
}
```
This validator consumes two contract schemas as its validation baseline.

---

## 3.13 `contracts_produced`

**What it does:** Lists the contracts/specifications this file produces as output. The inverse of `contracts_consumed`.

**Type:** `array|null`
**Derivation:** `LOOKUP_REGISTRY('contracts_produced_by', file_id)`
**Scope:** entity:file

**Derivation formula** (line ~1271):
```json
{
  "contracts_produced": {
    "formula": "LOOKUP_REGISTRY('contracts_produced_by', file_id)",
    "rationale": "Contracts this file produces"
  }
}
```

---

## 3.14 `enforces`

**What it does:** Human-readable description of what rules or controls this file enforces. This is the descriptive counterpart to `enforces_rule_ids`.

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** All record kinds

**Schema definition** (`governance_registry_schema.v3.json`, line ~205):
```json
"enforces": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Rules or controls enforced"
}
```

---

## 3.15 `enforces_rule_ids`

**What it does:** Lists the formal rule IDs that this file enforces. These are machine-readable identifiers that map to specific governance rules.

**Type:** `array|null`
**Derivation:** LOOKUP
**Scope:** All record kinds

**Codebase example** (`REGISTRY_file.json`, entries, line ~11186):
```json
{
  "file_id": "01999000042260124051",
  "enforces_rule_ids": []
}
```
When populated:
```json
"enforces_rule_ids": ["RULE-ID-001", "RULE-ID-042"]
```

---

## 3.16 `py_capability_tags`

**What it does:** Tags extracted from Python source code analysis that describe what capabilities the file provides. These are structured identifiers from the capability mapping pipeline.

**Type:** `array|null`
**Derivation:** DERIVED from Python analysis pipeline
**Scope:** entity:file (Python files)

**Codebase examples** (`REGISTRY_file.json`, files array):
```json
// Gate marker detected (high confidence)
{
  "file_id": "00020260130170000017",
  "relative_path": ".state/evidence/gates/gate_109.json",
  "one_line_purpose": "CAP-GATE-109-GATE_109: Gate 109",
  "py_capability_tags": ["CAP-GATE-109-GATE_109"],
  "notes": "capmap:confidence=high; justification=gate marker detected"
}

// Schema file (high confidence)
{
  "file_id": "00020260130170000490",
  "py_capability_tags": ["CAP-SCHEMA-AUTONOMOUS_DELIVERY_PLAN_V2_4_0"],
  "notes": "capmap:confidence=high; justification=schema file"
}

// No capability detected (low confidence)
{
  "file_id": "01999000042260124506",
  "py_capability_tags": [],
  "notes": "capmap:confidence=low; justification=no deterministic mapping rule"
}
```

---

## 3.17 `py_deliverable_kinds`

**What it does:** Classifies what kind of deliverables a Python file produces (e.g., reports, evidence artifacts, transformed data).

**Type:** `array|null`
**Derivation:** DERIVED from Python analysis pipeline
**Scope:** entity:file

---

## 3.18 `bundle_key`

**What it does:** Human-readable stable name that groups related files into a "bundle" -- a logical package of files that work together.

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** entity:file
**Normalization:** UPPERCASE

**Codebase examples** (`REGISTRY_file.json`, entries):
```json
// Config module bundle
{
  "file_id": "01999000042260124051",
  "bundle_key": "PRE-COMMIT-0199900004226012451_MODULE",
  "bundle_id": "1000000000000002"
}

// Documentation bundle
{
  "file_id": "01999000042260124056",
  "bundle_key": "DOCUMENTATION_BUNDLE",
  "bundle_id": "1000000000000026"
}
```

---

## 3.19 `bundle_role`

**What it does:** Defines the role this file plays within its bundle. Uses the same role vocabulary as GEU roles.

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** entity:file (CONDITIONAL -- required when bundle_key is set)
**Normalization:** UPPERCASE

**Allowed values** (from schema, line ~150): `SCHEMA`, `VALIDATOR`, `EXECUTOR`, `RUNNER`, `BRIDGE`, `TEST`, `DOC`, `REPORT`, `TOOL`, `FAILURE_MODE`, `EVIDENCE_SCHEMA`

**Codebase examples** (`REGISTRY_file.json`, entries):
```json
// Report within documentation bundle
{
  "file_id": "01999000042260124056",
  "bundle_key": "DOCUMENTATION_BUNDLE",
  "bundle_role": "REPORT"
}

// Validator in its GEU
{
  "file_id": "01999000042260125006",
  "geu_role": "VALIDATOR",
  "bundle_role": "VALIDATOR"
}

// Runner in its GEU
{
  "file_id": "01999000042260125007",
  "geu_role": "RUNNER",
  "bundle_role": "RUNNER"
}
```

---

## 3.20 `role` / `role_code`

**What they do:** General-purpose role labels from the project taxonomy. Less structured than `geu_role` or `bundle_role` -- these are freeform labels.

**Type:** `string|null` each
**Derivation:** INPUT
**Scope:** entity:file
**Normalization:** LOWERCASE

- `role` -- Human-readable label (e.g., `"validator"`, `"config"`, `"report"`)
- `role_code` -- Short code version (e.g., `"VAL"`, `"CFG"`, `"RPT"`)

---

## 3.21 `layer`

**What it does:** Classifies the file into an architecture layer -- where it sits in the logical stack of the system.

**Type:** `string|null`
**Derivation:** INPUT
**Scope:** All record kinds

**Allowed values** (from schema, line ~96):

| Layer | Description |
|-------|-------------|
| `CONFIGURATION` | Config files (YAML, JSON settings) |
| `DEFINITION` | Formal definitions (schemas, contracts) |
| `TEMPLATE` | Templates for generating artifacts |
| `EXAMPLE` | Example/sample files |
| `EXECUTION` | Executable scripts, runners |
| `VALIDATION` | Validators, checkers |
| `CORE` | Core system logic |
| `TRACE` | Tracing/logging infrastructure |
| `DAG` | DAG (directed acyclic graph) definitions |
| `UTIL` | Utility/helper code |
| `ERROR_HANDLING` | Error handling logic |
| `REPORTING` | Report generation |
| `TESTING` | Test infrastructure |
| `EVIDENCE` | Evidence collection/storage |
| `PERSISTENCE` | Data persistence |
| `GOVERNANCE` | Governance enforcement |
| `SSOT` | Single source of truth records |
| `GATES` | Gate/checkpoint definitions |
| `EVENTS` | Event system |
| `PACKAGE_MARKER` | Package markers (`__init__.py`) |
| `DOCUMENTATION` | Documentation files |
| `DERIVED` | Auto-generated/derived content |

**Codebase examples** (`REGISTRY_file.json`, entries):
```json
// Executable config
{
  "file_id": "01999000042260124051",
  "layer": "EXECUTION",
  "artifact_kind": "YAML_DATA"
}

// Documentation
{
  "file_id": "01999000042260124056",
  "layer": "DOCUMENTATION",
  "artifact_kind": "MARKDOWN_DOC"
}

// Validation script
{
  "file_id": "01999000042260125006",
  "layer": "VALIDATION",
  "artifact_kind": "PYTHON_MODULE"
}

// Testing
{
  "file_id": "01999000042260125007",
  "layer": "TESTING",
  "artifact_kind": "PYTHON_MODULE"
}

// Core data
{
  "file_id": "01999000042260125008",
  "layer": "CORE",
  "artifact_kind": "JSON_CONFIG"
}
```

---

# Part 4: GEU Type Slot Matrix

The `geu_type_slot_matrix` defines which roles are required vs. optional for each GEU type. This determines whether a GEU is "complete" or has coverage gaps.

**From `REGISTRY_file.json`, line ~202:**

| GEU Type | Required Roles | Optional Roles |
|----------|---------------|----------------|
| `schema_based` | SCHEMA, VALIDATOR, RUNNER, FAILURE_MODE, EVIDENCE, TEST | RULE, REPORT |
| `rule_based` | RULE, VALIDATOR, RUNNER, FAILURE_MODE, EVIDENCE, TEST | SCHEMA, REPORT |
| `runner_based` | RUNNER, VALIDATOR, FAILURE_MODE, EVIDENCE, TEST | SCHEMA, RULE, REPORT |
| `data_transformation` | SCHEMA, VALIDATOR, RUNNER, FAILURE_MODE, EVIDENCE, TEST | RULE, REPORT |
| `evidence_only` | EVIDENCE, FAILURE_MODE, REPORT | SCHEMA, RULE, VALIDATOR, RUNNER, TEST |

---

# Part 5: How These Columns Work Together

## Example: Complete file record with all relationship columns

```json
{
  "file_id": "01999000042260125006",
  "relative_path": "DOC-SCRIPT-0993__PROV-SOL_validate_evidence_schema.py",
  "record_kind": "entity",
  "entity_kind": "file",

  // ---- File-to-File Relationships ----
  "depends_on_file_ids": ["01999000042260125008"],
  "test_file_ids": ["01999000042260125050"],
  "enforced_by_file_ids": [],
  "anchor_file_id": "01999000042260125008",
  "generated_by_file_id": null,
  "superseded_by": null,

  // ---- System Feature Assignment ----
  "governance_domain": "SRC",
  "layer": "VALIDATION",
  "artifact_kind": "PYTHON_MODULE",
  "geu_ids": ["99990000000000000002"],
  "geu_role": "VALIDATOR",
  "primary_geu_id": "99990000000000000002",
  "owner_geu_id": "99990000000000000002",
  "bundle_key": "EVIDENCE_VALIDATION_BUNDLE",
  "bundle_role": "VALIDATOR",

  // ---- Contracts ----
  "contracts_consumed": ["EVIDENCE_SCHEMA_v1.0.0"],
  "contracts_produced": [],
  "enforces_rule_ids": ["RULE-EVIDENCE-001"],

  // ---- Python Analysis ----
  "py_capability_tags": ["CAP-VALIDATOR-EVIDENCE"],
  "py_imports_local": ["automation_descriptor.config"],
  "has_tests": true
}
```

## Example: Edge record linking two files

```json
{
  "record_kind": "edge",
  "edge_id": "EDGE-20260130-0001",
  "source_file_id": "01999000042260125006",
  "target_file_id": "01999000042260125008",
  "edge_type": "VALIDATES",
  "rel_type": "VALIDATES",
  "directionality": "unidirectional",
  "confidence": 1.0,
  "edge_flags": ["manual"],
  "evidence_method": "manual",
  "observed_utc": "2026-01-30T16:35:03Z"
}
```

This edge says: *"validate_evidence_schema.py (source) VALIDATES id_registry.json (target), manually confirmed with 100% confidence."*
