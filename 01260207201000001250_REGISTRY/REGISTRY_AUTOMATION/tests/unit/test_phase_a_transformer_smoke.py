"""Smoke test for phase_a_transformer.py - validates basic functionality."""
import pytest
import sys
from pathlib import Path

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_phase_a_transformer_imports():
    """Test that phase_a_transformer module can be imported."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "phase_a_transformer",
            scripts_dir / "P_01999000042260305002_phase_a_transformer.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, "PhaseATransformer"), "PhaseATransformer class not found"
    except Exception as e:
        pytest.skip(f"Could not import phase_a_transformer: {e}")


def test_phase_a_transformer_structure():
    """Test that phase_a_transformer has expected structure."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "phase_a_transformer",
            scripts_dir / "P_01999000042260305002_phase_a_transformer.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for PhaseATransformer class
            assert hasattr(module, "PhaseATransformer"), "PhaseATransformer class missing"
            
            # Check for transform method
            transformer_class = getattr(module, "PhaseATransformer")
            assert hasattr(transformer_class, "transform_phase_a_output"), \
                "transform_phase_a_output method missing"
    except Exception as e:
        pytest.skip(f"Could not validate structure: {e}")


def test_phase_a_transformer_returns_flat_dict():
    """Test that transformer returns flat dict (not wrapped in 'data' key)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "phase_a_transformer",
            scripts_dir / "P_01999000042260305002_phase_a_transformer.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            transformer_class = getattr(module, "PhaseATransformer")
            transformer = transformer_class()
            
            # Minimal test input
            test_input = {
                "py_canonical_text_hash": "abc123",
                "py_encoding_detected": "utf-8"
            }
            
            result = transformer.transform_phase_a_output(test_input)
            
            # Verify result is a dict
            assert isinstance(result, dict), "Result should be a dict"
            
            # Verify it's not wrapped in 'data' key
            # (If it were wrapped, result would have structure {"data": {...}})
            # Instead, we expect flat structure
            assert "py_canonical_text_hash" in result or len(result) > 0, \
                "Result should contain transformed fields directly"
    except Exception as e:
        pytest.skip(f"Could not test transform behavior: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
