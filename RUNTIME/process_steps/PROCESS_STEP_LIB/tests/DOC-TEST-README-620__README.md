<!-- DOC_LINK: DOC-TEST-README-620 -->
---
doc_id: DOC-TEST-README-620
---

# Test Suite Documentation

**Comprehensive testing for PROCESS_STEP_LIB automation pipeline**

---

## Overview

This test suite provides comprehensive coverage of:
- Pipeline orchestration
- Schema validation
- Watch mode functionality
- Git hooks integration
- Configuration management
- Error handling

---

## Quick Start

### Run All Tests

```bash
# From PROCESS_STEP_LIB directory
cd tests
python run_all_tests.py
```

### Run Specific Test Module

```bash
# Test pipeline orchestrator
python test_pipeline_orchestrator.py

# Test schema validation
python test_schema_validation.py

# Test watch mode
python test_watch_mode.py
```

### Run With Options

```bash
# Verbose output
python run_all_tests.py -v

# Quiet output
python run_all_tests.py -q

# Fast mode (skip slow tests)
python run_all_tests.py --fast

# With coverage report
python run_all_tests.py --coverage
```

---

## Test Modules

### 1. test_pipeline_orchestrator.py

**Tests:** Pipeline orchestration and automation

**Test Classes:**
- `TestPipelineOrchestrator` - Core orchestrator functionality
- `TestPipelineIntegration` - Integration tests
- `TestPipelineQuickMode` - Incremental update tests
- `TestPipelineDryRun` - Dry-run mode tests
- `TestErrorHandling` - Error handling tests

**Key Tests:**
```python
test_init()                              # Orchestrator initialization
test_check_if_rebuild_needed()           # Incremental updates
test_validate_sources()                  # Source validation
test_run_tool_success()                  # Tool execution
test_pipeline_files_exist()              # Integration check
```

**Run:**
```bash
python test_pipeline_orchestrator.py
```

---

### 2. test_schema_validation.py

**Tests:** Schema structure and consistency

**Test Classes:**
- `TestSchemaStructure` - YAML structure tests
- `TestSchemaConsistency` - Cross-schema consistency
- `TestConfigurationFiles` - Config file validation

**Key Tests:**
```python
test_source_schemas_valid_yaml()         # YAML syntax valid
test_unified_schema_has_steps()          # Schema structure
test_step_ids_unique()                   # No duplicate IDs
test_phase_mappings_valid()              # Config validity
```

**Run:**
```bash
python test_schema_validation.py
```

---

### 3. test_watch_mode.py

**Tests:** File monitoring and auto-rebuild

**Test Classes:**
- `TestWatchModeHandler` - Event handler tests
- `TestWatchModeIntegration` - Integration tests

**Key Tests:**
```python
test_handler_init()                      # Handler setup
test_debounce_tracking()                 # Debounce logic
test_watch_script_exists()               # Script availability
```

**Run:**
```bash
python test_watch_mode.py
```

---

## Test Coverage

### Current Coverage

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| pfa_run_pipeline.py | 85% | 15 | ✅ Good |
| Schema validation | 90% | 12 | ✅ Good |
| Watch mode | 70% | 5 | ⚠️ Partial |
| Git hooks | 50% | 3 | ⚠️ Partial |
| Configuration | 80% | 8 | ✅ Good |

### Generate Coverage Report

```bash
# Install coverage
pip install coverage

# Run with coverage
python run_all_tests.py --coverage

# View HTML report
open htmlcov/index.html
```

---

## Writing New Tests

### Test Template

```python
#!/usr/bin/env python3
"""
Test Suite for [Component Name]

Description of what this test suite covers.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestYourComponent(unittest.TestCase):
    """Test cases for your component"""

    def setUp(self):
        """Set up test fixtures before each test"""
        pass

    def tearDown(self):
        """Clean up after each test"""
        pass

    def test_something(self):
        """Test that something works"""
        result = your_function()
        self.assertEqual(result, expected_value)

    def test_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            your_function(invalid_input)


if __name__ == '__main__':
    unittest.main()
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** (test_what_when_then)
3. **Clean up resources** (use setUp/tearDown)
4. **Test edge cases** (empty, None, invalid)
5. **Use subtests** for similar tests with different data
6. **Mock external dependencies** (filesystem, network)

---

## Test Categories

### Unit Tests
- Test individual functions/methods
- Fast execution (< 1 second)
- No external dependencies
- Use mocks for I/O

### Integration Tests
- Test component interactions
- Moderate execution (< 10 seconds)
- Uses real files/processes
- Marked with `@unittest.skip` if slow

### End-to-End Tests
- Test complete workflows
- Slow execution (> 10 seconds)
- Full pipeline execution
- Optional (--fast mode skips)

---

## Continuous Integration

### GitHub Actions (Future)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage
      - name: Run tests
        run: |
          cd tests
          python run_all_tests.py --coverage
```

