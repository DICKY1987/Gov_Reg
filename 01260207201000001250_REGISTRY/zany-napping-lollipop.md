# Rewrite Package Correction Plan
## Template: NEWPHASEPLANPROCESS v3.0.0
## Plan ID: FIX-REG-AUTO-2026-03-08

> **SCOPE BOUNDARY**: This plan corrects the *rewrite delivery package* (`01260207201000001250_REGISTRY`).
> It does **not** address runtime system defects (pipeline runner, file-id promotion, defaults/null handling, etc.).
> A separate **Runtime Completion Plan** is required for those. See Section 16.

---

## SECTION 1: template_metadata

```json
{
  "template_version": "3.0.0",
  "plan_id": "FIX-REG-AUTO-2026-03-08",
  "plan_title": "Rewrite Package Correction Plan",
  "plan_scope": "delivery-package-correction",
  "source_delivery": "01260207201000001250_REGISTRY",
  "created": "2026-03-08",
  "author": "Claude Code",
  "status": "PLANNED",
  "phase_count": 10,
  "step_count": 12,
  "gate_count": 10
}
```

---

## SECTION 2: critical_constraint

**NO_IMPLIED_BEHAVIOR**: Every fix must be expressed as an explicit file edit with:
- Exact file path
- Exact line(s) changed
- Before/after diff
- Evidence file written on completion
- Gate criterion that verifies the change

No fix is complete without a passing gate. No gate passes without evidence files. No evidence without grep/file-check commands that return deterministic output.

---

## SECTION 3: task_analysis

### Root Cause Summary

The delivery `01260207201000001250_REGISTRY` contains 10 correctness defects introduced across three development sessions (14:xx, 17:xx, 19:xx UTC). The defects fall into three categories:

| Category | Count | Risk |
|---|---|---|
| Stale literal values (wrong field counts, wrong step counts) | 12 occurrences across 9 files | High — causes automated validators to trust wrong numbers |
| Structural incompleteness (gates_spec has 2/6 gates, remediation_plan has 0 work packages) | 2 files | Critical — plan cannot execute |
| Environmental coupling (hardcoded absolute paths, 14 missing scripts with no marker) | 16 locations | High — breaks portability and transparency |
| Epistemic defect (self-validation circularity) | 1 methodology gap | Medium — undermines acceptance proof |

### Issues Catalog

| ID | File | Defect | Priority |
|---|---|---|---|
| FIX-001 | `.state/complete_phase_step_gate_contracts.json` (3 locations) | `"11 required fields"` should be `"12"` | High |
| FIX-002 | 9 documents across delivery | Step count reported as `"12+"` or `"14"` or `"19"` instead of canonical `18` | High |
| FIX-003 | `.state/complete_phase_step_gate_contracts.json` (2 locations) | Hardcoded path `C:\\Users\\richg\\Gov_Reg\\newPhasePlanProcess\\...` | High |
| FIX-004 | `.state/complete_phase_step_gate_contracts.json` (14 gate/step commands) | Scripts referenced but not created; no `[NOT_IMPLEMENTED]` marker | Medium |
| FIX-005 | `.state/gates/gates_spec.json` | Only GATE-001 and GATE-002 present; total_gates claims 6 | Critical |
| FIX-006 | `.state/remediation/remediation_plan.json` | `work_packages: []`; only waves 1-3 defined; claims 19 packages / 73 tasks | Critical |
| FIX-007 | `COMPLETION_CERTIFICATE.txt`, `README.md`, `EXECUTION_COMPLETE.md` | Certification language claims full completion; checklist items unchecked | Medium |
| FIX-008 | `FINAL_VALIDATION_REPORT.md`, `ACCEPTANCE_VALIDATION_REPORT.md` | No disclosure of self-validation circularity in methodology | Medium |
| FIX-009 | `INDEX.md` | 8 wrong size entries; `REMEDIATION_PLAN_SUMMARY.md` phantom reference; 9 rewrite-package files missing from index; wrong template path | High |
| FIX-010 | `VERIFICATION_MANIFEST.json` | 4 files present on disk post-manifest-creation not recorded: `COMPLETION_CERTIFICATE.txt`, `REG_AUTO_PLAN.txt`, `ChatGPT-Automation Alignment Assessment.md`, `zany-napping-lollipop.md` | Medium |

---

## SECTION 4: assumptions_scope

```json
{
  "assumptions": [
    "Canonical step count = 18 (source: .state/complete_phase_step_gate_contracts.json, which has 18 step entries)",
    "Canonical column count = 12 (source: CONTRACT_GAP_MATRIX.md header row)",
    "Script placeholders are acceptable deliverables; actual implementation is out of scope for this fix plan",
    "Hardcoded paths replaced with repo-relative paths",
    "Work packages in remediation_plan.json will be populated with correct structure even if task detail is minimal",
    "All 10 gates (GATE-FIX-001 through GATE-FIX-010) can reference placeholder scripts if scripts are marked [NOT_IMPLEMENTED]",
    "Self-validation disclosure requires a methodology note added to validation reports, not a re-execution"
  ],
  "out_of_scope": [
    "Implementing the 14 referenced scripts (pipeline_runner.py fixes, etc.)",
    "Rewriting REG_AUTO_PLAN.txt",
    "Changing the Contract-Gap Matrix content",
    "Modifying ProgramSpec mappings"
  ],
  "file_root": "01260207201000001250_REGISTRY",
  "state_root": "01260207201000001250_REGISTRY/.state"
}
```

---

## SECTION 5: file_manifest

### Files to Modify (FIX-001 through FIX-008)

| File | Issues | Change Type |
|---|---|---|
| `.state/complete_phase_step_gate_contracts.json` | FIX-001, FIX-003, FIX-004 | String replacements (field count, paths, markers) |
| `.state/gates/gates_spec.json` | FIX-005 | Add GATE-003 through GATE-006; fix step_id references |
| `.state/remediation/remediation_plan.json` | FIX-006 | Add waves 4-6; populate work_packages array |
| `COMPLETION_CERTIFICATE.txt` | FIX-007 | Update step count; add caveats section |
| `README.md` | FIX-002, FIX-007 | Replace "12+" with "18" |
| `EXECUTION_COMPLETE.md` | FIX-002, FIX-007 | Replace "12+" with "18" |
| `INDEX.md` | FIX-002 | Replace "12+" with "18" |
| `FINAL_VALIDATION_REPORT.md` | FIX-002, FIX-008 | Correct step counts per phase; add methodology note |
| `ACCEPTANCE_VALIDATION_REPORT.md` | FIX-008 | Add methodology note about self-validation |
| `CORRECTION_REPORT.md` | FIX-002 | Update "14 total steps" → "18 total steps" |
| `REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json` | FIX-002 | Update step_contracts deferral comment |
| `VERIFICATION_MANIFEST.json` | FIX-002, FIX-006, FIX-010 | Update step count, remediation package count; add 4 missing entries |
| `INDEX.md` | FIX-009 | Correct 8 size entries; remove phantom file; add 9 missing file references; fix template path |

### Evidence Files to Create

| Path | Written By |
|---|---|
| `.state/evidence/FIX-001/field_count_corrections.json` | PH-01 STEP-001 |
| `.state/evidence/FIX-002/step_count_corrections.json` | PH-02 STEP-001 |
| `.state/evidence/FIX-003/path_parameterization.json` | PH-03 STEP-001 |
| `.state/evidence/FIX-004/script_markers.json` | PH-04 STEP-001 |
| `.state/evidence/FIX-005/gates_completion.json` | PH-05 STEP-001 |
| `.state/evidence/FIX-006/remediation_completion.json` | PH-06 STEP-001 |
| `.state/evidence/FIX-007/certification_corrections.json` | PH-07 STEP-001 |
| `.state/evidence/FIX-008/methodology_disclosure.json` | PH-08 STEP-001 |
| `.state/evidence/FIX-009/index_corrections.json` | PH-09 STEP-001 |
| `.state/evidence/FIX-010/manifest_additions.json` | PH-10 STEP-001 |

---

## SECTION 6: phase_plan

```
PH-01: Field Count Correction          → GATE-FIX-001
PH-02: Step Count Reconciliation       → GATE-FIX-002
PH-03: Path Parameterization           → GATE-FIX-003
PH-04: Script Presence Markers         → GATE-FIX-004
PH-05: Gates Completion                → GATE-FIX-005
PH-06: Remediation Plan Completion     → GATE-FIX-006
PH-07: Certification Correction        → GATE-FIX-007
PH-08: Methodology Disclosure          → GATE-FIX-008
```

Dependency order: PH-01 → PH-02 → PH-03 → PH-04 → PH-05 → PH-06 → PH-07 → PH-08

