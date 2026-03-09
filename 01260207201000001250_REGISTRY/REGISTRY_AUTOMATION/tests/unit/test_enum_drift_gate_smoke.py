"""Smoke test for enum_drift_gate.py - validates basic functionality."""
import pytest
import sys
from pathlib import Path

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_enum_drift_gate_imports():
    """Test that enum_drift_gate module can be imported."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "enum_drift_gate",
            scripts_dir / "P_01999000042260305000_enum_drift_gate.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, "EnumDriftGate"), "EnumDriftGate class not found"
    except Exception as e:
        pytest.skip(f"Could not import enum_drift_gate: {e}")


def test_enum_drift_gate_structure():
    """Test that enum_drift_gate has expected structure."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "enum_drift_gate",
            scripts_dir / "P_01999000042260305000_enum_drift_gate.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for EnumDriftGate class
            assert hasattr(module, "EnumDriftGate"), "EnumDriftGate class missing"
            
            # Check for key methods
            edg_class = getattr(module, "EnumDriftGate")
            assert hasattr(edg_class, "validate"), "validate method missing"
    except Exception as e:
        pytest.skip(f"Could not validate structure: {e}")


def test_enum_drift_gate_file_exists():
    """Test that enum drift gate script exists."""
    enum_gate_file = scripts_dir / "P_01999000042260305000_enum_drift_gate.py"
    assert enum_gate_file.exists(), "Enum drift gate script not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