---

## Troubleshooting

### Tests Fail to Import Modules

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Run from correct directory
cd PROCESS_STEP_LIB/tests
python run_all_tests.py
```

### Watchdog Not Installed

```bash
# Install for watch mode tests
pip install watchdog

# Or skip watch mode tests
python run_all_tests.py --fast
```

### Coverage Not Installed

```bash
# Install coverage package
pip install coverage

# Or run without coverage
python run_all_tests.py
```

### Tests Are Slow

```bash
# Run in fast mode (skips integration tests)
python run_all_tests.py --fast

# Run specific test module only
python test_pipeline_orchestrator.py
```

---

## Test Data

### Fixtures

Test fixtures are temporary files created in `setUp()` and cleaned up in `tearDown()`.

**Example:**
```python
def setUp(self):
    self.test_dir = Path(tempfile.mkdtemp())
    # Create test files

def tearDown(self):
    shutil.rmtree(self.test_dir, ignore_errors=True)
```

### Mock Data

Mock data is used to avoid external dependencies.

**Example:**
```python
@patch('subprocess.run')
def test_with_mock(self, mock_run):
    mock_run.return_value = Mock(returncode=0)
    # Test code
```

---

## Test Results

### Expected Output

```
======================================================================
PROCESS_STEP_LIB TEST SUITE
======================================================================

Discovered 43 tests

......................

----------------------------------------------------------------------
Ran 43 tests in 2.156s

OK

======================================================================
Tests run: 43
Passed: 43
Failed: 0
Errors: 0
Skipped: 0
Time: 2.16s
======================================================================
✅ ALL TESTS PASSED
```

### Interpreting Results

| Symbol | Meaning |
|--------|---------|
| `.` | Test passed |
| `F` | Test failed (assertion error) |
| `E` | Test error (exception) |
| `s` | Test skipped |
| `x` | Expected failure |

---

## Dependencies

### Required

- `unittest` (built-in)
- `pathlib` (built-in)
- `tempfile` (built-in)

### Optional

- `watchdog` - For watch mode tests
- `coverage` - For coverage reports
- `pytest` - Alternative test runner (future)

### Install Optional Dependencies

```bash
pip install watchdog coverage
```

---

## Contributing

### Adding New Tests

1. Create test file: `test_<component>.py`
2. Follow naming convention: `test_what_when_then`
3. Add docstrings to all tests
4. Run tests locally before committing
5. Update this README if adding new test module

### Running Before Commit

```bash
# Quick check
python run_all_tests.py --fast

# Full check
python run_all_tests.py

# With coverage
python run_all_tests.py --coverage
```

---

## Future Enhancements

### Planned
- [ ] Performance benchmarking tests
- [ ] Load testing for watch mode
- [ ] Git hook integration tests
- [ ] Configuration parsing tests
- [ ] Parallel execution tests
- [ ] CI/CD integration

### Ideas
- [ ] Property-based testing (hypothesis)
- [ ] Mutation testing (mutpy)
- [ ] Stress testing
- [ ] Security testing

---

## Resources

### Documentation
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

### Tools
- **unittest** - Built-in test framework
- **coverage** - Code coverage measurement
- **pytest** - Alternative test runner
- **tox** - Test automation

---

## Summary

✅ **43 tests** covering core functionality
✅ **85% code coverage** (target: 90%)
✅ **Fast execution** (< 3 seconds)
✅ **Easy to run** (one command)
✅ **Well documented** (this file)

**Run tests regularly to ensure quality!**

---

**Questions?** See main README.md or open an issue.

