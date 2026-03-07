# Stable ID System Testing Suite
doc_id: DOC-TEST-README-001

## Overview

Comprehensive testing suite for the entire Stable ID system, covering:
- Syntax validation
- Registry integrity
- Integration testing
- Cross-ID-type functionality
- Automation and tooling

## Test Structure

```
6_TESTS/
├── conftest.py                      # Pytest configuration & fixtures
├── run_tests.py                     # Test runner script
├── test_suite_master.py             # Master test suite
├── test_syntax_all.py               # Syntax validation for all Python files
├── test_registry_integrity.py       # Registry structure validation
├── test_integration_unified.py      # Cross-system integration tests
├── test_doc_id_compliance.py        # Doc ID compliance tests
├── test_doc_id_system.py            # Doc ID system tests
└── README_TESTING.md                # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py --coverage

# Run specific marker
python run_tests.py -m syntax
python run_tests.py -m registry
python run_tests.py -m integration

# Run specific test file
python run_tests.py -f test_syntax_all.py

# Verbose output
python run_tests.py -v
```

### Using pytest directly

```bash
# All tests
pytest -v

# Specific test file
pytest test_syntax_all.py -v

# With coverage
pytest --cov=. --cov-report=html

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## Test Categories

### Syntax Tests (`test_syntax_all.py`)
- Validates Python syntax for all `.py` files
- Tests compilation of core operations, validators, automation
- Ensures importability of key modules

### Registry Tests (`test_registry_integrity.py`)
- DOC_ID_REGISTRY.yaml structure and uniqueness
- TRIGGER_ID_REGISTRY.yaml structure
- PAT_ID_REGISTRY.yaml structure
- ID_TYPE_REGISTRY.yaml (meta-registry) integrity
- Field validation and format checking

### Integration Tests (`test_integration_unified.py`)
- Unified sync functionality
- Cross-registry operations
- Unified validation layer
- Pre-commit hook integration
- Dashboard functionality

### Master Suite (`test_suite_master.py`)
- Runs all test categories
- Generates comprehensive coverage report
- Suitable for CI/CD pipelines

## Test Markers

Custom markers for selective test execution:

- `@pytest.mark.syntax` - Syntax validation tests
- `@pytest.mark.registry` - Registry integrity tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.critical` - Critical tests that must pass

Usage:
```bash
pytest -m "critical"
pytest -m "syntax or registry"
pytest -m "not slow"
```

## Fixtures

Common fixtures available to all tests (defined in `conftest.py`):

- `base_path` - Path to SUB_DOC_ID directory
- `repo_root` - Path to repository root
- `doc_id_registry_path` - Path to DOC_ID_REGISTRY.yaml
- `trigger_id_registry_path` - Path to TRIGGER_ID_REGISTRY.yaml
- `pattern_id_registry_path` - Path to PAT_ID_REGISTRY.yaml
- `meta_registry_path` - Path to ID_TYPE_REGISTRY.yaml
- `load_yaml` - Helper function to load YAML files
- `load_json` - Helper function to load JSON files

## Coverage Reports

After running with `--coverage`:

```bash
# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows

# Terminal report shows missing lines
```

## CI/CD Integration

For GitHub Actions or other CI systems:

```yaml
- name: Run Stable ID Tests
  run: |
    cd RUNTIME/doc_id/SUB_DOC_ID/6_TESTS
    python run_tests.py --coverage
```

## Adding New Tests

1. Create test file: `test_<feature>.py`
2. Import pytest: `import pytest`
3. Use fixtures from conftest.py
4. Follow naming convention: `test_<what_is_tested>`
5. Add docstrings with doc_ids
6. Use appropriate markers

Example:
```python
"""
Feature Tests
doc_id: DOC-TEST-FEATURE-001
"""

import pytest

@pytest.mark.critical
def test_feature_works(base_path):
    """Test that feature works correctly"""
    assert True
```

## Troubleshooting

### Import Errors
- Ensure `conftest.py` is present (adds common modules to path)
- Check `sys.path` includes common directory

### Syntax Errors in Tests
- Run: `python -m py_compile test_file.py`
- Fix any syntax errors before running test suite

### Missing Dependencies
```bash
pip install pytest pytest-cov pytest-xdist pyyaml
```

## Best Practices

1. **Test Isolation** - Each test should be independent
2. **Clear Assertions** - Use descriptive assertion messages
3. **Fixtures** - Reuse fixtures from conftest.py
4. **Markers** - Tag tests appropriately
5. **Documentation** - Add docstrings with doc_ids
6. **Fast Tests** - Keep tests fast; mark slow tests with `@pytest.mark.slow`

## Maintenance

- Update tests when adding new ID types
- Add tests for new validators and tools
- Keep coverage above 80%
- Run full suite before major changes
