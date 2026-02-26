# DOC_ID: DOC-SCRIPT-1041
# AI CLI Provenance Solution - Directory Structure

**Purpose**: Flat structure with all files in root directory.

---

## Solution Root (Flat Structure)

```
C:\Users\richg\ALL_AI\AI_CLI_PROVENANCE_SOLUTION\
├── README.md                                          # Solution overview
├── DIRECTORY_STRUCTURE.md                             # This file
├── IMPLEMENTATION_CHECKLIST.md                        # Phase-by-phase checklist
├── SETUP.md                                           # Setup instructions
├── requirements.txt                                   # Python dependencies
├── .gitignore                                         # Git exclusions
│
├── Deterministic Codebase Triage & De-Noise System.md # System architecture
├── py_identify_soultion.yml                           # Current rules (50+ evidence paths)
├── abundant-coalescing-treasure.md                    # 20-week roadmap
└── AI_CLI_PROVENANCE_INTEGRATION_PLAN.md              # Detailed integration plan
```

All implementation files (collectors, validators, tests, rules, tools, docs, examples) will be added as individual files in this root directory as they are created.

---

## Integration with Existing Systems

### DOC_ID System
**Location**: `C:\Users\richg\ALL_AI\RUNTIME\doc_id\SUB_DOC_ID\`

**Integration**: AI CLI collector reads `5_REGISTRY_DATA\DOC_ID_REGISTRY.yaml` to map file paths → doc_ids.

### Relationship Index
**Location**: `C:\Users\richg\ALL_AI\RUNTIME\relationship_index\SUB_RELATIONSHIP_INDEX\`

**Integration**: Graph reachability combines with AI provenance for comprehensive analysis.

### Identification Criteria
**Location**: `C:\Users\richg\ALL_AI\RUNTIME\identification_criteria\`

**Integration**: This solution extends the identification criteria system with AI provenance collectors.

---

## Size Estimates

| Folder | Files | Lines of Code | Storage |
|--------|-------|---------------|---------|
| 0_REFERENCE_DOCS | 4 | ~10,000 | 500 KB |
| 1_SCHEMAS | 3 | ~500 | 50 KB |
| 2_COLLECTORS | 6 | ~2,000 | 100 KB |
| 3_VALIDATORS | 4 | ~800 | 40 KB |
| 4_TESTS | 6 | ~1,500 | 75 KB |
| 5_RULES | 4 | ~300 | 30 KB |
| 6_TOOLS | 3 | ~600 | 30 KB |
| 7_DOCS | 4 | ~3,000 | 150 KB |
| 8_EXAMPLES | 3 | ~500 | 50 KB |
| **Total** | **37** | **~19,200** | **~1 MB** |

*Note: SQLite index size depends on log volume (~1MB per 10K records)*

---

**Last Updated**: 2026-01-04
**Version**: 1.0
