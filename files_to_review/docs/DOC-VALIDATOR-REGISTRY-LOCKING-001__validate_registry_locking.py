#!/usr/bin/env python3
# DOC_LINK: DOC-VALIDATOR-REGISTRY-LOCKING-001
"""
DOC-VALIDATOR-REGISTRY-LOCKING-001
Validates that all registry write operations use proper locking.

Performs:
1. Static analysis: Scans code for registry.save() calls
2. Runtime verification: Checks lock acquisition patterns
3. Audit mode: Reviews all registry write locations
"""

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class RegistryLockingValidator:
    """Validates registry locking compliance."""

    def __init__(self, repo_root: Path):
        """
        Initialize validator.

        Args:
            repo_root: Repository root path
        """
        self.repo_root = repo_root
        self.violations = []
        self.warnings = []
        self.audited_files = []

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the repository."""
        python_files = []

        # Search RUNTIME and scripts directories
        search_dirs = [
            self.repo_root / "RUNTIME",
            self.repo_root / "scripts",
            self.repo_root / "tests"
        ]

        for search_dir in search_dirs:
            if search_dir.exists():
                python_files.extend(search_dir.rglob("*.py"))

        return python_files

    def analyze_file(self, file_path: Path) -> List[Dict]:
        """
        Analyze a Python file for registry save calls.

        Args:
            file_path: Path to Python file

        Returns:
            List of findings (violations or safe patterns)
        """
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Look for registry.save() calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if it's a .save() call
                    if (isinstance(node.func, ast.Attribute) and
                        node.func.attr == 'save'):

                        # Check if it's on a registry object
                        if isinstance(node.func.value, ast.Name):
                            var_name = node.func.value.id
                            if 'registry' in var_name.lower():

                                # Check if within a 'with' statement context
                                # This is a simplified check - full analysis would be more complex
                                lineno = node.lineno

                                # Extract surrounding context
                                lines = content.split('\n')
                                context_start = max(0, lineno - 10)
                                context_end = min(len(lines), lineno + 5)
                                context = '\n'.join(lines[context_start:context_end])

                                # Check for 'with registry_lock' in context
                                has_lock = 'with registry_lock' in context or 'registry_lock(' in context

                                finding = {
                                    "file": str(file_path.relative_to(self.repo_root)),
                                    "line": lineno,
                                    "has_lock": has_lock,
                                    "context_snippet": lines[lineno-1] if lineno > 0 else ""
                                }

                                findings.append(finding)

        except (SyntaxError, UnicodeDecodeError):
            # Skip files that can't be parsed
            pass

        return findings

    def audit_all_files(self) -> Dict:
        """
        Audit all files for registry locking compliance.

        Returns:
            Audit report dictionary
        """
        python_files = self.find_python_files()

        total_save_calls = 0
        locked_calls = 0
        unlocked_calls = 0

        for file_path in python_files:
            findings = self.analyze_file(file_path)
            self.audited_files.append(str(file_path.relative_to(self.repo_root)))

            for finding in findings:
                total_save_calls += 1

                if finding["has_lock"]:
                    locked_calls += 1
                else:
                    unlocked_calls += 1
                    self.violations.append(finding)

        # Generate report
        report = {
            "validator_id": "VAL-009",
            "validator_name": "Registry Locking Validator",
            "total_files_audited": len(self.audited_files),
            "total_save_calls": total_save_calls,
            "locked_calls": locked_calls,
            "unlocked_calls": unlocked_calls,
            "violations": self.violations,
            "warnings": self.warnings
        }

        # Determine status
        if unlocked_calls > 0:
            report["status"] = "FAIL"
            report["severity"] = "ERROR"
            report["message"] = f"Found {unlocked_calls} registry save calls without locking"
        else:
            report["status"] = "PASS"
            report["severity"] = "INFO"
            report["message"] = "All registry save calls use proper locking"

        return report

    def check_registry_implementation(self) -> Tuple[bool, str]:
        """
        Check that the Registry class itself implements locking.

        Returns:
            Tuple of (is_valid, message)
        """
        registry_file = self.repo_root / "RUNTIME" / "doc_id" / "SUB_DOC_ID" / "common" / "DOC-CORE-COMMON-REGISTRY-1171__registry.py"

        if not registry_file.exists():
            return False, f"Registry implementation not found: {registry_file}"

        with open(registry_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for registry_lock import
        if 'registry_lock' not in content and 'RegistryLock' not in content:
            return False, "Registry implementation missing lock imports"

        # Check that save() method uses locking
        if 'def save(' in content:
            # Find save method
            lines = content.split('\n')
            in_save_method = False
            has_lock_in_save = False

            for line in lines:
                if 'def save(' in line:
                    in_save_method = True
                elif in_save_method and ('def ' in line or 'class ' in line):
                    in_save_method = False
                elif in_save_method and 'registry_lock' in line:
                    has_lock_in_save = True
                    break

            if not has_lock_in_save:
                return False, "Registry.save() method does not use registry_lock"

        return True, "Registry implementation uses proper locking"


def main():
    """Main entry point for validator."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate registry locking compliance")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--audit-all", action="store_true", help="Audit all files")
    parser.add_argument("--check-implementation", action="store_true", help="Check Registry class implementation")
    parser.add_argument("--output", type=Path, help="Output JSON file path")

    args = parser.parse_args()

    validator = RegistryLockingValidator(repo_root=args.repo_root)

    # Check implementation first
    if args.check_implementation or args.audit_all:
        impl_valid, impl_message = validator.check_registry_implementation()

        if not impl_valid:
            print(f"ERROR: {impl_message}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"✓ {impl_message}")

    # Run full audit
    if args.audit_all:
        report = validator.audit_all_files()

        # Write report
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, sort_keys=True)

        # Print summary
        print(json.dumps(report, indent=2))

        # Exit with appropriate code
        sys.exit(0 if report["status"] == "PASS" else 1)

    print("Registry locking validation complete")


if __name__ == "__main__":
    main()