PH-05 and PH-06 may run after PH-04 in parallel (independent artifacts).
PH-07 and PH-08 must run after PH-05 and PH-06 complete (they reference final counts).
PH-09 and PH-10 may run after PH-02 in parallel (independent artifacts; PH-09 corrects INDEX.md sizes which are also addressed by PH-02 step count work; run PH-09 after PH-02 to avoid re-opening INDEX.md).

---

## SECTION 7: self_healing

```json
{
  "per_phase_max_attempts": 3,
  "per_step_max_attempts": 2,
  "on_gate_failure": "re-read affected file, re-apply edit, re-run gate",
  "on_evidence_missing": "re-run step, do not skip gate",
  "abort_condition": "same gate fails 3 times in a row — escalate to user"
}
```

---

## SECTION 8: worktree_isolation

Each phase runs in the main worktree (no parallel branches needed — changes are sequential and non-conflicting). All edits are committed atomically per phase with message format:

```
fix(PHASE-N): <short description> [FIX-XXX]
```

Evidence directories are created before edits so gate validators can verify they exist post-edit.

---

## SECTION 9: ground_truth_levels

| Level | Description | Used In |
|---|---|---|
| L0 | No verification — assertion only | Never used in this plan |
| L1 | File existence check | Evidence directory creation |
| L2 | File content grep / regex match | Field count corrections, step count checks |
| L3 | JSON parse + key/value assertion | gates_spec completeness, remediation_plan structure |
| L4 | Cross-file consistency (two files agree) | VERIFICATION_MANIFEST vs actual file contents |
| L5 | Full execution simulation | Out of scope (scripts not implemented) |

This plan targets L2-L4 verification. L5 is deferred until scripts are implemented.

---

## SECTION 10: phase_contracts

### PH-01: Field Count Correction

```json
{
  "phase_id": "PH-01",
  "title": "Fix '11 required fields' → '12' in contracts file",
  "inputs": [
    ".state/complete_phase_step_gate_contracts.json"
  ],
  "outputs": [
    ".state/complete_phase_step_gate_contracts.json (modified)",
    ".state/evidence/FIX-001/field_count_corrections.json"
  ],
  "invariants": [
    "All other content in contracts file unchanged",
    "JSON remains parseable after edit"
  ],
  "pass_criteria": "grep '11 required fields' .state/complete_phase_step_gate_contracts.json returns 0 matches",
  "gate": "GATE-FIX-001"
}
```

### PH-02: Step Count Reconciliation

```json
{
  "phase_id": "PH-02",
  "title": "Replace all step count references with canonical value 18",
  "inputs": [
    "README.md",
    "EXECUTION_COMPLETE.md",
    "INDEX.md",
    "FINAL_VALIDATION_REPORT.md",
    "CORRECTION_REPORT.md",
    "COMPLETION_CERTIFICATE.txt",
    "REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json",
    "VERIFICATION_MANIFEST.json"
  ],
  "outputs": [
    "All 8 files modified",
    ".state/evidence/FIX-002/step_count_corrections.json"
  ],
  "invariants": [
    "Step count 18 used consistently (not '12+', not '14', not '19')",
    "Phase-level breakdown (PH-01=3, PH-02=4, PH-03=3, PH-04=4, PH-05=2, PH-06=2) used wherever per-phase counts appear"
  ],
  "pass_criteria": "No document contains '12+' near 'steps'; FINAL_VALIDATION_REPORT shows PH-01=3, PH-02=4",
  "gate": "GATE-FIX-002"
}
```

### PH-03: Path Parameterization

```json
{
  "phase_id": "PH-03",
  "title": "Replace hardcoded absolute paths with relative or parameterized references",
  "inputs": [
    ".state/complete_phase_step_gate_contracts.json"
  ],
  "outputs": [
    ".state/complete_phase_step_gate_contracts.json (modified)",
    ".state/evidence/FIX-003/path_parameterization.json"
  ],
  "invariants": [
    "Functional semantics of the path reference preserved",
    "JSON remains parseable"
  ],
  "replacement_strategy": "Two-tier resolution: (1) Replace absolute path with repo-relative path '../newPhasePlanProcess/01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json' as the primary reference. (2) Add a comment: 'OVERRIDE: if repo layout differs, update ../newPhasePlanProcess/ prefix accordingly'. Repo-relative path is the authoritative reference.",
  "pass_criteria": "grep 'C:\\\\Users\\\\richg' .state/complete_phase_step_gate_contracts.json returns 0 matches",
  "gate": "GATE-FIX-003"
}
```

### PH-04: Script Presence Markers

```json
{
  "phase_id": "PH-04",
  "title": "Mark all 14 referenced-but-absent scripts with [NOT_IMPLEMENTED] prefix",
  "inputs": [
    ".state/complete_phase_step_gate_contracts.json"
  ],
  "outputs": [
    ".state/complete_phase_step_gate_contracts.json (modified)",
    ".state/evidence/FIX-004/script_markers.json"
  ],
  "invariants": [
    "Script path strings preserved — only prefix added",
    "Gate commands also marked so validators know to skip execution"
  ],
  "scripts_to_mark": [
    "scripts/inventory_sources.py",
    "scripts/validate_source_inventory.py",
    "scripts/parse_reg_auto_plan.py",
    "scripts/build_contract_gap_matrix.py",
    "scripts/validate_matrix_completeness.py",
    "scripts/map_programspec_fields.py",
    "scripts/validate_programspec_mapping.py",
    "scripts/synthesize_remediation.py",
    "scripts/validate_remediation_plan.py",
    "scripts/generate_gates.py",
    "scripts/validate_gates.py",
    "scripts/assemble_final_plan.py",
    "scripts/validate_final_assembly.py",
    "scripts/run_full_validation.py"
  ],
  "pass_criteria": "All 14 script references contain '[NOT_IMPLEMENTED]' prefix in command fields",
  "gate": "GATE-FIX-004"
}
```

### PH-05: Gates Completion

```json
{
  "phase_id": "PH-05",
  "title": "Add GATE-003 through GATE-006 to gates_spec.json; fix step_id naming",
  "inputs": [
    ".state/gates/gates_spec.json",
    ".state/complete_phase_step_gate_contracts.json (for step_id reference)"
  ],
  "outputs": [
    ".state/gates/gates_spec.json (modified — 6 gates total)",
    ".state/evidence/FIX-005/gates_completion.json"
  ],
  "invariants": [
    "Gate step_ids use STEP-NNN format (not STEP-001-D or STEP-002-E)",
    "validation_summary.total_gates updated to actual count",
    "All 6 gates have: gate_id, phase, step_id, command, expect_exit_code, expect_stdout_regex, expect_files, evidence"
  ],
  "step_id_fixes": {
    "GATE-001": "STEP-001-D → STEP-003 (last step of PH-01)",
    "GATE-002": "STEP-002-E → STEP-007 (last step of PH-02)"
  },
  "pass_criteria": "JSON parse of gates_spec.json yields array with 6 items; each item has all required fields",
  "gate": "GATE-FIX-005"
}
```

### PH-06: Remediation Plan Completion

```json
{
  "phase_id": "PH-06",
  "title": "Add waves 4-6 and populate work_packages in remediation_plan.json",
  "inputs": [
    ".state/remediation/remediation_plan.json",
    ".state/issues/normalized_issues.json (for issue list)"
  ],
  "outputs": [
    ".state/remediation/remediation_plan.json (modified)",
    ".state/evidence/FIX-006/remediation_completion.json"
  ],
  "invariants": [
    "Work packages reference actual issue IDs from normalized_issues.json",
    "Total counts (total_work_packages, total_tasks) are either accurate or marked as [ESTIMATE]",
    "Waves 1-3 content preserved unchanged"
  ],
  "work_packages_strategy": "Add one work_package entry per issue (REG-001 through REG-019); mark task_count as [ESTIMATED] if not precisely known",
  "pass_criteria": "work_packages array has 19 entries; waves array has 6 entries; JSON is valid",
  "gate": "GATE-FIX-006"
}
```

### PH-07: Certification Correction

```json
{
  "phase_id": "PH-07",
  "title": "Update certification documents to reflect accurate delivery status",
  "inputs": [
    "COMPLETION_CERTIFICATE.txt",
    "README.md",
    "EXECUTION_COMPLETE.md"
  ],
  "outputs": [
    "All 3 files modified",
    ".state/evidence/FIX-007/certification_corrections.json"
  ],
  "changes": [
    "COMPLETION_CERTIFICATE: Add CAVEATS section listing FIX-001 through FIX-006 as post-acceptance corrections",
    "README.md: Update step count; add correction notice at top",
    "EXECUTION_COMPLETE.md: Update step count; add correction notice"
  ],
  "invariants": [
    "Acceptance certificate date preserved (not backdated)",
    "Correction notice references certificate ID REG-AUTO-REWRITE-2026-03-08-001"
  ],
  "pass_criteria": "COMPLETION_CERTIFICATE.txt contains 'CAVEATS' section; README contains correction notice; step count '18' present",
  "gate": "GATE-FIX-007"
}
```

