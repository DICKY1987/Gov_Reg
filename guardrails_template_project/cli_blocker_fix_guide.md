# CLI Remediation Guide
## Fixing the Four Indexing Blockers in newPhasePlanProcess v3.2

**Purpose:** provide concrete solutions and implementation instructions for a CLI app to remove the four blockers identified in the indexing plan assessment.

> **Execution rule:** do not generate or rely on index artifacts until all four blockers are fixed and validated.

## 1. Objective and deliverable

**Objective:** Modify the current planning files so a CLI app can safely build deterministic ID-to-pointer indexes for patch-target arrays without ambiguity, duplicate identities, or unstable element references.

**Deliverable from the CLI app:** updated source JSON files, validation evidence for each blocker, and a final blocker-resolution report showing PASS for all four items.

## 2. Summary of blockers

| Blocker | File / location | Problem | Required fix |
|---|---|---|---|
| 1 | Technical spec `/architecture/system_layers/layer_2_validation/components[1]/gate_registry` | Duplicate gate identity: `GATE-008` appears twice | Assign unique IDs and update all cross-references |
| 2 | Template `/final_summary/what_was_delivered/enhancements` | Enhancement IDs are numeric ordinals, not stable semantic identifiers | Rename to stable symbolic IDs such as `ENH-001..ENH-010` |
| 3 | Technical spec `/architecture/system_layers/layer_2_validation/components[1]/execution_phases` | List contains plain strings with no stable identity field | Either classify as structural or convert to objects with stable IDs |
| 4 | Technical spec `/architecture/system_layers/*/components` | Component arrays lack stable `component_id` fields | Add `component_id` to each component and preserve existing display names |

## 3. Global CLI app instructions

- Work only through deterministic file reads and RFC-6902 patch generation. Do not make manual ad hoc edits.
- Before each change, compute and record source file SHA-256.
- After each change, validate JSON syntax, schema constraints, and uniqueness rules relevant to the blocker being fixed.
- Emit machine-readable evidence for every blocker under a dedicated evidence directory.
- Stop immediately on duplicate identities, unresolved references, or schema failures.

### Recommended evidence layout

- `evidence/blocker_1_gate_registry_fix/pre_state.json`
- `evidence/blocker_1_gate_registry_fix/post_state.json`
- `evidence/blocker_1_gate_registry_fix/validation.json`
- Repeat the same pattern for `blocker_2`, `blocker_3`, and `blocker_4`.
- Create `evidence/final_blocker_resolution_report.json` summarizing PASS/FAIL for all four items.

## 4.1 Fix duplicate gate identity in `gate_registry`

**Source location:** `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json :: /architecture/system_layers/layer_2_validation/components[1]/gate_registry`

**Problem:** Two different gate objects use the same `id` value `GATE-008`. A generated index cannot produce a unique `id -> pointer` map when the same identity resolves to more than one array element.

**Why it blocks indexing:** Duplicate identities break the core premise of index-eligible arrays: one stable semantic key must resolve to exactly one current pointer.

### Solution

- Choose one canonical naming scheme and make every gate ID unique.
- Keep one existing `GATE-008` value only if it is already the authoritative identity. Rename the other to a distinct stable ID.
- Update any descriptions, dependency references, examples, or documentation text that still points to the old duplicate ID.
- Add or strengthen a uniqueness validation rule for `gate_registry` IDs so duplicates fail closed in future runs.

### CLI app implementation steps

- Load `gate_registry` and build a frequency map on field `id`.
- If any ID count is greater than `1`, produce a duplicate-identity report listing each conflicting pointer.
- Apply an RFC-6902 `replace` operation to rename the non-canonical duplicate entry.
- Search the full technical specification for string references to the old duplicate ID and patch only true cross-references.
- Re-run duplicate scan and emit validation evidence proving uniqueness.

### Acceptance checks

- Every `gate_registry` element has a unique `id` value.
- No remaining textual cross-reference points to the retired duplicate ID unless explicitly documented as legacy text.
- Generated `by_gate_id` index resolves each gate ID to exactly one JSON Pointer.

## 4.2 Replace numeric enhancement IDs with stable semantic IDs

**Source location:** `NEWPHASEPLANPROCESS_AUTONOMOUS_DELIVERY_TEMPLATE_V3_2.json :: /final_summary/what_was_delivered/enhancements`

**Problem:** Enhancement objects use numeric `id` values such as `1`, `2`, `3`. Those are ordinals, not stable semantic identities. Reordering or inserting an item changes meaning and makes the ID map unsafe.

**Why it blocks indexing:** Index-eligible arrays require identities that survive reorder and insertion. Numeric ordinals do not.

### Solution

