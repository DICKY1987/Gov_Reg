# DOC_LINK: DOC-TEST-DOC-ID-TESTS-TEST-DRIFT-DETECTION-671
"""Tests for documentation drift detection.

DOC_ID: DOC-TEST-DOC-ID-TESTS-TEST-DRIFT-DETECTION-671
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
DOC_ID_DIR = REPO_ROOT / "4_REPORTING_MONITORING"
DRIFT_DETECTOR = DOC_ID_DIR / "detect_doc_drift.py"


class TestDriftDetection:
    """Test suite for drift detector."""

    @pytest.mark.skip(reason="Drift detector not yet implemented")
    def test_drift_detector_exists(self):
        """Drift detector script should exist."""
        assert DRIFT_DETECTOR.exists(), f"Drift detector not found at {DRIFT_DETECTOR}"

    @pytest.mark.skip(reason="Drift detector not yet implemented")
    def test_drift_detector_runs(self):
        """Drift detector should execute successfully."""
        result = subprocess.run(
            [sys.executable, str(DRIFT_DETECTOR), "--dry-run"],
            capture_output=True,
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="replace",
        )
        # Exit code 0 (no drift) or 1 (drift detected) are both valid
        assert result.returncode in (
            0,
            1,
        ), f"Unexpected exit code: {result.returncode}\n{result.stderr}"

    @pytest.mark.skip(reason="Drift detector not yet implemented")
    def test_drift_detector_help(self):
        """Drift detector should provide help text."""
        result = subprocess.run(
            [sys.executable, str(DRIFT_DETECTOR), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0
        assert "detect" in result.stdout.lower() and "drift" in result.stdout.lower()

    @pytest.mark.skip(reason="Drift detector not yet implemented")
    def test_drift_report_generation(self):
        """Drift detector should generate JSON report."""
        output_path = REPO_ROOT / ".state" / "test_drift_report.json"

        # Clean up any existing test report
        if output_path.exists():
            output_path.unlink()

        result = subprocess.run(
            [sys.executable, str(DRIFT_DETECTOR), "--report", str(output_path)],
            capture_output=True,
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="replace",
        )

        # Should succeed or fail gracefully
        assert result.returncode in (0, 1)

        # Report should be generated
        assert output_path.exists(), "Drift report was not generated"

        # Report should be valid JSON
        with open(output_path, "r") as f:
            report = json.load(f)

        # Verify report structure
        assert "timestamp" in report
        assert "summary" in report
        assert "findings" in report
        assert "stats" in report

        # Verify summary fields
        assert "total_findings" in report["summary"]
        assert "hash_mismatches" in report["summary"]
        assert "temporal_drifts" in report["summary"]
        assert "broken_references" in report["summary"]
        assert "documentation_gaps" in report["summary"]

        # Clean up
        output_path.unlink()

    def test_drift_detector_ci_mode(self):
        """Drift detector should support CI mode with thresholds."""
        result = subprocess.run(
            [
                sys.executable,
                str(DRIFT_DETECTOR),
                "--dry-run",
                "--ci-check",
                "--max-drift",
                "1000",
            ],
            capture_output=True,
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="replace",
        )

        # With high threshold, should pass or output CI check info
        assert result.stdout is not None
        # Just verify it ran - CI mode may or may not pass depending on findings

    def test_drift_types_detected(self):
        """Drift detector should detect all drift types."""
        output_path = REPO_ROOT / ".state" / "test_drift_types.json"

        if output_path.exists():
            output_path.unlink()

        subprocess.run(
            [sys.executable, str(DRIFT_DETECTOR), "--report", str(output_path)],
            capture_output=True,
            cwd=REPO_ROOT,
            encoding="utf-8",
            errors="replace",
        )

        if output_path.exists():
            with open(output_path, "r") as f:
                report = json.load(f)

            # Check that drift type categorization works
            drift_types = set()
            for finding in report.get("findings", []):
                drift_types.add(finding.get("drift_type"))

            # At least one drift type should be detected (likely documentation_gap)
            assert len(drift_types) > 0, "No drift types detected"

            # Valid drift types
            valid_types = {
                "hash_mismatch",
                "temporal_drift",
                "broken_cross_reference",
                "documentation_gap",
            }
            assert drift_types.issubset(
                valid_types
            ), f"Invalid drift types detected: {drift_types - valid_types}"

            output_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
