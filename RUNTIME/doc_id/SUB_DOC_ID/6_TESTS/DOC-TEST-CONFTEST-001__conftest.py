# DOC_LINK: DOC-TEST-CONFTEST-001
# DOC_ID: DOC-TEST-CONFTEST-001
"""
Pytest Configuration for Stable ID Test Suite
doc_id: DOC-TEST-CONFTEST-001
Shared fixtures and configuration
"""

import pytest
from pathlib import Path
import sys
import yaml
import json

# Add common modules to path for all tests
@pytest.fixture(scope="session", autouse=True)
def add_common_to_path():
    """Automatically add common modules to Python path"""
    base_path = Path(__file__).parent.parent
    common_path = base_path / "common"
    if common_path.exists() and str(common_path) not in sys.path:
        sys.path.insert(0, str(common_path))

@pytest.fixture(scope="session")
def base_path():
    """Base path for stable ID system"""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def repo_root():
    """Repository root path"""
    return Path(__file__).parent.parent.parent.parent.parent

@pytest.fixture
def doc_id_registry_path(base_path):
    """Path to DOC_ID_REGISTRY.yaml"""
    return base_path / "5_REGISTRY_DATA" / "DOC_ID_REGISTRY.yaml"

@pytest.fixture
def trigger_id_registry_path(base_path):
    """Path to TRIGGER_ID_REGISTRY.yaml"""
    return base_path / "trigger_id" / "5_REGISTRY_DATA" / "TRIGGER_ID_REGISTRY.yaml"

@pytest.fixture
def pattern_id_registry_path(base_path):
    """Path to PAT_ID_REGISTRY.yaml"""
    return base_path / "pattern_id" / "5_REGISTRY_DATA" / "PAT_ID_REGISTRY.yaml"

@pytest.fixture
def meta_registry_path(base_path):
    """Path to ID_TYPE_REGISTRY.yaml"""
    return base_path / "ID_TYPE_REGISTRY.yaml"

@pytest.fixture
def load_yaml():
    """Helper to load YAML files"""
    def _load(path):
        with open(path) as f:
            return yaml.safe_load(f)
    return _load

@pytest.fixture
def load_json():
    """Helper to load JSON files"""
    def _load(path):
        with open(path) as f:
            return json.load(f)
    return _load

# Custom markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "syntax: tests for Python syntax validation"
    )
    config.addinivalue_line(
        "markers", "registry: tests for registry integrity"
    )
    config.addinivalue_line(
        "markers", "integration: tests for cross-system integration"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take significant time"
    )
    config.addinivalue_line(
        "markers", "critical: critical tests that must pass"
    )

# Test report customization
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Add custom test result handling"""
    if call.when == "call":
        if hasattr(item, 'obj') and hasattr(item.obj, '__doc__'):
            # Could add custom logging here
            pass