- Replace integer IDs with symbolic string IDs such as `ENH-001` through `ENH-010`.
- Preserve ordering separately if order matters; do not overload identity to carry order semantics.
- Update schema or validation logic so future enhancement entries must use the symbolic format.

### CLI app implementation steps

- Read the enhancement array in current order.
- Generate a deterministic mapping from current ordinal position to symbolic ID using zero-padded numbering.
- Patch each object's `id` field from integer to string.
- If any cross-references or narrative text refer to bare numeric enhancement IDs as identifiers, patch them to the new symbolic form.
- Emit a migration map in evidence showing `old_id -> new_id` for auditability.

### Acceptance checks

- Every enhancement object `id` matches `^ENH-\d{3}$`.
- No enhancement `id` is numeric.
- Reordering the array would not change the semantic identity of any enhancement entry.

## 4.3 Resolve `execution_phases` plain-string array

**Source location:** `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json :: /architecture/system_layers/layer_2_validation/components[1]/execution_phases`

**Problem:** `execution_phases` is a list of plain strings rather than objects with stable keys. The CLI app cannot safely build an element identity index from display strings unless the contract explicitly allows that, which it should not by default.

**Why it blocks indexing:** The generator must know whether an array is index-eligible or structural. Plain strings with no identity field cannot satisfy the index-eligible contract.

### Solution

- Make an explicit design decision before indexing work continues.
- Preferred option if the array will be patched by element identity: convert each string into an object with `phase_id`, `display_name`, and optional `gate_range`.
- Alternative option if the array is descriptive only: classify it as structural and exclude it from generated index output.
- Document the chosen classification in the Phase 1 indexing contract.

### CLI app implementation steps

- Inspect current downstream usage of `execution_phases`.
- If no tooling patches individual phases, emit a classification patch or registry entry marking this array structural.
- If tooling needs element-level patching, transform each string into a structured object with stable `phase_id` values such as `VAL-PH-001`, `VAL-PH-002`, etc.
- If transformed, patch schema and validation logic so future entries require the new object shape.

### Acceptance checks

- Either: `execution_phases` is formally classified structural and excluded from indexing; or: every entry has a stable `phase_id` and is indexable.
- There is no ambiguous middle state where plain display strings are treated as durable machine identities.

## 4.4 Add stable `component_id` fields to system layer components

**Source location:** `NEWPHASEPLANPROCESS_TECHNICAL_SPECIFICATION_V3_2.json :: /architecture/system_layers/*/components`

**Problem:** Component arrays currently rely on `name` fields such as `Plan CLI` or `Validation Gate System`. Those are display labels, not stable machine identities. Renaming a component would break any name-based index.

**Why it blocks indexing:** Display names are inherently unstable. Machine addressing needs a separate identity field.

### Solution

- Add a stable `component_id` field to every component object in every system layer.
- Use `component_id` only for identity. Keep `name` as a human-readable display label.
- Choose a deterministic naming scheme such as `COMP-L1-01`, `COMP-L2-02`, etc., based on layer and position at the time of migration.
- Update schema or validation logic so `component_id` is required everywhere these component objects appear.

### CLI app implementation steps

- Enumerate all component arrays under `architecture.system_layers`.
- Assign deterministic `component_id` values by layer and current order.
- Patch each component object to include `component_id` without changing existing `name` text unless separately required.
- If other structures refer to components by `name` as if `name` were identity, add matching `component_id` references or document those references as descriptive only.
- Emit a component migration report showing layer, old name, and new `component_id`.

### Acceptance checks

- Every component object has a non-empty `component_id`.
- `component_id` values are unique across the full technical specification or at minimum unique within the declared namespace policy.
- Generated `by_component_id` index resolves cleanly and does not depend on display-name text.

## 5. Required processing order

- Fix Blocker 1 first because duplicate identities invalidate any gate-level index or validation scan.
- Fix Blocker 2 second because unstable ordinal IDs undermine the array identity model.
- Resolve Blocker 3 before Phase 1 indexing rules are finalized, because it requires an explicit classification choice.
- Fix Blocker 4 before generating spec-level component indexes.

## 6. Final validation routine for the CLI app

- Validate JSON parse success for every modified file.
- Validate blocker-specific identity constraints.
- Validate that any newly introduced ID fields match their declared format.
- Validate that all generated evidence files exist.
- Emit `final_blocker_resolution_report.json` with per-blocker status, changed files, source hashes before and after, and any remaining manual-review items.

## 7. Definition of done

- All four blockers are resolved and validated.
- No indexed collection depends on duplicate, ordinal-only, or display-name-only identities.
- The CLI app can proceed to Phase 1 classification of index-eligible arrays versus structural arrays without ambiguity.
- The final report shows PASS for all blockers.
