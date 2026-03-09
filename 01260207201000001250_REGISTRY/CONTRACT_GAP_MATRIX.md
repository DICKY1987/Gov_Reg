# Contract-Gap Matrix

## Purpose
This matrix is the authoritative catalog of all known issues in the Registry Automation system, expressed in framework-native language. Each row converts a script-centric bug or gap into a contract violation that can be mechanically verified and closed through ProgramSpec/runner/evidence architecture.

## How to Read This Matrix
- **issue_id**: Stable identifier (FCA-NNN format)
- **current_component**: Script or registry component where the gap appears
- **framework_category**: Gate / Phase / Mutation / Transport / Executor
- **broken_contract**: One of 8 standard contract types (see taxonomy below)
- **symptom**: Observable failure behavior
- **root_cause**: Technical explanation of why the contract is broken
- **required_runner_capability**: What a shared runner must enforce to prevent this
- **required_spec_fields**: ProgramSpec fields that should declare the rule
- **evidence_required**: Artifacts that prove the issue is fixed
- **remediation_type**: code_fix / schema_fix / spec_fix / runner_fix / policy_fix / data_backfill
- **verification_test**: Deterministic pass/fail test description
- **priority**: critical / high / medium

## Framework Categories
- **Gate**: Validation, pass/fail, drift checks, invariants
- **Phase**: Multi-step transformation or staged enrichment
- **Mutation**: Patch/apply/update/change to SSOT
- **Transport**: Move/copy/sync/transfer
- **Executor**: Orchestration, task launching, lifecycle control

## Standard Contract Types
1. **input_contract**: Required inputs present and valid before execution
2. **identity_contract**: file_id resolution and canonicalization
3. **output_result_envelope_contract**: Consistent result shape between components
4. **evidence_contract**: Artifacts proving execution outcome
5. **pass_fail_criteria_contract**: Binary gate decision rules
6. **mutation_safety_contract**: Lock, backup, rollback before writes
7. **rollback_contract**: Undo artifacts required before commit
8. **fingerprint_idempotency_contract**: Skip-if-same-inputs behavior

## ProgramSpec Field Mapping
Issues must map to at least one of these ProgramSpec fields:
- **category**: Gate/Phase/Mutation/Transport/Executor classification
- **inputs**: Required input data/files with must_exist checks
- **steps**: Executable commands with preconditions/postconditions
- **locks_write_policy**: Write permissions and conflict prevention
- **evidence_contract**: Required artifacts with validation rules
- **pass_criteria**: Deterministic pass/fail conditions
- **fingerprint_contract**: Idempotency rules based on inputs + version
- **outputs**: Guaranteed artifacts with path policies
- **remediation**: Self-healing rules when failures occur

## Issue Matrix