### PH-09: INDEX.md Corrections

```json
{
  "phase_id": "PH-09",
  "title": "Correct INDEX.md: size entries, phantom file, missing files, template path",
  "inputs": ["INDEX.md"],
  "outputs": [
    "INDEX.md (modified)",
    ".state/evidence/FIX-009/index_corrections.json"
  ],
  "size_corrections": {
    "source": "VERIFICATION_MANIFEST.json (verified against disk)",
    "corrections": [
      { "artifact": "REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json", "index_claimed": "~22KB", "actual_bytes": 13744, "actual_kb": "13.4KB" },
      { "artifact": "CONTRACT_GAP_MATRIX.md", "index_claimed": "~42KB", "actual_bytes": 15398, "actual_kb": "15.0KB" },
      { "artifact": ".state/remediation/remediation_plan.json", "index_claimed": "~8KB", "actual_bytes": 1677, "actual_kb": "1.6KB" },
      { "artifact": ".state/gates/gates_spec.json", "index_claimed": "~5KB", "actual_bytes": 1912, "actual_kb": "1.9KB" },
      { "artifact": ".state/issues/normalized_issues.json", "index_claimed": "~15KB", "actual_bytes": 13457, "actual_kb": "13.1KB" },
      { "artifact": ".state/issues/component_inventory.json", "index_claimed": "~3KB", "actual_bytes": 6916, "actual_kb": "6.8KB" },
      { "artifact": ".state/issues/contract_taxonomy.json", "index_claimed": "~2KB", "actual_bytes": 5035, "actual_kb": "4.9KB" },
      { "artifact": ".state/matrix/contract_gap_matrix.json", "index_claimed": "~25KB", "actual_bytes": 17604, "actual_kb": "17.2KB" }
    ]
  },
  "phantom_file_removal": "REMEDIATION_PLAN_SUMMARY.md — referenced as 'To be created'; either remove entry or re-label clearly as NOT_CREATED",
  "missing_files_to_add": [
    "README.md (6.5KB) — rewrite delivery document",
    "BEFORE_AFTER_COMPARISON.md (11.5KB) — rewrite delivery document",
    "EXECUTION_COMPLETE.md (5.6KB) — rewrite delivery document",
    "ACCEPTANCE_VALIDATION_REPORT.md (13.0KB) — rewrite delivery document",
    "CORRECTION_REPORT.md (9.3KB) — rewrite delivery document",
    "IMPLEMENTATION_CHECKLIST.md (9.0KB) — rewrite delivery document",
    "ISSUE_REMEDIATION_PLAN.md (21.6KB) — rewrite delivery document",
    "COMPLETION_CERTIFICATE.txt — certification artifact",
    "zany-napping-lollipop.md — correction plan (this document)"
  ],
  "path_fix": "Template path in Source Materials table: 'newPhasePlanProcess/...' → '../newPhasePlanProcess/...'",
  "invariants": [
    "Existing correct entries unchanged",
    "FINAL_VALIDATION_REPORT.md size (~11KB actual 11,277 bytes) verified correct — do not modify",
    "INDEX.md remains valid Markdown"
  ],
  "pass_criteria": "All 8 size entries match manifest actuals; REMEDIATION_PLAN_SUMMARY.md entry removed or clearly marked NOT_CREATED; 9 missing files present in index",
  "gate": "GATE-FIX-009"
}
```

### PH-10: VERIFICATION_MANIFEST.json Additions

```json
{
  "phase_id": "PH-10",
  "title": "Add 4 missing post-creation files to VERIFICATION_MANIFEST.json",
  "inputs": ["VERIFICATION_MANIFEST.json"],
  "outputs": [
    "VERIFICATION_MANIFEST.json (modified)",
    ".state/evidence/FIX-010/manifest_additions.json"
  ],
  "files_to_add": [
    { "path": "COMPLETION_CERTIFICATE.txt", "note": "Primary certification artifact; absent from manifest despite existing on disk" },
    { "path": "REG_AUTO_PLAN.txt", "note": "Source material listed in INDEX.md; absent from manifest" },
    { "path": "ChatGPT-Automation Alignment Assessment.md", "note": "Source material listed in INDEX.md; absent from manifest" },
    { "path": "zany-napping-lollipop.md", "note": "Correction plan created post-manifest-timestamp 2026-03-08T19:00:36Z" }
  ],
  "size_strategy": "Read actual file sizes from disk before writing manifest entries; do not estimate",
  "invariants": [
    "Existing 126 entries preserved unchanged",
    "JSON remains valid after additions",
    "VERIFICATION_MANIFEST.json itself excluded from self-referential entry (acceptable gap)"
  ],
  "pass_criteria": "All 4 files present in manifest.artifacts array with correct path and exists: true",
  "gate": "GATE-FIX-010"
}
```

### PH-08: Methodology Disclosure

```json
{
  "phase_id": "PH-08",
  "title": "Add self-validation circularity disclosure to validation reports",
  "inputs": [
    "FINAL_VALIDATION_REPORT.md",
    "ACCEPTANCE_VALIDATION_REPORT.md"
  ],
  "outputs": [
    "Both files modified",
    ".state/evidence/FIX-008/methodology_disclosure.json"
  ],
  "disclosure_text": "METHODOLOGY NOTE: Criterion 11 (Report Consistency) was validated by the same system that generated the reports. Independent third-party cross-check was not performed. Metrics should be independently verified before treating this delivery as ground truth.",
  "invariants": [
    "Disclosure added as clearly labeled section, not buried in existing text",
    "Existing validation results unchanged"
  ],
  "pass_criteria": "Both files contain string 'METHODOLOGY NOTE'",
  "gate": "GATE-FIX-008"
}
```

---

## SECTION 11: step_contracts

> **Standard step schema**: Every step carries `step_id`, `phase`, `title`, `preconditions`, `execution`, `postconditions`, `file_scope`, `evidence`, `ground_truth_level`, `timeout_sec`, `retries`, `failure_modes`.

### PH-01 Steps

#### STEP-PH01-001: Locate and correct '11 required fields' occurrences

```json
{
  "step_id": "STEP-PH01-001",
  "phase": "PH-01",
  "title": "Grep and replace '11 required fields' with '12 required fields'",
  "preconditions": [
    ".state/complete_phase_step_gate_contracts.json exists and is valid JSON"
  ],
  "inputs": {
    "file": ".state/complete_phase_step_gate_contracts.json",
    "target_string": "11 required fields",
    "replacement_string": "12 required fields"
  },
  "execution": [
    "1. Read .state/complete_phase_step_gate_contracts.json",
    "2. Grep for '11 required fields' — note all 3 line numbers",
    "3. Apply Edit tool: replace each occurrence",
    "4. Verify JSON still parses after edit"
  ],
  "postconditions": [
    "grep '11 required fields' returns 0 matches",
    "grep '12 required fields' returns >= 3 matches",
    "python -c \"import json; json.load(open('.state/complete_phase_step_gate_contracts.json'))\" exits 0"
  ],
  "file_scope": {
    "allowed": [".state/complete_phase_step_gate_contracts.json"],
    "forbidden": ["*.py", "src/*"],
    "read_only": [".state/matrix/*", ".state/issues/*"]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-001",
    "files": ["field_count_corrections.json"],
    "content": "{ issue_id: FIX-001, occurrences_fixed: 3, old_value: '11', new_value: '12', timestamp: <ISO> }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 60,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-001", "condition": "grep finds != 3 occurrences", "action": "Log actual count; fix all found occurrences; note discrepancy in evidence" },
    { "code": "FM-002", "condition": "JSON parse fails after edit", "action": "Revert edit; inspect file for syntax error; re-apply carefully" }
  ]
}
```

### PH-02 Steps

#### STEP-PH02-001: Identify all step count mismatches

```json
{
  "step_id": "STEP-PH02-001",
  "phase": "PH-02",
  "title": "Grep all 9 target files for incorrect step count strings",
  "preconditions": ["PH-01 gate GATE-FIX-001 has passed"],
  "execution": [
    "Grep each target file for: '12+', '14 total steps', '19 total steps'",
    "Grep FINAL_VALIDATION_REPORT.md for per-phase counts (PH-01=4, PH-02=5)",
    "Record all locations in evidence"
  ],
  "postconditions": [
    "Evidence file contains location map of all mismatches found",
    "Files with no mismatches are recorded as 'already-correct' — not treated as errors"
  ],
  "file_scope": {
    "allowed": [],
    "forbidden": [],
    "read_only": [
      "README.md", "EXECUTION_COMPLETE.md", "INDEX.md",
      "FINAL_VALIDATION_REPORT.md", "CORRECTION_REPORT.md",
      "COMPLETION_CERTIFICATE.txt", "REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json",
      "VERIFICATION_MANIFEST.json"
    ]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-002",
    "files": ["mismatch_location_map.json"],
    "content": "{ files_scanned: [...], mismatches: [{ file, line, found_value }], already_correct: [...], timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 30,
  "retries": 1,
  "failure_modes": [
    { "code": "FM-003", "condition": "No matches found in a file that was expected to have them", "action": "Mark as already-correct in evidence; proceed" }
  ]
}
```

