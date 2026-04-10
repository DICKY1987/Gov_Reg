# Plan: Establish PRE-B Baseline and Fix Metadata in the Tracked v3.2 Corpus

## Context

The prior plan mixed tracked files, untracked relocation copies, and an untracked runbook. That makes it unsafe to execute as written.

This revised plan uses only the current tracked repository state as authority:

1. The authoritative release decision is in `guardrails_template_project\phase_b_override_map.md`: no explicit `v3.3.0` release bump has been selected.
2. The authoritative v3.2 source corpus for execution is the tracked repo-root files from a clean worktree based on `HEAD`:
   - `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`
   - `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`
   - `C:\Users\richg\Gov_Reg\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json`
   - `C:\Users\richg\Gov_Reg\index_generator.py`
3. The A.1 blocker evidence under `C:\Users\richg\Gov_Reg\evidence\` is already tracked. It should be verified, not re-committed by default.
4. `guardrails_template_project\typed-questing-balloon.md` is currently untracked. Do not use it as operational authority until it is reconciled and committed in a separate change.

---

## Task 0: Create a Clean Execution Worktree

PRE-B evidence should be produced from a clean tracked baseline, not from the current dirty working tree.

**Steps:**
1. Create a dedicated worktree from the current `HEAD` commit:
   ```powershell
   git -C C:\Users\richg\Gov_Reg worktree add ..\gov_reg_phase_b -b phase-b/pre-b-baseline HEAD
   ```
2. In `C:\Users\richg\gov_reg_phase_b`, confirm the tracked repo-root v3.2 JSON files and `index_generator.py` exist.
3. Confirm the worktree is clean:
   ```powershell
   git -C C:\Users\richg\gov_reg_phase_b status --short
   ```
   Expected: no output.
4. Confirm the release-decision input from the tracked override map:
   - `guardrails_template_project\phase_b_override_map.md` states that no explicit `v3.3.0` release bump is selected.

**Result:** all further PRE-B and metadata work happens inside `C:\Users\richg\gov_reg_phase_b`.

---

## Task 1: Create `evidence\PRE-B\readiness.json`

**Target file:** `C:\Users\richg\gov_reg_phase_b\evidence\PRE-B\readiness.json`

This evidence file should describe the clean tracked baseline that Phase B will start from.

**Required fields:**
- SHA-256 hashes of the three tracked repo-root source JSON files
- `git_head` from the clean worktree
- `override_map_release_decision_v3_3_0: false`
- `reserved_id_namespaces_committed: true`
- `phase_b_override_map_committed: true`
- `git_status_clean: true`
- `source_files_parse: true`
- `index_generator_exit_code: 0`
- `timestamp` in ISO 8601 format

**Schema:**
```json
{
  "phase": "PRE-B",
  "status": "PASS",
  "timestamp": "<ISO-8601>",
  "source_hashes": {
    "NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json": "<sha256>",
    "NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json": "<sha256>",
    "NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json": "<sha256>"
  },
  "git_head": "<commit-hash>",
  "override_map_release_decision_v3_3_0": false,
  "reserved_id_namespaces_committed": true,
  "phase_b_override_map_committed": true,
  "git_status_clean": true,
  "source_files_parse": true,
  "index_generator_exit_code": 0
}
```

**Steps:**
1. Create the directory if needed:
   ```powershell
   New-Item -ItemType Directory -Force C:\Users\richg\gov_reg_phase_b\evidence\PRE-B | Out-Null
   ```
2. From `C:\Users\richg\gov_reg_phase_b`, run:
   ```powershell
   python index_generator.py
   ```
   Record `index_generator_exit_code: 0`.
3. Parse each tracked repo-root JSON file:
   ```powershell
   python -c "import json; json.load(open(r'NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json', encoding='utf-8'))"
   python -c "import json; json.load(open(r'NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json', encoding='utf-8'))"
   python -c "import json; json.load(open(r'NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json', encoding='utf-8'))"
   ```
4. Compute SHA-256 hashes for the three tracked repo-root JSON files:
   ```powershell
   Get-FileHash -Algorithm SHA256 .\NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json
   Get-FileHash -Algorithm SHA256 .\NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json
   Get-FileHash -Algorithm SHA256 .\NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json
   ```
5. Record the clean worktree commit:
   ```powershell
   git rev-parse HEAD
   ```
6. Write `evidence\PRE-B\readiness.json`.
7. Commit only that file:
   ```powershell
   git add evidence\PRE-B\readiness.json
   git commit -m "evidence(PRE-B): record operational readiness baseline"
   ```

---

## Task 2: Verify A.1 Blocker Evidence Instead of Re-Committing It

The blocker evidence already exists in the tracked root evidence tree:
- `evidence\blocker_1_gate_registry_fix\`
- `evidence\blocker_2_enhancement_id_migration\`
- `evidence\blocker_3_execution_phases_classification\`
- `evidence\blocker_4_component_id_backfill\`
- `evidence\final_blocker_resolution_report.json`

**Steps:**
1. Verify the files are tracked:
   ```powershell
   git ls-files evidence\blocker_1_gate_registry_fix evidence\blocker_2_enhancement_id_migration evidence\blocker_3_execution_phases_classification evidence\blocker_4_component_id_backfill evidence\final_blocker_resolution_report.json
   ```
2. Optionally validate the summary report parses:
   ```powershell
   python -c "import json; json.load(open(r'evidence\final_blocker_resolution_report.json', encoding='utf-8'))"
   ```
3. Do not create an A.1 evidence commit unless this verification reveals an actual missing or changed tracked file.

---

## Task 3: Metadata Cleanup in the Tracked Repo-Root JSONs

Apply the metadata fixes to the tracked repo-root v3.2 source files inside the clean worktree.

### 3a - Fix gate count in `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`

Replace:
- `"Template-defined validation gates (5 default gates, extensible)"`
- `"Added template default validation gates (5, extensible)"`

With:
- `"Template-defined validation gates (6 default gates, extensible)"`
- `"Added template default validation gates (6, extensible)"`

**Why this is correct:** the file enumerates `GATE-CFG-001` through `GATE-CFG-006`, and PH-09 reports `GATE-CFG: 6`.

### 3b - Fix stale v3.0 title in `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json`

Replace:
- `"title": "Phase Plan v3.0 with Step-Level Contract Features"`

With:
- `"title": "Phase Plan v3.2 with Step-Level Contract Features"`

### 3c - Add a `v3.2.0` changelog entry to `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json`

Insert a `v3.2.0` entry in `appendix.version_history` before the existing `v3.0.0` entry:

```json
"v3.2.0": {
  "date": "2026-04-04",
  "changes": [
    "Added configuration_driven_development enforcement section",
    "Added pattern_governance with pattern_creation_contract",
    "Added executor_registry with registered executor binding",
    "Extended execution_patterns with allow_null_pattern_id enforcement",
    "Added GATE-CFG-001 through GATE-CFG-006 configuration-driven validation gates",
    "Added step-level implementation_mode, executor_binding, behavior_spec, behavior_binding_proof fields",
    "Extended planning_hierarchy with implementation_style and engine_component_id",
    "Added traceability mappings for requirement_to_pattern, component_to_pattern, step_to_executor",
    "Expanded anti_pattern_detection with CDD-violation triggers",
    "Mandatory pattern creation before implementation when no matching pattern exists"
  ]
},
```

**Steps:**
1. Apply the three metadata edits above in the repo-root files.
2. Validate both modified files parse:
   ```powershell
   python -c "import json; json.load(open(r'NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json', encoding='utf-8'))"
   python -c "import json; json.load(open(r'NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json', encoding='utf-8'))"
   ```
3. Commit only the two modified files:
   ```powershell
   git add NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json
   git commit -m "docs(metadata): fix gate count, v3.0 title, add v3.2.0 changelog entry"
   ```

---

## Critical Files

| File | Role |
|------|------|
| `evidence\PRE-B\readiness.json` | New PRE-B readiness artifact in the tracked root evidence tree |
| `evidence\final_blocker_resolution_report.json` | Existing tracked A.1 summary report |
| `evidence\blocker_1_gate_registry_fix\` | Existing tracked A.1 evidence |
| `evidence\blocker_2_enhancement_id_migration\` | Existing tracked A.1 evidence |
| `evidence\blocker_3_execution_phases_classification\` | Existing tracked A.1 evidence |
| `evidence\blocker_4_component_id_backfill\` | Existing tracked A.1 evidence |
| `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json` | Tracked repo-root spec JSON to update |
| `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json` | Tracked repo-root template JSON to update |
| `NEWPHASEPLANPROCESS_INSTRUCTION_DOCUMENT_V3_2.json` | Tracked repo-root instruction JSON used for PRE-B hashing and parse validation |
| `index_generator.py` | Tracked repo-root index generator used for PRE-B validation |
| `guardrails_template_project\phase_b_override_map.md` | Tracked release-decision authority |

---

## Commit Order

1. `evidence(PRE-B): record operational readiness baseline`
2. `docs(metadata): fix gate count, v3.0 title, add v3.2.0 changelog entry`

No A.1 commit is expected unless verification in Task 2 finds a real tracked-file discrepancy.

---

## Verification

After the planned commits inside `C:\Users\richg\gov_reg_phase_b`:
1. `git status --short` is clean.
2. `python index_generator.py` exits `0`.
3. The three tracked repo-root v3.2 JSON files parse successfully.
4. `evidence\PRE-B\readiness.json` exists and is valid JSON.
5. `git log --oneline -5` includes the PRE-B evidence commit and the metadata commit.
6. `git ls-files evidence\blocker_1_gate_registry_fix evidence\blocker_2_enhancement_id_migration evidence\blocker_3_execution_phases_classification evidence\blocker_4_component_id_backfill evidence\final_blocker_resolution_report.json` confirms the A.1 evidence remains tracked.

---

## Optional Follow-On

If `guardrails_template_project\typed-questing-balloon.md` is still intended to guide Phase B, reconcile it with `phase_b_override_map.md` and commit it as a separate documentation change before relying on it.
