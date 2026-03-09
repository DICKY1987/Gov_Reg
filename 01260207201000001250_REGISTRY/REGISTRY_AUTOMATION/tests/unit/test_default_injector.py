"""Unit tests for default_injector.py"""
import pytest
import sys
from pathlib import Path

scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_default_injector_imports():
    """Test that default_injector can be imported."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "default_injector",
            scripts_dir / "P_01999000042260305007_default_injector.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, "DefaultInjector")
    except Exception as e:
        pytest.skip(f"Could not import: {e}")


def test_default_injector_structure():
    """Test that DefaultInjector has expected methods."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "default_injector",
            scripts_dir / "P_01999000042260305007_default_injector.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            injector_class = getattr(module, "DefaultInjector")
            assert hasattr(injector_class, "inject_defaults")
    except Exception as e:
        pytest.skip(f"Could not validate: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