#### STEP-PH02-002: Apply step count corrections

```json
{
  "step_id": "STEP-PH02-002",
  "phase": "PH-02",
  "title": "Edit all 9 files to replace incorrect step counts with '18'",
  "preconditions": ["STEP-PH02-001 complete; location map exists"],
  "execution": [
    "For each file with '12+' near 'steps': replace with '18'",
    "For FINAL_VALIDATION_REPORT.md: correct PH-01=4→3, PH-02=5→4, confirm PH-03=3, PH-04=4, PH-05=2, PH-06=2",
    "For CORRECTION_REPORT.md: replace '14 total steps' with '18 total steps'",
    "For VERIFICATION_MANIFEST.json: update step count field if present"
  ],
  "file_scope": {
    "allowed": [
      "README.md", "EXECUTION_COMPLETE.md", "INDEX.md",
      "FINAL_VALIDATION_REPORT.md", "CORRECTION_REPORT.md",
      "COMPLETION_CERTIFICATE.txt", "REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json",
      "VERIFICATION_MANIFEST.json"
    ],
    "forbidden": [".state/complete_phase_step_gate_contracts.json", "*.py"]
  },
  "postconditions": [
    "No target file contains '12+' in step-count context",
    "FINAL_VALIDATION_REPORT.md shows PH-01=3 steps"
  ],
  "evidence": {
    "directory": ".state/evidence/FIX-002",
    "files": ["step_count_corrections.json"],
    "content": "{ issue_id: 'FIX-002', files_modified: [...], corrections: [{ file, old_value, new_value, line }], timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 120,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-004", "condition": "'12+' still found after edit in a target file", "action": "Re-read file; check for variant patterns ('12+ steps', '12+steps'); fix all variants" },
    { "code": "FM-005", "condition": "Per-phase breakdown in FINAL_VALIDATION_REPORT still wrong after edit", "action": "Re-read that section; identify exact line; apply targeted edit" }
  ]
}
```

### PH-03 Steps

#### STEP-PH03-001: Replace hardcoded paths

```json
{
  "step_id": "STEP-PH03-001",
  "phase": "PH-03",
  "title": "Replace C:\\Users\\richg\\Gov_Reg\\newPhasePlanProcess\\... with parameterized reference",
  "preconditions": ["PH-02 gate GATE-FIX-002 has passed"],
  "execution": [
    "Read .state/complete_phase_step_gate_contracts.json",
    "Locate both hardcoded path occurrences (PH-06 input ~line 117, GATE-006 command ~line 419)",
    "Replace each with the repo-relative path: '../newPhasePlanProcess/01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json'",
    "Add an adjacent comment string near first occurrence: 'OVERRIDE: if repo layout differs, update ../newPhasePlanProcess/ prefix accordingly'",
    "Verify JSON parses after edit"
  ],
  "postconditions": [
    "grep 'C:\\\\Users\\\\richg' returns 0 matches",
    "grep '../newPhasePlanProcess/' returns >= 2 matches",
    "JSON is valid"
  ],
  "file_scope": {
    "allowed": [".state/complete_phase_step_gate_contracts.json"],
    "forbidden": ["*.py", "src/*"],
    "read_only": []
  },
  "evidence": {
    "directory": ".state/evidence/FIX-003",
    "files": ["path_parameterization.json"],
    "content": "{ issue_id: 'FIX-003', locations_fixed: 2, old_value: 'C:\\\\Users\\\\richg\\\\...', new_value: '../newPhasePlanProcess/...', strategy: 'repo-relative-primary', timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 60,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-006", "condition": "grep finds != 2 occurrences of hardcoded path", "action": "Log actual count; fix all found; note discrepancy in evidence" },
    { "code": "FM-007", "condition": "JSON parse fails after edit", "action": "Revert; inspect for syntax error around replaced strings; re-apply carefully" }
  ]
}
```

### PH-04 Steps

#### STEP-PH04-001: Mark absent scripts

```json
{
  "step_id": "STEP-PH04-001",
  "phase": "PH-04",
  "title": "Prefix all 14 absent script paths with [NOT_IMPLEMENTED] in command fields",
  "preconditions": ["PH-03 gate GATE-FIX-003 has passed"],
  "execution": [
    "Read .state/complete_phase_step_gate_contracts.json",
    "For each of the 14 script references in 'command' fields, prepend '[NOT_IMPLEMENTED] '",
    "Do not modify non-command fields that reference scripts in description/evidence",
    "Verify JSON is valid after all edits"
  ],
  "postconditions": [
    "All 14 command fields containing script references now carry '[NOT_IMPLEMENTED]' prefix",
    "No title/description/evidence field was altered",
    "JSON is valid"
  ],
  "file_scope": {
    "allowed": [".state/complete_phase_step_gate_contracts.json"],
    "forbidden": ["*.py", "src/*", "scripts/*"],
    "read_only": []
  },
  "evidence": {
    "directory": ".state/evidence/FIX-004",
    "files": ["script_markers.json"],
    "content": "{ issue_id: 'FIX-004', scripts_marked: [{ script_name, field: 'command', before, after }], non_command_fields_unmodified: true, timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L3",
  "timeout_sec": 120,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-008", "condition": "A non-command field (title/description/evidence) is accidentally marked", "action": "Revert that field; re-apply only to command fields" },
    { "code": "FM-009", "condition": "JSON parse fails after batch edit", "action": "Read file; find malformed entry; fix syntax; verify parse" }
  ]
}
```

### PH-05 Steps

#### STEP-PH05-001: Fix existing gates step_id references

```json
{
  "step_id": "STEP-PH05-001",
  "phase": "PH-05",
  "title": "Fix GATE-001 step_id STEP-001-D → STEP-003; GATE-002 step_id STEP-002-E → STEP-007",
  "preconditions": [
    "PH-04 gate GATE-FIX-004 has passed",
    ".state/gates/gates_spec.json exists — preflight: python -c \"import json; json.load(open('.state/gates/gates_spec.json'))\" must exit 0",
    ".state/complete_phase_step_gate_contracts.json parseable (used as step_id reference source)"
  ],
  "execution": [
    "Read .state/gates/gates_spec.json",
    "Locate GATE-001 entry; update step_id from 'STEP-001-D' to 'STEP-003'",
    "Locate GATE-002 entry; update step_id from 'STEP-002-E' to 'STEP-007'",
    "Verify JSON valid after edit"
  ],
  "postconditions": [
    "GATE-001 entry has step_id == 'STEP-003'",
    "GATE-002 entry has step_id == 'STEP-007'",
    "No other gate entries modified",
    "JSON is valid"
  ],
  "file_scope": {
    "allowed": [".state/gates/gates_spec.json"],
    "forbidden": ["*.py", "src/*"],
    "read_only": [".state/complete_phase_step_gate_contracts.json"]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-005",
    "files": ["step_id_corrections.json"],
    "content": "{ issue_id: 'FIX-005', step: 'STEP-PH05-001', corrections: [{ gate_id: 'GATE-001', old: 'STEP-001-D', new: 'STEP-003' }, { gate_id: 'GATE-002', old: 'STEP-002-E', new: 'STEP-007' }], timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L3",
  "timeout_sec": 60,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-010", "condition": "GATE-001 or GATE-002 not found in gates_spec.json", "action": "Log missing entry; skip rename for that entry; continue; note in evidence" },
    { "code": "FM-011", "condition": "JSON parse fails after edit", "action": "Revert; inspect structure; re-apply targeted rename" }
  ]
}
```

#### STEP-PH05-002: Add GATE-003 through GATE-006

