#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DOC_ID: DOC-TEST-0643
"""
Integration Tests for File Watcher v2 Hardened - REAL END-TO-END TESTS

Tests the ACTUAL production code with real detection logic.
NO MOCKS. NO DUPLICATED LOGIC.

Run: pytest test_file_watcher_v2_integration.py -v
"""

from importlib import util
from pathlib import Path

# Import the REAL production functions
_module_path = Path(__file__).resolve().parent / "DOC-SCRIPT-DOC-ID-FILE-WATCHER-HARDENED-010__file_watcher_v2_hardened.py"
_spec = util.spec_from_file_location("file_watcher_v2_hardened", _module_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load module from {_module_path}")
_module = util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
smart_category_detection = _module.smart_category_detection
check_file_stable = _module.check_file_stable
REPO_ROOT = _module.REPO_ROOT

import pytest


class TestSmartCategoryDetection:
    """Test REAL smart_category_detection() function"""

    def test_segment_matching_tests_directory(self):
        """Test files under /tests/ directory"""
        path = REPO_ROOT / 'tests' / 'unit' / 'example.py'
        assert smart_category_detection(path) == 'test'

    def test_segment_matching_scripts_directory(self):
        """Test files under /scripts/ directory"""
        path = REPO_ROOT / 'scripts' / 'deploy.py'
        assert smart_category_detection(path) == 'script'

    def test_segment_matching_docs_directory(self):
        """Test files under /docs/ directory"""
        path = REPO_ROOT / 'docs' / 'README.md'
        assert smart_category_detection(path) == 'guide'

    def test_segment_matching_governance(self):
        """Test files under /GOVERNANCE/"""
        path = REPO_ROOT / 'GOVERNANCE' / 'policy.md'
        assert smart_category_detection(path) == 'policy'

    def test_filename_pattern_test_prefix(self):
        """Test test_*.py files"""
        path = REPO_ROOT / 'automation' / 'test_example.py'
        # Should match filename pattern before falling back to segment
        assert smart_category_detection(path) == 'test'

    def test_filename_pattern_test_suffix(self):
        """Test *_test.py files"""
        path = REPO_ROOT / 'utils' / 'parser_test.py'
        assert smart_category_detection(path) == 'test'

    def test_filename_pattern_powershell_script(self):
        """Test .ps1 files"""
        path = REPO_ROOT / 'automation' / 'deploy.ps1'
        # Segment 'automation' should match first
        assert smart_category_detection(path) == 'script'

    def test_extension_fallback_py_file(self):
        """Test .py file without matching patterns → module"""
        path = REPO_ROOT / 'utils' / 'helper.py'
        assert smart_category_detection(path) == 'module'

    def test_extension_fallback_md_file(self):
        """Test .md file without matching patterns → guide"""
        path = REPO_ROOT / 'random' / 'notes.md'
        assert smart_category_detection(path) == 'guide'

    def test_extension_fallback_yaml_file(self):
        """Test .yaml file without matching patterns → config"""
        path = REPO_ROOT / 'settings' / 'app.yaml'
        assert smart_category_detection(path) == 'config'

    def test_general_fallback(self):
        """Test unknown file type → general"""
        path = REPO_ROOT / 'unknown' / 'file.xyz'
        assert smart_category_detection(path) == 'general'

    # NEGATIVE TESTS: Avoid false positives

    def test_no_false_positive_contest_not_test(self):
        """'contest' should NOT match 'test' category"""
        path = REPO_ROOT / 'contest' / 'example.py'
        # Should be 'module' (fallback for .py), not 'test'
        assert smart_category_detection(path) != 'test'
        assert smart_category_detection(path) == 'module'

    def test_no_false_positive_latest_not_test(self):
        """'latest' should NOT match 'test' category"""
        path = REPO_ROOT / 'latest' / 'version.py'
        assert smart_category_detection(path) != 'test'
        assert smart_category_detection(path) == 'module'

    def test_no_false_positive_attest_not_test(self):
        """'attest' should NOT match 'test' category"""
        path = REPO_ROOT / 'attest' / 'verifier.py'
        assert smart_category_detection(path) != 'test'
        assert smart_category_detection(path) == 'module'

    def test_precedence_segment_over_extension(self):
        """Segment matching should win over extension fallback"""
        # File in /docs/ should be 'guide', not fallback to 'module' for .py
        path = REPO_ROOT / 'docs' / 'generator.py'
        assert smart_category_detection(path) == 'guide'

    def test_precedence_filename_over_segment(self):
        """Filename pattern should win over segment"""
        # test_*.py in /automation/ should be 'test', not 'script'
        path = REPO_ROOT / 'automation' / 'test_deploy.py'
        assert smart_category_detection(path) == 'test'

    def test_prompts_directory_smart_detection(self):
        """Test /prompts/ directory (not in MONITORED_FOLDERS)"""
        path = REPO_ROOT / 'prompts' / 'example.md'
        assert smart_category_detection(path) == 'prompt'

    def test_templates_directory_smart_detection(self):
        """Test /templates/ directory"""
        path = REPO_ROOT / 'templates' / 'boilerplate.py'
        assert smart_category_detection(path) == 'template'

    def test_workflow_directory(self):
        """Test /workflows/ directory"""
        path = REPO_ROOT / 'workflows' / 'ci.yaml'
        assert smart_category_detection(path) == 'workflow'

    def test_nested_path_segment_matching(self):
        """Test deeply nested paths still match segments"""
        path = REPO_ROOT / 'a' / 'b' / 'tests' / 'c' / 'd' / 'file.py'
        assert smart_category_detection(path) == 'test'


class TestFileStabilityCheck:
    """Test check_file_stable() function"""

    def test_nonexistent_file_not_stable(self):
        """Non-existent file should not be stable"""
        path = REPO_ROOT / 'nonexistent_file_12345.txt'
        assert not check_file_stable(path)

    def test_stable_file_is_stable(self):
        """Existing old file should be stable"""
        # Use a known existing file from the repo
        path = REPO_ROOT / 'RUNTIME' / 'doc_id' / 'SUB_DOC_ID' / 'common.py'
        if path.exists():
            # File must exist and be old enough
            import time
            stat = path.stat()
            age = time.time() - stat.st_mtime
            if age >= 2:  # FILE_MIN_AGE_SECONDS
                assert check_file_stable(path)
            else:
                # If file is too new, skip this test
                pytest.skip("Test file too new (< 2 seconds old)")
        else:
            pytest.skip("Test file not found")


class TestCategoryDistribution:
    """Test category distribution makes sense"""

    def test_most_common_categories_covered(self):
        """Verify common categories are detected"""
        test_paths = [
            (REPO_ROOT / 'tests' / 'test.py', 'test'),
            (REPO_ROOT / 'scripts' / 'deploy.py', 'script'),
            (REPO_ROOT / 'docs' / 'README.md', 'guide'),
            (REPO_ROOT / 'config' / 'app.yaml', 'config'),
            (REPO_ROOT / 'modules' / 'parser.py', 'module'),
        ]

        for path, expected_category in test_paths:
            actual = smart_category_detection(path)
            assert actual == expected_category, \
                f"Expected {path} → {expected_category}, got {actual}"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_path_outside_repo_root(self):
        """Path outside REPO_ROOT should return 'general'"""
        path = Path("C:/Windows/System32/test.py")
        assert smart_category_detection(path) == 'general'

    def test_empty_filename(self):
        """File with empty name should not crash"""
        path = REPO_ROOT / 'tests' / ''
        # Should handle gracefully
        result = smart_category_detection(path)
        assert isinstance(result, str)

    def test_very_long_path(self):
        """Very long path should not crash"""
        long_path = REPO_ROOT / ('a' * 100) / ('b' * 100) / 'test.py'
        result = smart_category_detection(long_path)
        assert isinstance(result, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
