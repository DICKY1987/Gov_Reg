<!-- DOC_LINK: DOC-PATTERN-README-424 -->
---
doc_id: DOC-PATTERN-README-424
---

# Pattern ID Subsystem

**Version:** 1.0.0
**Status:** ACTIVE
**Created:** 2025-12-29

---

## Overview

The Pattern ID subsystem provides stable identity for **execution patterns** - multi-file concepts that represent reusable workflows. A pattern typically consists of:

- **Specification** (optional): Pattern documentation
- **Executor**: Implementation file(s) that execute the pattern
- **Tests** (optional): Test coverage for the pattern

This enables:
- **Pattern Tracking**: Know which patterns exist and where they're implemented
- **Pattern Coverage**: Track which patterns have tests
- **Pattern Evolution**: Track pattern changes over time
- **Documentation**: Cross-reference patterns with their implementations

## Pattern ID Format

```
PATTERN-{CATEGORY}-{SEQUENCE}
```

**Examples:**
- `PATTERN-EXEC-DOC-ID-SCANNING-001` - Execution pattern #1
- `PATTERN-VALID-DOC-ID-CLEANUP-002` - Validation pattern #2
- `PATTERN-DOC-003` - Documentation pattern #3
- `PATTERN-TEST-004` - Test pattern #4

## Categories

| Category | Prefix | Description |
|----------|--------|-------------|
| exec | EXEC | Execution patterns (batch ops, atomic ops, guards) |
| validation | VALID | Validation patterns |
| doc | DOC | Documentation patterns |
| test | TEST | Test patterns |

## Directory Structure

```
pattern_id/
├── 1_CORE_OPERATIONS/         # Pattern management
│   ├── pattern_id_scanner.py  # Discover pattern references
│   └── pattern_id_manager.py  # Create and link patterns
├── 2_VALIDATION_FIXING/       # Validation tools
│   └── validate_pattern_completeness.py
├── 3_AUTOMATION_HOOKS/        # (reserved)
├── 4_REPORTING_MONITORING/    # Reports and dashboards
├── 5_REGISTRY_DATA/           # SSOT registry
│   ├── PAT_ID_REGISTRY.yaml   # Central registry
│   ├── patterns_inventory.jsonl # Scan results
│   └── pattern_references.json  # Reference tracking
├── 6_TESTS/                   # Test suite
├── 7_CLI_INTERFACE/           # Unified CLI
├── common/                    # Shared utilities
└── docs/                      # Documentation
```

## Quick Start

### 1. Scan for Pattern References

```bash
python SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_scanner.py scan
```

This discovers pattern references in code (e.g., `PATTERN: PATTERN-EXEC-DOC-ID-SCANNING-001`).

### 2. Create a New Pattern

```bash
python SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_manager.py create \
    --name "Batch Doc ID Minting" \
    --category exec \
    --description "Mint doc_ids in batch with validation"
```

### 3. Link Files to Pattern

```bash
# Link executor
python SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_manager.py link \
    --pattern-id PATTERN-EXEC-DOC-ID-SCANNING-001 \
    --file "SUB_DOC_ID/1_CORE_OPERATIONS/doc_id_scanner.py" \
    --role executor \
    --doc-id DOC-SCRIPT-DOC-ID-SCANNER-046

# Link tests
python SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_manager.py link \
    --pattern-id PATTERN-EXEC-DOC-ID-SCANNING-001 \
    --file "SUB_DOC_ID/6_TESTS/test_doc_id_system.py" \
    --role test
```

### 4. List Patterns

```bash
python SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_manager.py list
```

### 5. Validate Completeness

```bash
python SUB_DOC_ID/pattern_id/1_CORE_OPERATIONS/pattern_id_manager.py validate
```

## Pattern Concept

### What is a Pattern?

A **pattern** is a multi-file logical entity representing a reusable execution workflow:

```
Pattern: "Doc ID Scanning"
├── Specification (optional): docs/patterns/doc-id-scanning.md
├── Executor: 1_CORE_OPERATIONS/doc_id_scanner.py
└── Tests: 6_TESTS/test_doc_id_scanner.py
```