```json
{
  "step_id": "STEP-PH05-002",
  "phase": "PH-05",
  "title": "Append GATE-003 through GATE-006 to gates_spec.json; update total_gates to 6",
  "preconditions": [
    "STEP-PH05-001 complete",
    ".state/gates/gates_spec.json currently has exactly 2 gates — verify before adding"
  ],
  "execution": [
    "Read .state/gates/gates_spec.json",
    "Append 4 new gate objects (GATE-003 through GATE-006) from data_contract below",
    "Update validation_summary.total_gates field to 6",
    "Verify JSON is valid; count gate entries"
  ],
  "data_contract": {
    "GATE-003": {
      "gate_id": "GATE-003",
      "phase": "PH-03",
      "step_id": "STEP-010",
      "purpose": "Verify ProgramSpec mapping covers all 19 issues",
      "command": "[NOT_IMPLEMENTED] python scripts/validate_programspec_mapping.py",
      "expect_exit_code": 0,
      "expect_stdout_regex": "ProgramSpec mapping: PASS.*19 issues mapped",
      "forbid_stdout_regex": "FAIL|UNMAPPED",
      "expect_files": [".state/programspec/programspec_mapping.json"],
      "evidence": { "directory": ".state/evidence/PH-03/GATE-003" }
    },
    "GATE-004": {
      "gate_id": "GATE-004",
      "phase": "PH-04",
      "step_id": "STEP-014",
      "purpose": "Verify remediation plan has all waves and work packages",
      "command": "[NOT_IMPLEMENTED] python scripts/validate_remediation_plan.py",
      "expect_exit_code": 0,
      "expect_stdout_regex": "Remediation plan: PASS.*6 waves.*19 packages",
      "forbid_stdout_regex": "FAIL|EMPTY|MISSING",
      "expect_files": [".state/remediation/remediation_plan.json"],
      "evidence": { "directory": ".state/evidence/PH-04/GATE-004" }
    },
    "GATE-005": {
      "gate_id": "GATE-005",
      "phase": "PH-05",
      "step_id": "STEP-016",
      "purpose": "Verify all 6 gates present in gates_spec with required fields",
      "command": "[NOT_IMPLEMENTED] python scripts/validate_gates.py",
      "expect_exit_code": 0,
      "expect_stdout_regex": "Gates validation: PASS.*6 gates",
      "forbid_stdout_regex": "FAIL|MISSING",
      "expect_files": [".state/gates/gates_spec.json"],
      "evidence": { "directory": ".state/evidence/PH-05/GATE-005" }
    },
    "GATE-006": {
      "gate_id": "GATE-006",
      "phase": "PH-06",
      "step_id": "STEP-018",
      "purpose": "Verify final assembly is complete and all artifacts consistent",
      "command": "[NOT_IMPLEMENTED] python scripts/validate_final_assembly.py --template ../newPhasePlanProcess/01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json",
      "expect_exit_code": 0,
      "expect_stdout_regex": "Final assembly: PASS",
      "forbid_stdout_regex": "FAIL|INCONSISTENT",
      "expect_files": ["REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json", "CONTRACT_GAP_MATRIX.md"],
      "evidence": { "directory": ".state/evidence/PH-06/GATE-006" }
    }
  },
  "postconditions": [
    "JSON parse of gates_spec.json yields 6-item array (or object with 6 gates)",
    "validation_summary.total_gates == 6"
  ],
  "file_scope": {
    "allowed": [".state/gates/gates_spec.json"],
    "forbidden": ["*.py", "src/*"],
    "read_only": [".state/complete_phase_step_gate_contracts.json"]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-005",
    "files": ["gates_completion.json"],
    "content": "{ issue_id: 'FIX-005', step: 'STEP-PH05-002', gates_added: ['GATE-003','GATE-004','GATE-005','GATE-006'], total_gates_after: 6, timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L3",
  "timeout_sec": 120,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-012", "condition": "JSON invalid after appending gates", "action": "Revert to pre-edit state; add gates one at a time; verify JSON after each" },
    { "code": "FM-013", "condition": "validation_summary.total_gates field not found", "action": "Add validation_summary object if missing; set total_gates to 6" }
  ]
}
```

### PH-06 Steps

#### STEP-PH06-001: Add waves 4-6 to remediation_plan.json

```json
{
  "step_id": "STEP-PH06-001",
  "phase": "PH-06",
  "title": "Add dependency waves 4-6 and populate work_packages",
  "preconditions": [
    "PH-05 gate GATE-FIX-005 has passed",
    ".state/remediation/remediation_plan.json exists — preflight: python -c \"import json; json.load(open('.state/remediation/remediation_plan.json'))\" must exit 0",
    ".state/issues/normalized_issues.json exists — preflight: python -c \"import json; json.load(open('.state/issues/normalized_issues.json'))\" must exit 0",
    "Read normalized_issues.json to confirm issue IDs REG-001 through REG-019 are present before proceeding"
  ],
  "wave_assignment_rules": {
    "rule": "Assign by framework_category from CONTRACT_GAP_MATRIX.md — deterministic, not arbitrary",
    "wave_1": "Executor category (pipeline execution layer) — REG-001",
    "wave_2": "Mutation/Identity category (fail-closed write paths) — REG-005",
    "wave_3": "Phase postcondition gaps (pipeline reliability) — REG-002, REG-004, REG-007, REG-014",
    "wave_4": "Gate/validation gaps (correctness checking layer) — REG-003, REG-010, REG-011, REG-013",
    "wave_5": "Transport/integration (data flow and deduplication) — REG-006, REG-008, REG-009, REG-012",
    "wave_6": "Cross-cutting (reporting, metadata, final consistency) — REG-015 through REG-019"
  },
  "execution": [
    "Read .state/remediation/remediation_plan.json — confirm waves 1-3 are present and preserve them unchanged",
    "Apply wave_assignment_rules above to determine wave membership",
    "Add wave 4 entry with issues from rule: REG-003, REG-010, REG-011, REG-013",
    "Add wave 5 entry with issues from rule: REG-006, REG-008, REG-009, REG-012",
    "Add wave 6 entry with issues from rule: REG-015, REG-016, REG-017, REG-018, REG-019",
    "Populate work_packages array with 19 entries (one per REG-NNN) — each: { issue_id, component, framework_category, remediation_type, priority, wave_assignment, estimated_tasks }",
    "Update total_work_packages to 19; mark total_tasks as '[ESTIMATED: 73]'",
    "Verify JSON is valid"
  ],
  "postconditions": [
    "work_packages array length == 19",
    "waves array length == 6",
    "Each work_package.issue_id exists in normalized_issues.json",
    "JSON is valid"
  ],
  "file_scope": {
    "allowed": [".state/remediation/remediation_plan.json"],
    "forbidden": ["*.py", "src/*"],
    "read_only": [".state/issues/normalized_issues.json", ".state/matrix/contract_gap_matrix.json"]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-006",
    "files": ["remediation_completion.json"],
    "content": "{ issue_id: 'FIX-006', waves_added: [4,5,6], work_packages_count: 19, total_waves: 6, wave_assignment_rule: 'by framework_category', timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L3",
  "timeout_sec": 120,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-014", "condition": "normalized_issues.json missing or unparseable", "action": "ABORT phase; report to user; do not guess issue IDs" },
    { "code": "FM-015", "condition": "waves 1-3 content corrupted during edit", "action": "Revert; re-read; add waves 4-6 with append-only edit" },
    { "code": "FM-016", "condition": "work_packages count != 19 after edit", "action": "Diff against normalized_issues.json; identify missing entries; add them" }
  ]
}
```

### PH-07 Steps

#### STEP-PH07-001: Update certification documents

```json
{
  "step_id": "STEP-PH07-001",
  "phase": "PH-07",
  "title": "Add correction notices and update step counts in certification docs",
  "preconditions": ["PH-06 gate GATE-FIX-006 has passed"],
  "execution": [
    "Read COMPLETION_CERTIFICATE.txt; add CAVEATS section after SIGNATURE block listing FIX-001 through FIX-006",
    "Read README.md; add 'CORRECTION NOTICE (2026-03-08)' at top with summary of fixes",
    "Read EXECUTION_COMPLETE.md; add correction notice; update step count to 18"
  ],
  "postconditions": [
    "COMPLETION_CERTIFICATE.txt contains 'CAVEATS'",
    "README.md contains 'CORRECTION NOTICE'",
    "EXECUTION_COMPLETE.md step count shows '18'"
  ],
  "file_scope": {
    "allowed": ["COMPLETION_CERTIFICATE.txt", "README.md", "EXECUTION_COMPLETE.md"],
    "forbidden": [".state/*", "*.py", "src/*"],
    "read_only": []
  },
  "evidence": {
    "directory": ".state/evidence/FIX-007",
    "files": ["certification_corrections.json"],
    "content": "{ issue_id: 'FIX-007', files_modified: ['COMPLETION_CERTIFICATE.txt','README.md','EXECUTION_COMPLETE.md'], caveats_section_added: true, correction_notice_added: true, step_count_corrected: true, timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 90,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-017", "condition": "SIGNATURE block not found in COMPLETION_CERTIFICATE.txt", "action": "Add CAVEATS section at end of file; note placement variation in evidence" },
    { "code": "FM-018", "condition": "README.md already contains 'CORRECTION NOTICE'", "action": "Verify notice is current; update if stale; proceed" }
  ]
}
```

### PH-08 Steps

#### STEP-PH08-001: Add methodology disclosure

