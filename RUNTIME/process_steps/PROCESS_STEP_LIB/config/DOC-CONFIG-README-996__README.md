<!-- DOC_LINK: DOC-CONFIG-README-996 -->
---
doc_id: DOC-CONFIG-README-996
---

# Config Directory

Configuration files for schema processing tools.

## Files

### phase_mappings.yaml
Maps original phases from source schemas to universal phase taxonomy.

**Structure:**
```yaml
universal_phases:
  - PHASE_0_BOOTSTRAP
  - PHASE_1_PLANNING
  # ... 9 phases total

mappings:
  master_splinter:
    "MS_Initialization":
      universal_phase: "PHASE_0_BOOTSTRAP"
      substage: "Environment Setup"
    # ... more mappings

  patterns:
    "Pattern Discovery":
      universal_phase: "PHASE_1_PLANNING"
      substage: "Pattern Analysis"
    # ... more mappings
```

### operation_taxonomy.yaml
Categorizes operation kinds into universal categories.

**Structure:**
```yaml
universal_categories:
  - ANALYSIS
  - CONSTRUCTION
  - VALIDATION
  - ORCHESTRATION
  - MONITORING
  - ERROR_HANDLING

mappings:
  master_splinter:
    "orchestration": "ORCHESTRATION"
    "analysis": "ANALYSIS"
    # ... more mappings

  patterns:
    "pattern_detection": "ANALYSIS"
    "pattern_application": "CONSTRUCTION"
    # ... more mappings
```

## Usage

These configuration files are automatically loaded by the merge and processing tools:

```bash
cd ../tools
python pfa_merge_schemas.py --all \
  --phase-mappings phase_mappings.yaml \
  --operation-taxonomy operation_taxonomy.yaml \
  --output ../schemas/unified/PFA_E2E_UNIFIED_PROCESS_STEPS_SCHEMA.yaml
```

Default behavior uses these files from the `config/` directory.

## Editing Guidelines

### Adding New Phase Mappings
1. Add the original phase name from your source schema
2. Map it to one of the 9 universal phases
3. Specify a substage (optional but recommended)
4. Run the merge tool to test

### Adding New Operation Mappings
1. Add the original operation_kind from your source schema
2. Map it to one of the 6 universal categories
3. Ensure consistency across similar operations
4. Run validation to verify

## Validation

After editing, validate your changes:
```bash
cd ../tools
python pfa_merge_schemas.py --all --dry-run --output test.yaml
```

This will report any unmapped phases or operations.