| issue_id | current_component | framework_category | broken_contract | symptom | root_cause | required_runner_capability | required_spec_fields | evidence_required | remediation_type | verification_test | priority |
|----------|-------------------|--------------------|-----------------|---------|-----------|-----------------------------|----------------------|-------------------|------------------|-------------------|----------|
| FCA-001 | pipeline_runner.py | Executor | output_result_envelope_contract | Valid transformation outputs are silently not staged for patch generation | Executor assumes wrapped transform envelope with "data" key; transformer returns raw transformed payload in direct-call path | Validate result envelope schema before staging; reject or normalize mismatched outputs | outputs, evidence_contract, pass_criteria | Staged output manifest, result-envelope validation report | code_fix + runner_fix | Given valid transform output without "data" wrapper, executor stages patch input exactly once | critical |
| FCA-002 | default_injector.py | Phase | input_contract + pass_fail_criteria_contract | Missing fields remain unset after default injection phase | Column metadata lacks actionable default definitions; all defaults resolve to None | Verify required fields/default-fill expectations after phase execution; enforce declared default semantics from schema | inputs, steps, outputs, pass_criteria | Before/after field population report, default-source manifest | schema_fix + data_backfill | When defaults are declared for eligible columns, post-phase record contains those values | medium |
| FCA-003 | e2e_validator.py | Gate | evidence_contract + pass_fail_criteria_contract | Invalid or incomplete outputs can reach promotion path | Validator checks structure but not full policy-level invariants; no enforcement of required columns from schema | Require mandatory post-execution gate pass before promotion; validate all REQUIRED columns from schema are non-null | evidence_contract, pass_criteria | Validation report against schema/invariant catalog, required-columns check log | runner_fix + schema_fix | Outputs missing required governed fields fail gate and do not promote | high |
| FCA-004 | timestamp_clusterer.py | Phase | input_contract | Timestamp clustering uses wrong field name causing empty clusters | Code reads f.get("created_at") but registry field is allocated_at or created_utc; non-authoritative timestamp source | Validate input schema contract before execution; enforce authoritative field names from column dictionary | inputs, pass_criteria | Field name validation report, cluster population statistics | code_fix | Clusterer reads authoritative timestamp field and produces non-empty clusters | medium |
| FCA-005 | pipeline_runner.py + file_id_reconciler.py | Executor | identity_contract | Pipeline cannot promote records because official 20-digit file_id is missing; SHA256 used as surrogate | Transformer/executor use SHA256 as file_id; registry requires 20-digit numeric ID; no identity resolution layer | Fail closed unless identity contract resolved; block mutation/executor paths until official file_id resolution proven | inputs, pass_criteria, locks_write_policy | Resolved file_id lookup report, identity mapping manifest, promotion status log | spec_fix + code_fix | Given file with SHA256, identity layer resolves 20-digit file_id before executor allows promotion | critical |
| FCA-006 | doc_id_resolver.py | Gate + Mutation | mutation_safety_contract | doc_id collision detection runs but does not update registry; analysis-only mode | Component emits collision analysis report but has no write path to registry; no mutation contract defined | Define mutation-safety contract with write-path ownership; require governed mutation contract before registry writes | category, locks_write_policy, outputs, remediation | Collision resolution plan, mutation ledger, registry update confirmation | runner_fix | doc_id resolver identifies collisions and writes resolution plan to registry under mutation contract | medium |
| FCA-007 | module_dedup.py | Gate + Mutation | mutation_safety_contract | Module deduplication identifies duplicates but does not update registry; analysis-only mode | Component emits deduplication report but has no write path; FILE WATCHER path prefix pollution causes false positives | Define mutation-safety contract; canonicalize paths before comparison; require governed mutation before writes | category, locks_write_policy, outputs, remediation | Deduplication resolution plan, canonicalized path report, registry update confirmation | runner_fix + code_fix | Module deduplicator canonicalizes paths, identifies true duplicates, writes resolution under mutation contract | medium |
| FCA-008 | e2e_validator.py + all gates | Gate | fingerprint_idempotency_contract | No idempotency mechanism exists; validation always re-runs even for identical inputs | No fingerprint contract defined; no skip logic based on inputs + version hash | Compute fingerprint from inputs + spec version; store fingerprints; skip execution if fingerprint exists unless forced | fingerprint_contract, pass_criteria | Fingerprint computation log, fingerprint storage manifest, skip decision log | spec_fix | Given identical inputs and spec version, runner skips execution and returns cached result | high |
| FCA-009 | all scripts | Executor | fingerprint_idempotency_contract | All automation re-runs unconditionally; no replay avoidance | No shared runner enforces fingerprint-based skip logic; scripts have no idempotency layer | Runner computes fingerprint before execution; checks fingerprint store; skips if match found | fingerprint_contract, outputs | Fingerprint match log, skip statistics, cache hit report | runner_fix | Runner computes fingerprint, finds match, skips execution, emits cached result with provenance | high |
| FCA-010 | registry (data) | Mutation | identity_contract | 100% of records missing core metadata: doc_id, file_size, canonicality | Metadata fields not populated during initial intake; no backfill automation exists | Require metadata population contract before records considered complete; block promotion if metadata incomplete | inputs, pass_criteria, outputs | Metadata backfill manifest, before/after record counts, validation report | data_backfill | Given registry records, metadata_backfill.py populates doc_id/file_size/canonicality and validation passes | critical |
| FCA-011 | registry (data) | Mutation | identity_contract | 46 files missing repo_root_id (31.5% incomplete) | repo_root_id inference not automated; manual or missing during intake | Require repo_root_id resolution before file record considered complete; infer from path patterns | inputs, pass_criteria, outputs | repo_root inference manifest, resolution rate report, validation confirmation | data_backfill | Given files with missing repo_root_id, repo_root_inferrer.py infers IDs and validation passes | critical |
| FCA-012 | registry (data) | Mutation | evidence_contract | Empty edges[] array; no relationship tracking populated | Relationship generation not automated; edges builder does not exist | Require relationship population before registry considered complete; generate edges from file references | outputs, evidence_contract, pass_criteria | Edges generation manifest, relationship count report, validation confirmation | data_backfill | Given registry with empty edges[], edges_builder.py generates relationships and validation passes | critical |
| FCA-013 | registry (data) | Mutation | identity_contract | 243/245 entries[] records orphaned (legacy_read_only, no file match) | Orphaned entries not pruned; legacy data retained without cleanup automation | Require entry reconciliation; prune entries without corresponding files; maintain referential integrity | outputs, pass_criteria, locks_write_policy | Entry pruning manifest, before/after orphan counts, referential integrity report | data_backfill | Given orphaned entries[], entries_pruner.py removes unmatched entries and validation passes | critical |
| FCA-014 | column_loader.py + column_validator.py | Phase | input_contract | 6 undocumented columns in registry not present in COLUMN_DICTIONARY | Registry contains columns not defined in authoritative schema; drift between implementation and schema | Enforce schema as authoritative; reject undocumented columns or add to schema under governance | inputs, pass_criteria | Column drift report, schema alignment manifest, governance approval log | schema_fix + policy_fix | Given registry columns, validator fails on undocumented columns or schema updated under governance | high |
| FCA-015 | registry (data) | Mutation | identity_contract | 1 duplicate SHA256 hash detected (ambiguous file_id mapping) | SHA256 collision or duplicate file ingestion without deduplication | Enforce unique SHA256 constraint; detect duplicates at intake; resolve canonical file | pass_criteria, locks_write_policy | Duplicate detection report, canonical file resolution log, uniqueness validation | data_backfill + code_fix | Given duplicate SHA256, deduplicator identifies canonical file and updates references | high |
| FCA-016 | governance_registry_schema.v3.json vs registry | Gate | evidence_contract | Schema version mismatch: registry v4.0 vs schema file v3 | Registry evolved beyond schema file; no version synchronization enforcement | Enforce schema version consistency; validate registry against declared schema version | evidence_contract, pass_criteria | Version consistency report, schema validation log, upgrade manifest | schema_fix | Registry and schema versions match; validation passes with zero version discrepancies | high |
| FCA-017 | null_coalescer.py | Phase | pass_fail_criteria_contract | null_coalescer inert because default_injector provides no defaults | Depends on default_injector which is broken; no null-handling logic active | Verify preconditions before phase execution; ensure upstream phase postconditions met | inputs, steps, pass_criteria | Null coalescing report, before/after null counts, precondition validation log | code_fix | Given records with nulls and active defaults, null_coalescer reduces null count to target level | medium |
| FCA-018 | documentation files | Gate | evidence_contract | Documentation drift: SCRIPT_INDEX.md does not list sha256_backfill.py; outdated descriptions | Documentation manually maintained; no automated sync with actual scripts | Require documentation generation from code/schema; validate docs against implementation | evidence_contract, outputs | Documentation coverage report, drift detection log, auto-generation manifest | runner_fix + code_fix | Given scripts directory, doc generator updates SCRIPT_INDEX.md and validation passes | medium |
| FCA-019 | phase_a_transformer.py + phase B/C integration | Phase | output_result_envelope_contract | Incomplete phase B/C integration; output shape assumptions brittle | Phase B/C not fully implemented; transformer output shape not formally contracted | Enforce output contract for all phases; validate phase output against contract before handoff | outputs, evidence_contract, pass_criteria | Phase integration manifest, contract validation log, handoff success report | spec_fix + code_fix | Given phase A output, phase B consumes under contract and validation passes | medium |

## Verification Closure Rules
Every matrix row must have:
1. A framework category (not "mixed" or "unclear")
2. A broken contract from the standard 8 types
3. A required_runner_capability stated in active voice
4. At least one required_spec_field
5. Concrete evidence_required (not "TBD" or "various")
6. A controlled remediation_type value
7. A deterministic verification_test with pass/fail criteria

## Change Control Rules
- New rows require issue_id assignment in FCA-NNN sequence
- Contract type additions require taxonomy update and approval
- Remediation type additions require controlled vocabulary update
- Priority changes require impact assessment
- Row closure requires verification_test execution and evidence

## Completion Criteria
This matrix is complete when:
- All source issues from REG_AUTO_PLAN.txt are represented
- All issues from resilient-skipping-rainbow.md are represented
- All issues from ChatGPT Alignment Assessment are represented
- No row has empty required fields
- Every row maps into at least one phase/step/gate in the execution plan
- All verification tests are deterministic and executable