```json
{
  "step_id": "STEP-PH08-001",
  "phase": "PH-08",
  "title": "Add self-validation circularity disclosure to validation reports",
  "preconditions": ["PH-07 gate GATE-FIX-007 has passed"],
  "execution": [
    "Read FINAL_VALIDATION_REPORT.md; add 'METHODOLOGY NOTE' section after 'Validation Method' field",
    "Read ACCEPTANCE_VALIDATION_REPORT.md; add same 'METHODOLOGY NOTE' section",
    "Note: Criterion 11 (Report Consistency) was self-validated; independent cross-check not performed"
  ],
  "postconditions": [
    "Both files contain 'METHODOLOGY NOTE'",
    "Note explicitly names Criterion 11 as the affected check",
    "Existing validation results are unchanged"
  ],
  "file_scope": {
    "allowed": ["FINAL_VALIDATION_REPORT.md", "ACCEPTANCE_VALIDATION_REPORT.md"],
    "forbidden": [".state/*", "*.py", "src/*"],
    "read_only": []
  },
  "evidence": {
    "directory": ".state/evidence/FIX-008",
    "files": ["methodology_disclosure.json"],
    "content": "{ issue_id: 'FIX-008', files_modified: ['FINAL_VALIDATION_REPORT.md','ACCEPTANCE_VALIDATION_REPORT.md'], disclosure_added: true, criterion_11_named: true, timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 60,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-019", "condition": "'Validation Method' field not found in target file", "action": "Add METHODOLOGY NOTE as top-level section; note placement in evidence" },
    { "code": "FM-020", "condition": "Existing validation result rows were modified by edit", "action": "Revert; apply targeted insert-only edit; do not modify result rows" }
  ]
}
```

### PH-09 Steps

#### STEP-PH09-001: Correct INDEX.md size entries, phantom file, missing files, and template path

```json
{
  "step_id": "STEP-PH09-001",
  "phase": "PH-09",
  "title": "Apply all INDEX.md corrections in one atomic edit pass",
  "preconditions": [
    "PH-08 gate GATE-FIX-008 has passed",
    "VERIFICATION_MANIFEST.json readable — use as authoritative size source",
    "Read INDEX.md before editing to identify current line numbers for each size entry"
  ],
  "execution": [
    "Read VERIFICATION_MANIFEST.json to extract verified byte sizes for all 8 corrected artifacts",
    "Read INDEX.md in full to locate each size string",
    "Apply corrections: replace 8 wrong size strings with verified values from manifest",
    "Remove or relabel REMEDIATION_PLAN_SUMMARY.md entry (replace with: 'REMEDIATION_PLAN_SUMMARY.md — NOT CREATED; removed from delivery scope')",
    "Add a 'Correction-Era Documents' section listing the 9 missing rewrite-delivery files with sizes from manifest/disk",
    "Fix template path in Source Materials table from 'newPhasePlanProcess/...' to '../newPhasePlanProcess/...'",
    "Verify INDEX.md is valid Markdown after all edits"
  ],
  "postconditions": [
    "All 8 size corrections applied",
    "REMEDIATION_PLAN_SUMMARY.md entry removed or relabeled NOT_CREATED",
    "9 missing files listed in index",
    "Template path uses '../newPhasePlanProcess/' prefix"
  ],
  "file_scope": {
    "allowed": ["INDEX.md"],
    "forbidden": [".state/*", "*.py", "src/*"],
    "read_only": ["VERIFICATION_MANIFEST.json"]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-009",
    "files": ["index_corrections.json"],
    "content": "{ issue_id: 'FIX-009', size_corrections: [{ artifact, old, new }], phantom_removed: true, files_added: [...], path_fixed: true, timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L2",
  "timeout_sec": 120,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-021", "condition": "A size string not found at expected location in INDEX.md", "action": "Search for artifact name nearby; find the actual size text; correct it; note location shift in evidence" },
    { "code": "FM-022", "condition": "REMEDIATION_PLAN_SUMMARY.md entry not found", "action": "Mark as already-removed in evidence; proceed" }
  ]
}
```

### PH-10 Steps

#### STEP-PH10-001: Add 4 missing files to VERIFICATION_MANIFEST.json

```json
{
  "step_id": "STEP-PH10-001",
  "phase": "PH-10",
  "title": "Append 4 missing file entries to VERIFICATION_MANIFEST.json artifacts array",
  "preconditions": [
    "PH-09 gate GATE-FIX-009 has passed",
    "Read actual file sizes from disk before writing entries — do not use estimated values",
    "VERIFICATION_MANIFEST.json is valid JSON — preflight: python -c \"import json; json.load(open('VERIFICATION_MANIFEST.json'))\" must exit 0"
  ],
  "execution": [
    "Determine actual byte sizes for each of the 4 missing files by reading them",
    "Append 4 new objects to the artifacts array: COMPLETION_CERTIFICATE.txt, REG_AUTO_PLAN.txt, ChatGPT-Automation Alignment Assessment.md, zany-napping-lollipop.md",
    "Each entry format: { 'path': '<relative_path>', 'size_bytes': <actual>, 'size_kb': <rounded>, 'exists': true }",
    "Verify JSON is valid after additions; verify total artifacts count increased by 4"
  ],
  "postconditions": [
    "All 4 files present in artifacts array",
    "Each entry has correct path, actual size_bytes (not estimated), and exists: true",
    "JSON is valid",
    "Existing 126 entries untouched"
  ],
  "file_scope": {
    "allowed": ["VERIFICATION_MANIFEST.json"],
    "forbidden": ["*.py", "src/*"],
    "read_only": ["COMPLETION_CERTIFICATE.txt", "REG_AUTO_PLAN.txt", "ChatGPT-Automation Alignment Assessment.md", "zany-napping-lollipop.md"]
  },
  "evidence": {
    "directory": ".state/evidence/FIX-010",
    "files": ["manifest_additions.json"],
    "content": "{ issue_id: 'FIX-010', entries_added: [{ path, size_bytes }], total_artifacts_before: 126, total_artifacts_after: 130, timestamp: '<ISO>', operator: 'Claude Code' }"
  },
  "ground_truth_level": "L3",
  "timeout_sec": 60,
  "retries": 2,
  "failure_modes": [
    { "code": "FM-023", "condition": "A file to be added does not exist on disk", "action": "Log as missing; skip that entry; note in evidence; do not add exists: false entry" },
    { "code": "FM-024", "condition": "JSON invalid after additions", "action": "Revert; inspect for trailing comma or structural error; re-add entries one at a time" }
  ]
}
```

---

## SECTION 12: validation_gates

> **Gate naming convention**:
> - `GATE-FIX-NNN` — gates in **this correction plan** (delivery-package repairs)
> - `GATE-NNN` — gates in the **original runtime plan** (`REG_AUTO_PLAN_REWRITTEN_TEMPLATE_NATIVE.json`)
>
> These two gate spaces are independent. Do not conflate them when reading cross-references.
>
> **Standard gate schema**: Every gate carries `gate_id`, `phase`, `step_id`, `purpose`, `commands[]`, `timeout_sec`, `retries`, `expect_files`, `evidence`, `ground_truth_level`. Each command in `commands[]` carries `description`, `command`, `expect_exit_code`, `expect_stdout_regex`, and optionally `forbid_stdout_regex`.

### GATE-FIX-001: Field Count Corrected

```json
{
  "gate_id": "GATE-FIX-001",
  "phase": "PH-01",
  "step_id": "STEP-PH01-001",
  "purpose": "Verify '11 required fields' eliminated; '12 required fields' present ≥3 times",
  "commands": [
    {
      "description": "Old value absent",
      "command": "grep -c '11 required fields' 01260207201000001250_REGISTRY/.state/complete_phase_step_gate_contracts.json",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^0$",
      "forbid_stdout_regex": "^[1-9]"
    },
    {
      "description": "New value present ≥3 times",
      "command": "grep -c '12 required fields' 01260207201000001250_REGISTRY/.state/complete_phase_step_gate_contracts.json",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[3-9]$|^[1-9][0-9]+"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-001/field_count_corrections.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-001" },
  "ground_truth_level": "L2"
}
```

### GATE-FIX-002: Step Count Reconciled

```json
{
  "gate_id": "GATE-FIX-002",
  "phase": "PH-02",
  "step_id": "STEP-PH02-002",
  "purpose": "Verify '12+' and '14 total steps' eliminated; FINAL_VALIDATION_REPORT per-phase breakdown corrected",
  "commands": [
    {
      "description": "No '12+' in README",
      "command": "grep -c '12+' 01260207201000001250_REGISTRY/README.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^0$",
      "forbid_stdout_regex": "^[1-9]"
    },
    {
      "description": "PH-01 shows 3 steps in FINAL_VALIDATION_REPORT",
      "command": "grep -c 'PH-01.*3 step\\|3 step.*PH-01' 01260207201000001250_REGISTRY/FINAL_VALIDATION_REPORT.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]"
    },
    {
      "description": "'14 total steps' gone from CORRECTION_REPORT",
      "command": "grep -c '14 total steps' 01260207201000001250_REGISTRY/CORRECTION_REPORT.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^0$",
      "forbid_stdout_regex": "^[1-9]"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-002/step_count_corrections.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-002" },
  "ground_truth_level": "L2"
}
```

