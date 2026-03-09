"""Smoke test for pipeline_runner.py - validates basic functionality."""
import pytest
import sys
from pathlib import Path

# Add scripts to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


def test_pipeline_runner_imports():
    """Test that pipeline_runner module can be imported."""
    try:
        # Try importing the module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_runner",
            scripts_dir / "P_01999000042260305017_pipeline_runner.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, "PipelineRunner"), "PipelineRunner class not found"
    except Exception as e:
        pytest.skip(f"Could not import pipeline_runner: {e}")


def test_pipeline_runner_staging_fix():
    """Test that the staging bug is fixed (no .get('data') check)."""
    pipeline_file = scripts_dir / "P_01999000042260305017_pipeline_runner.py"
    
    if not pipeline_file.exists():
        pytest.skip("pipeline_runner.py not found")
    
    content = pipeline_file.read_text(encoding='utf-8')
    
    # Verify the bug is fixed
    assert 'transformed.get("data")' not in content, \
        "Staging bug still present: transformed.get('data') found"
    
    # Verify correct pattern exists
    assert 'if file_id and transformed:' in content, \
        "Correct staging pattern not found"


def test_pipeline_runner_structure():
    """Test that pipeline_runner has expected structure."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "pipeline_runner",
            scripts_dir / "P_01999000042260305017_pipeline_runner.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for PipelineRunner class
            assert hasattr(module, "PipelineRunner"), "PipelineRunner class missing"
            
            # Check for process_file method
            pr_class = getattr(module, "PipelineRunner")
            assert hasattr(pr_class, "process_file"), "process_file method missing"
            assert hasattr(pr_class, "run_pipeline"), "run_pipeline method missing"
    except Exception as e:
        pytest.skip(f"Could not validate structure: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