### Pattern Roles

| Role | Description | Required? |
|------|-------------|-----------|
| `spec` | Pattern documentation/specification | Optional |
| `executor` | Implementation file(s) | **Required** |
| `test` | Test coverage | Recommended |

### Multiple Files Per Role

A pattern can have multiple executors or test files:

```yaml
pattern_id: PATTERN-EXEC-DOC-ID-SCHEDULED-REPORTS-005
name: "Multi-File Pattern"
files:
  executor:
    - path: scanner.py
      doc_id: DOC-SCRIPT-SCANNER-XXX
    - path: processor.py
      doc_id: DOC-SCRIPT-PROCESSOR-XXX
  test:
    - path: test_scanner.py
    - path: test_processor.py
```

## Current Status

**Total Patterns:** 3
**Breakdown:**
- Execution: 2
- Validation: 1

**Coverage:**
- Patterns with executors: 3/3 (100%)
- Patterns with tests: 1/3 (33%)
- Patterns with specs: 0/3 (0%)

## Registry Schema

```yaml
doc_id: DOC-REGISTRY-PATTERN-001
meta:
  version: 1.0.0
  total_patterns: 3

categories:
  exec:
    prefix: EXEC
    next_id: 3
  validation:
    prefix: VALID
    next_id: 2

patterns:
  - pattern_id: PATTERN-EXEC-DOC-ID-SCANNING-001
    category: exec
    name: "Doc ID Scanning"
    description: "Scan repository files for doc_id presence"
    status: active
    files:
      executor:
        - path: SUB_DOC_ID/1_CORE_OPERATIONS/doc_id_scanner.py
          doc_id: DOC-SCRIPT-DOC-ID-SCANNER-046
      test:
        - path: SUB_DOC_ID/6_TESTS/test_doc_id_system.py
          doc_id: DOC-TEST-DOC-ID-SYSTEM-001
    first_seen: '2025-12-29T10:00:00Z'
    last_seen: '2025-12-29T10:00:00Z'
```

## Integration with CI/CD

Validators can run in CI gates to ensure:
- ✅ All patterns have executors
- ⚠️ Patterns without tests trigger warnings
- ⚠️ Patterns without specs trigger warnings
- ✅ Pattern IDs are unique

## Pattern References in Code

### Python Files

```python
# PATTERN_ID: PATTERN-EXEC-DOC-ID-SCANNING-001
"""
Doc ID Scanner

PURPOSE: Scan repository for doc_id presence
PATTERN: PATTERN-EXEC-DOC-ID-SCANNING-001
"""
```

### Markdown Files

```markdown
---
doc_id: DOC-SPEC-PATTERN-BATCH-MINT-001
pattern_id: PATTERN-EXEC-DOC-ID-SCHEDULED-REPORTS-005
---

# Pattern: Batch Doc ID Minting

This pattern describes...
```

## Related Documentation

- **Doc ID System**: `SUB_DOC_ID/README.md`
- **Trigger ID System**: `SUB_DOC_ID/trigger_id/README.md`
- **Governance Requirements**: `SUB_DOC_ID/docs/ID_SYSTEM_GOVERNANCE_REQUIREMENTS.md`

## Maintenance

### Adding New Patterns

1. Create pattern: `python pattern_id_manager.py create --name "..." --category exec`
2. Link executor: `python pattern_id_manager.py link --pattern-id PATTERN-... --file ... --role executor`
3. Link tests: `python pattern_id_manager.py link --pattern-id PATTERN-... --file ... --role test`
4. Validate: `python pattern_id_manager.py validate`

### Evolving Patterns

Patterns can evolve over time:
- Add new executor files to existing patterns
- Add test coverage to patterns
- Add specifications to document patterns
- Mark patterns as `deprecated` when no longer used

### Pattern Coverage Metrics

Track pattern health:
- % of patterns with tests
- % of patterns with specs
- % of patterns with documentation
- Pattern usage frequency (via references)

---

**Last Updated:** 2025-12-29
**Maintained By:** SUB_DOC_ID subsystem
**Registry:** `5_REGISTRY_DATA/PAT_ID_REGISTRY.yaml`