### GATE-FIX-003: Paths Parameterized

```json
{
  "gate_id": "GATE-FIX-003",
  "phase": "PH-03",
  "step_id": "STEP-PH03-001",
  "purpose": "Verify hardcoded Windows path absent; repo-relative path present ≥2 times",
  "commands": [
    {
      "description": "Hardcoded path absent",
      "command": "grep -c 'Users.richg' 01260207201000001250_REGISTRY/.state/complete_phase_step_gate_contracts.json",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^0$",
      "forbid_stdout_regex": "^[1-9]"
    },
    {
      "description": "Repo-relative path present ≥2 times",
      "command": "grep -c '../newPhasePlanProcess/' 01260207201000001250_REGISTRY/.state/complete_phase_step_gate_contracts.json",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[2-9]$|^[1-9][0-9]+"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-003/path_parameterization.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-003" },
  "ground_truth_level": "L2"
}
```

### GATE-FIX-004: Scripts Marked

```json
{
  "gate_id": "GATE-FIX-004",
  "phase": "PH-04",
  "step_id": "STEP-PH04-001",
  "purpose": "Verify all 14 exact script names marked [NOT_IMPLEMENTED] in command fields only; non-command fields uncontaminated",
  "commands": [
    {
      "description": "All 14 exact script names have [NOT_IMPLEMENTED] on same line as script path",
      "command": "python -c \"import json,re; data=open('01260207201000001250_REGISTRY/.state/complete_phase_step_gate_contracts.json').read(); scripts=['scripts/inventory_sources.py','scripts/validate_source_inventory.py','scripts/parse_reg_auto_plan.py','scripts/build_contract_gap_matrix.py','scripts/validate_matrix_completeness.py','scripts/map_programspec_fields.py','scripts/validate_programspec_mapping.py','scripts/synthesize_remediation.py','scripts/validate_remediation_plan.py','scripts/generate_gates.py','scripts/validate_gates.py','scripts/assemble_final_plan.py','scripts/validate_final_assembly.py','scripts/run_full_validation.py']; missing=[s for s in scripts if not re.search(r'\\[NOT_IMPLEMENTED\\].*' + re.escape(s), data)]; print('MISSING:', missing) if missing else print('ALL 14 MARKED')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^ALL 14 MARKED$",
      "forbid_stdout_regex": "MISSING"
    },
    {
      "description": "Non-command fields not contaminated",
      "command": "python -c \"import json; d=json.load(open('01260207201000001250_REGISTRY/.state/complete_phase_step_gate_contracts.json')); bad=[]; [bad.append(k) for obj in (d if isinstance(d,list) else d.values()) if isinstance(obj,dict) for k,v in obj.items() if k != 'command' and isinstance(v,str) and '[NOT_IMPLEMENTED]' in v]; print('CONTAMINATED_FIELDS:', bad) if bad else print('COMMAND_FIELDS_ONLY')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^COMMAND_FIELDS_ONLY$"
    }
  ],
  "timeout_sec": 60,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-004/script_markers.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-004" },
  "ground_truth_level": "L3"
}
```

### GATE-FIX-005: Gates Completed

```json
{
  "gate_id": "GATE-FIX-005",
  "phase": "PH-05",
  "step_id": "STEP-PH05-002",
  "purpose": "Verify gates_spec.json has exactly 6 gates; GATE-001 step_id corrected to STEP-003",
  "commands": [
    {
      "description": "Exactly 6 gates present",
      "command": "python -c \"import json; g=json.load(open('01260207201000001250_REGISTRY/.state/gates/gates_spec.json')); gates=g.get('gates', g) if isinstance(g,dict) else g; print(len(gates))\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^6$",
      "forbid_stdout_regex": "^[0-57-9]"
    },
    {
      "description": "GATE-001 step_id corrected",
      "command": "python -c \"import json; g=json.load(open('01260207201000001250_REGISTRY/.state/gates/gates_spec.json')); gates=g.get('gates',g) if isinstance(g,dict) else g; g001=[x for x in gates if x.get('gate_id')=='GATE-001']; print(g001[0]['step_id'] if g001 else 'NOT_FOUND')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^STEP-003$"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-005/gates_completion.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-005" },
  "ground_truth_level": "L3"
}
```

### GATE-FIX-006: Remediation Plan Complete

```json
{
  "gate_id": "GATE-FIX-006",
  "phase": "PH-06",
  "step_id": "STEP-PH06-001",
  "purpose": "Verify remediation_plan.json has 19 work_packages and 6 waves; all issue_ids are valid REG-NNN references",
  "commands": [
    {
      "description": "work_packages == 19 and waves == 6",
      "command": "python -c \"import json; r=json.load(open('01260207201000001250_REGISTRY/.state/remediation/remediation_plan.json')); print(len(r.get('work_packages',[])), len(r.get('waves',[])))\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^19 6$",
      "forbid_stdout_regex": "^0"
    },
    {
      "description": "All work_package issue_ids exist in normalized_issues.json",
      "command": "python -c \"import json; r=json.load(open('01260207201000001250_REGISTRY/.state/remediation/remediation_plan.json')); n=json.load(open('01260207201000001250_REGISTRY/.state/issues/normalized_issues.json')); valid=set(i.get('issue_id') for i in (n if isinstance(n,list) else n.get('issues',[])) if i.get('issue_id')); pkgs=set(p['issue_id'] for p in r.get('work_packages',[])); orphans=pkgs-valid; print('ORPHANS:',orphans) if orphans else print('ALL_VALID')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^ALL_VALID$"
    }
  ],
  "timeout_sec": 60,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-006/remediation_completion.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-006" },
  "ground_truth_level": "L3"
}
```

### GATE-FIX-007: Certification Updated

```json
{
  "gate_id": "GATE-FIX-007",
  "phase": "PH-07",
  "step_id": "STEP-PH07-001",
  "purpose": "Verify CAVEATS section and CORRECTION NOTICE present; step count '18' in EXECUTION_COMPLETE",
  "commands": [
    {
      "description": "CAVEATS section in COMPLETION_CERTIFICATE",
      "command": "grep -c 'CAVEATS' 01260207201000001250_REGISTRY/COMPLETION_CERTIFICATE.txt",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]",
      "forbid_stdout_regex": "^0$"
    },
    {
      "description": "CORRECTION NOTICE in README",
      "command": "grep -c 'CORRECTION NOTICE' 01260207201000001250_REGISTRY/README.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]",
      "forbid_stdout_regex": "^0$"
    },
    {
      "description": "Step count '18' in EXECUTION_COMPLETE",
      "command": "grep -c '18 step\\|steps.*18\\|18 total' 01260207201000001250_REGISTRY/EXECUTION_COMPLETE.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-007/certification_corrections.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-007" },
  "ground_truth_level": "L2"
}
```

### GATE-FIX-008: Methodology Disclosed

```json
{
  "gate_id": "GATE-FIX-008",
  "phase": "PH-08",
  "step_id": "STEP-PH08-001",
  "purpose": "Verify METHODOLOGY NOTE present in both validation reports; Criterion 11 named explicitly",
  "commands": [
    {
      "description": "METHODOLOGY NOTE in FINAL_VALIDATION_REPORT",
      "command": "grep -c 'METHODOLOGY NOTE' 01260207201000001250_REGISTRY/FINAL_VALIDATION_REPORT.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]",
      "forbid_stdout_regex": "^0$"
    },
    {
      "description": "METHODOLOGY NOTE in ACCEPTANCE_VALIDATION_REPORT",
      "command": "grep -c 'METHODOLOGY NOTE' 01260207201000001250_REGISTRY/ACCEPTANCE_VALIDATION_REPORT.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]",
      "forbid_stdout_regex": "^0$"
    },
    {
      "description": "Criterion 11 named explicitly in disclosure",
      "command": "grep -c 'Criterion 11' 01260207201000001250_REGISTRY/FINAL_VALIDATION_REPORT.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]",
      "forbid_stdout_regex": "^0$"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-008/methodology_disclosure.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-008" },
  "ground_truth_level": "L2"
}
```

### GATE-FIX-009: INDEX.md Corrected

