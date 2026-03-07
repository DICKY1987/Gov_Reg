# DOC_ID: DOC-SCRIPT-1180
# Stable ID Testing - Quick Reference Card

## Test Locations
```
RUNTIME/doc_id/SUB_DOC_ID/6_TESTS/
```

## Quick Commands

### Run All Tests
```bash
cd RUNTIME/doc_id/SUB_DOC_ID/6_TESTS
python run_tests.py
```

### Run with Coverage
```bash
python run_tests.py --coverage
```

### Run Specific Tests
```bash
python run_tests.py -m syntax        # Syntax tests only
python run_tests.py -m registry      # Registry tests only
python run_tests.py -m integration   # Integration tests only
python run_tests.py -m critical      # Critical tests only
```

### Run Specific File
```bash
python run_tests.py -f test_syntax_all.py
```

## Test Status

| Test Suite | Status | Pass Rate |
|------------|--------|-----------|
| Syntax Validation | ✅ PASS | 7/7 (100%) |
| Registry Integrity | ⚠️ PARTIAL | 10/15 (67%) |
| Integration Tests | ⏳ READY | Not executed |

## Current Issues

### Critical (2)
1. **Registry Structure** - DOC_ID_REGISTRY flat list vs dict
2. **Field Naming** - type_id vs id_type inconsistency

### High (2)
3. **Coverage** - 9.24% (target: 80%)
4. **Integration** - Not fully executed

## Documentation

| File | Purpose |
|------|---------|
| README_TESTING.md | Complete testing guide |
| TEST_RESULTS_SUMMARY.md | Test results analysis |
| STABLE_ID_TESTING_SUITE_COMPLETE.md | Full implementation report |
| STABLE_ID_SESSION_SUMMARY_2026-01-03.md | Session summary |

## Test Files Created

- `test_suite_master.py` - Master orchestrator
- `test_syntax_all.py` - Syntax validation (✅ 100%)
- `test_registry_integrity.py` - Registry validation (⚠️ 67%)
- `test_integration_unified.py` - Integration tests (⏳)
- `conftest.py` - Pytest configuration
- `run_tests.py` - CLI test runner

## Next Steps

1. Fix registry structure (2-4h)
2. Run full test suite (1-2h)
3. Improve coverage to 80% (8-16h)
4. CI/CD integration (2-4h)

## Status
- Infrastructure: ✅ OPERATIONAL
- Code Syntax: ✅ VALID
- Registry: ⚠️ ISSUES
- Overall: 🟡 FUNCTIONAL

Last Updated: 2026-01-03