```json
{
  "gate_id": "GATE-FIX-009",
  "phase": "PH-09",
  "step_id": "STEP-PH09-001",
  "purpose": "Verify INDEX.md size entries corrected to manifest actuals; phantom file removed; 9 missing files present; template path fixed",
  "commands": [
    {
      "description": "Main JSON size corrected to 13.4KB",
      "command": "grep -c '13.4KB\\|13,744' 01260207201000001250_REGISTRY/INDEX.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]"
    },
    {
      "description": "CONTRACT_GAP_MATRIX size corrected to 15.0KB",
      "command": "grep -c '15.0KB\\|15,398' 01260207201000001250_REGISTRY/INDEX.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]"
    },
    {
      "description": "REMEDIATION_PLAN_SUMMARY.md entry removed or marked NOT_CREATED",
      "command": "python -c \"content=open('01260207201000001250_REGISTRY/INDEX.md').read(); phantom=content.count('REMEDIATION_PLAN_SUMMARY.md'); uncaveated=content.count('REMEDIATION_PLAN_SUMMARY.md') - content.count('NOT_CREATED'); print('PHANTOM_REMAINS') if uncaveated > 0 else print('CLEAN')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^CLEAN$"
    },
    {
      "description": "Template path uses repo-relative prefix",
      "command": "grep -c '../newPhasePlanProcess/' 01260207201000001250_REGISTRY/INDEX.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]"
    },
    {
      "description": "README.md referenced in index",
      "command": "grep -c 'README.md' 01260207201000001250_REGISTRY/INDEX.md",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^[1-9]"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-009/index_corrections.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-009" },
  "ground_truth_level": "L2"
}
```

### GATE-FIX-010: Manifest Additions Complete

```json
{
  "gate_id": "GATE-FIX-010",
  "phase": "PH-10",
  "step_id": "STEP-PH10-001",
  "purpose": "Verify all 4 missing files now present in VERIFICATION_MANIFEST.json artifacts array with real sizes",
  "commands": [
    {
      "description": "All 4 paths present in manifest",
      "command": "python -c \"import json; m=json.load(open('01260207201000001250_REGISTRY/VERIFICATION_MANIFEST.json')); paths={a['path'] for a in m['artifacts']}; required=['COMPLETION_CERTIFICATE.txt','REG_AUTO_PLAN.txt','ChatGPT-Automation Alignment Assessment.md','zany-napping-lollipop.md']; missing=[r for r in required if r not in paths]; print('MISSING:',missing) if missing else print('ALL_PRESENT')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^ALL_PRESENT$",
      "forbid_stdout_regex": "MISSING"
    },
    {
      "description": "Total artifact count increased by exactly 4",
      "command": "python -c \"import json; m=json.load(open('01260207201000001250_REGISTRY/VERIFICATION_MANIFEST.json')); print(len(m['artifacts']))\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^130$"
    },
    {
      "description": "No entry has size_bytes of 0 or missing",
      "command": "python -c \"import json; m=json.load(open('01260207201000001250_REGISTRY/VERIFICATION_MANIFEST.json')); zero=[a['path'] for a in m['artifacts'] if a.get('size_bytes',0)==0]; print('ZERO_SIZE:',zero) if zero else print('ALL_SIZED')\"",
      "expect_exit_code": 0,
      "expect_stdout_regex": "^ALL_SIZED$"
    }
  ],
  "timeout_sec": 30,
  "retries": 2,
  "expect_files": [
    "01260207201000001250_REGISTRY/.state/evidence/FIX-010/manifest_additions.json"
  ],
  "evidence": { "directory": "01260207201000001250_REGISTRY/.state/evidence/FIX-010" },
  "ground_truth_level": "L3"
}
```

---

## SECTION 13: metrics

```json
{
  "issues_addressed": 10,
  "phases": 10,
  "steps": 12,
  "gates": 10,
  "files_modified": 14,
  "evidence_files_created": 10,
  "ground_truth_level_targets": {
    "L2": 7,
    "L3": 3
  },
  "scripts_implemented": 0,
  "scripts_marked_not_implemented": 14,
  "estimated_commit_count": 10,
  "audit_additions": {
    "FIX-009": "INDEX.md: 8 size corrections, 1 phantom removal, 9 missing file additions, 1 path fix",
    "FIX-010": "VERIFICATION_MANIFEST.json: 4 post-creation files added (126 → 130 entries)"
  }
}
```

---

## SECTION 14: infrastructure

```json
{
  "python_required": true,
  "python_version": "3.8+",
  "tools_required": ["Read", "Edit", "Grep", "Write"],
  "external_scripts": "None — all gate commands use python -c or grep",
  "worktree_required": false,
  "path_resolution_strategy": "repo-relative only",
  "repo_relative_template_path": "../newPhasePlanProcess/01260207201000000510_NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3.json"
}
```

---

## SECTION 15: final_summary

### Defects Resolved

All 10 defects identified in the post-delivery review are addressed by this plan:

| FIX-ID | Description | Phase | Gate |
|---|---|---|---|
| FIX-001 | Field count "11" → "12" (3 locations) | PH-01 | GATE-FIX-001 |
| FIX-002 | Step count "12+"/"14" → "18" (9 documents) | PH-02 | GATE-FIX-002 |
| FIX-003 | Hardcoded paths → parameterized (2 locations) | PH-03 | GATE-FIX-003 |
| FIX-004 | Absent scripts marked [NOT_IMPLEMENTED] (14) | PH-04 | GATE-FIX-004 |
| FIX-005 | gates_spec.json completed (2/6 → 6/6 gates) | PH-05 | GATE-FIX-005 |
| FIX-006 | remediation_plan.json completed (0 → 19 packages) | PH-06 | GATE-FIX-006 |
| FIX-007 | Certification docs updated with correction notices | PH-07 | GATE-FIX-007 |
| FIX-008 | Self-validation circularity disclosed | PH-08 | GATE-FIX-008 |
| FIX-009 | INDEX.md corrected (8 sizes, phantom removed, 9 files added, path fixed) | PH-09 | GATE-FIX-009 |
| FIX-010 | VERIFICATION_MANIFEST.json: 4 missing entries added (126→130) | PH-10 | GATE-FIX-010 |

### Post-Fix Delivery State

After all 10 phases pass their gates:
- All literal values (field counts, step counts) will be accurate
- All paths will be portable (no machine-specific hardcoding)
- All referenced scripts will be transparently marked as not-yet-implemented
- gates_spec.json will have all 6 gates with correct step_id references
- remediation_plan.json will have all 6 waves and 19 work packages
- Certification documents will carry honest correction notices
- Validation reports will disclose methodology limitations

### What Remains After This Fix Plan

The delivery will be **documentation-accurate** but **not execution-ready** until:
1. The 14 `[NOT_IMPLEMENTED]` scripts are built
2. An independent validator (separate from the generating system) runs criterion 11
3. `IMPLEMENTATION_CHECKLIST.md` checkboxes are checked off as scripts are implemented

---

## SECTION 16: runtime_completion_plan_stub

> **Status: NOT YET AUTHORED**
>
> This section is a placeholder for the separate **Runtime Completion Plan** that must follow this correction plan. This plan (`FIX-REG-AUTO-2026-03-08`) does not address any of the items below.

### Remaining Blockers for 100% Functioning Registry Automation

| ID | Blocker | Affected Component |
|---|---|---|
| RCP-001 | Pipeline runner skip logic still blocks patch generation | `pipeline_runner.py` |
| RCP-002 | File-id promotion blocked (sha256 → 20-digit `file_id` unresolved) | `file_id_reconciler.py` |
| RCP-003 | Defaults/null handling inert (`None` semantics not actionable) | `default_injector.py` |
| RCP-004 | `doc_id_resolver` and `module_dedup` report-only, no mutation | `doc_id_resolver.py`, `module_dedup.py` |
| RCP-005 | Registry cleanup, duplicate removal, path normalization unresolved | registry cleanup scripts |
| RCP-006 | Timestamp field authority not fixed | `timestamp_clusterer.py` |
| RCP-007 | E2E validator still shallow (existence-check only) | `e2e_validator.py` |
| RCP-008 | 14 `[NOT_IMPLEMENTED]` scripts need real implementation | `scripts/*.py` |
| RCP-009 | Integration tests for end-to-end patch generation and governed mutation | `tests/` |

### Two-Plan Model (Required for Full Completion)

```
Plan 1 (this plan):  REWRITE_PACKAGE_CORRECTION_PLAN  — delivery artifact accuracy
Plan 2 (pending):    RUNTIME_COMPLETION_PLAN          — actual system functionality
```

Plan 2 must be authored as a separate NEWPHASEPLANPROCESS v3.0.0 artifact after this plan's gates pass. The runtime defects in RCP-001 through RCP-009 are the true blockers between the current state and a 100% functioning registry pipeline.

---

**Plan Status: READY FOR REVIEW**
**Template Conformance: NEWPHASEPLANPROCESS v3.0.0**
**Created: 2026-03-08**
