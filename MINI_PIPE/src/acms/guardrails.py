"""
Guardrails Enforcement Module

Enforces pattern guardrails, invariants, and anti-pattern detection
for ACMS/MINI_PIPE execution system.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import yaml

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation"""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    rule_id: str
    message: str
    context: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class PatternGuardrails:
    """Manages and enforces pattern guardrails"""

    def __init__(self, pattern_index_path: Path):
        self.pattern_index_path = pattern_index_path
        self.pattern_index = self._load_pattern_index()
        self.protected_paths = self.pattern_index.get("global_guardrails", {}).get(
            "protected_paths", []
        )
        self.violations: List[GuardrailViolation] = []

    def _load_pattern_index(self) -> Dict:
        """Load PATTERN_INDEX.yaml"""
        if not self.pattern_index_path.exists():
            raise FileNotFoundError(
                f"PATTERN_INDEX.yaml not found: {self.pattern_index_path}"
            )

        with open(self.pattern_index_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_pattern(self, pattern_id: str) -> Optional[Dict]:
        """Get pattern definition by ID"""
        return self.pattern_index.get("patterns", {}).get(pattern_id)

    def validate_pattern_exists(self, pattern_id: str) -> Tuple[bool, Optional[str]]:
        """Validate that pattern exists and is enabled"""
        pattern = self.get_pattern(pattern_id)

        if not pattern:
            return False, f"Pattern '{pattern_id}' not found in PATTERN_INDEX.yaml"

        if not pattern.get("enabled", False):
            return False, f"Pattern '{pattern_id}' is disabled"

        return True, None

    def validate_path_scope(
        self, pattern_id: str, file_paths: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that file paths are within pattern's allowed scope

        Returns:
            (is_valid, violations)
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False, [f"Pattern '{pattern_id}' not found"]

        guardrails = pattern.get("guardrails", {})
        path_scope = guardrails.get("path_scope", {})
        include_patterns = path_scope.get("include", [])
        exclude_patterns = path_scope.get("exclude", [])

        violations = []

        for file_path in file_paths:
            # Check against protected paths first (global)
            for protected in self.protected_paths:
                if self._matches_glob(file_path, protected):
                    violations.append(
                        f"Path '{file_path}' matches protected path '{protected}'"
                    )
                    continue

            # Check include patterns
            included = any(
                self._matches_glob(file_path, pattern) for pattern in include_patterns
            )

            if not included:
                violations.append(f"Path '{file_path}' not in pattern's include scope")
                continue

            # Check exclude patterns
            excluded = any(
                self._matches_glob(file_path, pattern) for pattern in exclude_patterns
            )

            if excluded:
                violations.append(f"Path '{file_path}' matches exclude pattern")

        return len(violations) == 0, violations

    def validate_tool_usage(
        self, pattern_id: str, tool_ids: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate that tools are allowed for this pattern"""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False, [f"Pattern '{pattern_id}' not found"]

        allowed_tools = pattern.get("guardrails", {}).get("allowed_tools", [])
        violations = []

        for tool_id in tool_ids:
            if tool_id not in allowed_tools:
                violations.append(
                    f"Tool '{tool_id}' not in pattern's allowed_tools list"
                )

        return len(violations) == 0, violations

    def validate_change_limits(
        self, pattern_id: str, changes: Dict[str, int]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that changes are within pattern's max_changes limits

        Args:
            changes: Dict with keys like 'files', 'lines', 'hunks', etc.
        """
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False, [f"Pattern '{pattern_id}' not found"]

        max_changes = pattern.get("guardrails", {}).get("max_changes", {})
        violations = []

        for metric, actual_value in changes.items():
            max_value = max_changes.get(metric)
            if max_value is not None and actual_value > max_value:
                violations.append(
                    f"Change metric '{metric}' ({actual_value}) exceeds limit ({max_value})"
                )

        return len(violations) == 0, violations

    def check_forbidden_operations(
        self, pattern_id: str, operations: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check if any operations are forbidden for this pattern"""
        pattern = self.get_pattern(pattern_id)
        if not pattern:
            return False, [f"Pattern '{pattern_id}' not found"]

        forbidden = pattern.get("guardrails", {}).get("forbidden_operations", [])
        violations = []

        for operation in operations:
            if operation in forbidden:
                violations.append(
                    f"Operation '{operation}' is forbidden for this pattern"
                )

        return len(violations) == 0, violations

    def _matches_glob(self, path: str, glob_pattern: str) -> bool:
        """Simple glob matching (supports *, **, ?)"""
        # Convert glob to regex
        regex_pattern = glob_pattern.replace(".", r"\.")
        regex_pattern = regex_pattern.replace("*", ".*")
        regex_pattern = regex_pattern.replace("?", ".")
        regex_pattern = f"^{regex_pattern}$"

        return re.match(regex_pattern, path) is not None

    def pre_execution_checks(
        self, pattern_id: str, task_data: Dict[str, Any]
    ) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Run all pre-execution guardrail checks

        Returns:
            (passed, violations)
        """
        violations = []

        # 1. Pattern exists and enabled
        is_valid, error = self.validate_pattern_exists(pattern_id)
        if not is_valid:
            violations.append(
                GuardrailViolation(
                    severity="CRITICAL",
                    rule_id="PG-1",
                    message=error,
                    context={"pattern_id": pattern_id},
                )
            )
            # Can't continue if pattern doesn't exist
            return False, violations

        pattern = self.get_pattern(pattern_id)

        # 2. Path scope validation
        file_paths = task_data.get("file_paths", [])
        if file_paths:
            is_valid, path_violations = self.validate_path_scope(pattern_id, file_paths)
            if not is_valid:
                for violation_msg in path_violations:
                    violations.append(
                        GuardrailViolation(
                            severity="CRITICAL",
                            rule_id="RL-2",
                            message=violation_msg,
                            context={
                                "pattern_id": pattern_id,
                                "file_paths": file_paths,
                            },
                        )
                    )

        # 3. Tool usage validation
        tool_ids = task_data.get("tools_used", [])
        if tool_ids:
            is_valid, tool_violations = self.validate_tool_usage(pattern_id, tool_ids)
            if not is_valid:
                for violation_msg in tool_violations:
                    violations.append(
                        GuardrailViolation(
                            severity="HIGH",
                            rule_id="PG-3",
                            message=violation_msg,
                            context={"pattern_id": pattern_id, "tools": tool_ids},
                        )
                    )

        # 4. Forbidden operations check
        operations = task_data.get("operations", [])
        if operations:
            is_valid, op_violations = self.check_forbidden_operations(
                pattern_id, operations
            )
            if not is_valid:
                for violation_msg in op_violations:
                    violations.append(
                        GuardrailViolation(
                            severity="CRITICAL",
                            rule_id="PG-3",
                            message=violation_msg,
                            context={
                                "pattern_id": pattern_id,
                                "operations": operations,
                            },
                        )
                    )

        # Store violations
        self.violations.extend(violations)

        # Return overall result
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        return len(critical_violations) == 0, violations

    def post_execution_checks(
        self, pattern_id: str, task_result: Dict[str, Any]
    ) -> Tuple[bool, List[GuardrailViolation]]:
        """
        Run all post-execution guardrail checks

        Returns:
            (passed, violations)
        """
        violations = []

        pattern = self.get_pattern(pattern_id)
        if not pattern:
            violations.append(
                GuardrailViolation(
                    severity="CRITICAL",
                    rule_id="PG-1",
                    message=f"Pattern '{pattern_id}' not found",
                    context={"pattern_id": pattern_id},
                )
            )
            return False, violations

        # 1. Validate change limits
        changes = task_result.get("changes", {})
        if changes:
            is_valid, change_violations = self.validate_change_limits(
                pattern_id, changes
            )
            if not is_valid:
                for violation_msg in change_violations:
                    violations.append(
                        GuardrailViolation(
                            severity="HIGH",
                            rule_id="RL-1",
                            message=violation_msg,
                            context={"pattern_id": pattern_id, "changes": changes},
                        )
                    )

        # 2. Check for hallucinated success (GT-3)
        if task_result.get("status") == "success":
            verification = task_result.get("verification", {})

            # Check exit code
            exit_code = verification.get("exit_code")
            if exit_code is not None and exit_code != 0:
                violations.append(
                    GuardrailViolation(
                        severity="CRITICAL",
                        rule_id="AP_HALLUCINATED_SUCCESS",
                        message=f"Task claims success but exit_code={exit_code}",
                        context={"task_result": task_result},
                    )
                )

            # Check expected outputs exist
            expected_outputs = task_result.get("expected_outputs", [])
            for output_file in expected_outputs:
                if not Path(output_file).exists():
                    violations.append(
                        GuardrailViolation(
                            severity="CRITICAL",
                            rule_id="AP_HALLUCINATED_SUCCESS",
                            message=f"Task claims success but expected file missing: {output_file}",
                            context={
                                "task_result": task_result,
                                "missing_file": output_file,
                            },
                        )
                    )

        # Store violations
        self.violations.extend(violations)

        # Return overall result
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        return len(critical_violations) == 0, violations


class AntiPatternDetector:
    """Detects anti-patterns during execution"""

    def __init__(self, runbook_dir: Path):
        self.runbook_dir = runbook_dir
        self.runbooks = self._load_runbooks()
        self.detections: List[Dict[str, Any]] = []

    def _load_runbooks(self) -> Dict[str, Dict]:
        """Load all anti-pattern runbooks"""
        runbooks = {}

        if not self.runbook_dir.exists():
            return runbooks

        for runbook_file in self.runbook_dir.glob("AP_*.yaml"):
            try:
                with open(runbook_file, "r", encoding="utf-8") as f:
                    runbook = yaml.safe_load(f)
                    ap_id = runbook.get("meta", {}).get("id")
                    if ap_id:
                        runbooks[ap_id] = runbook
            except Exception as e:
                print(f"⚠️  Failed to load runbook {runbook_file.name}: {e}")

        return runbooks

    def detect_hallucinated_success(
        self, task_status: str, verification: Dict[str, Any]
    ) -> Optional[Dict]:
        """Detect AP_HALLUCINATED_SUCCESS"""
        if task_status != "success":
            return None

        # Check exit code
        if verification.get("exit_code") != 0:
            return {
                "anti_pattern_id": "AP_HALLUCINATED_SUCCESS",
                "rule": "rule_1",
                "evidence": f"Task claims success but exit_code={verification.get('exit_code')}",
            }

        # Check test results
        tests_run = verification.get("tests_run", 0)
        tests_passed = verification.get("tests_passed", 0)
        if tests_run > 0 and tests_passed < tests_run:
            return {
                "anti_pattern_id": "AP_HALLUCINATED_SUCCESS",
                "rule": "rule_2",
                "evidence": f"Task claims success but {tests_passed}/{tests_run} tests passed",
            }

        return None

    def detect_planning_loop(self, run_stats: Dict[str, Any]) -> Optional[Dict]:
        """Detect AP_PLANNING_LOOP"""
        planning_attempts = run_stats.get("planning_attempts", 0)
        patches_applied = run_stats.get("patches_applied", 0)

        # Rule 1: Excessive planning attempts
        if planning_attempts > 3 and patches_applied == 0:
            return {
                "anti_pattern_id": "AP_PLANNING_LOOP",
                "rule": "rule_1",
                "evidence": f"{planning_attempts} planning attempts but 0 patches applied",
            }

        return None

    def detect_all(self, run_context: Dict[str, Any]) -> List[Dict]:
        """Run all anti-pattern detectors"""
        detections = []

        # Check for hallucinated success
        task_status = run_context.get("task_status")
        verification = run_context.get("verification", {})
        if task_status:
            detection = self.detect_hallucinated_success(task_status, verification)
            if detection:
                detections.append(detection)
                self.detections.append(detection)

        # Check for planning loop
        run_stats = run_context.get("run_stats", {})
        if run_stats:
            detection = self.detect_planning_loop(run_stats)
            if detection:
                detections.append(detection)
                self.detections.append(detection)

        return detections


def validate_pattern_spec(spec_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate a pattern spec file against schema"""
    if not JSONSCHEMA_AVAILABLE:
        return True, "jsonschema not available - skipping validation"

    schema_path = (
        Path(__file__).parent.parent.parent
        / "patterns"
        / "schemas"
        / "pattern_spec.schema.json"
    )

    if not schema_path.exists():
        return False, f"Pattern spec schema not found: {schema_path}"

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        with open(spec_path, "r", encoding="utf-8") as f:
            if spec_path.suffix in [".yaml", ".yml"]:
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)

        jsonschema.validate(instance=spec, schema=schema)
        return True, None

    except jsonschema.ValidationError as e:
        return False, f"Validation error: {e.message}"
    except Exception as e:
        return False, f"Error: {str(e)}"


if __name__ == "__main__":
    # Quick test
    from pathlib import Path

    pattern_index = (
        Path(__file__).parent.parent.parent / "patterns" / "PATTERN_INDEX.yaml"
    )

    if pattern_index.exists():
        print("Testing Guardrails Enforcement...")

        guardrails = PatternGuardrails(pattern_index)

        # Test pattern validation
        is_valid, error = guardrails.validate_pattern_exists("atomic_create")
        print(f"\n✓ Pattern 'atomic_create' exists: {is_valid}")

        is_valid, error = guardrails.validate_pattern_exists("nonexistent")
        print(f"✗ Pattern 'nonexistent' exists: {is_valid} ({error})")

        # Test path scope
        is_valid, violations = guardrails.validate_path_scope(
            "atomic_create", ["test.py", "PATTERN_INDEX.yaml"]
        )
        print(f"\n✓ Path scope test: {is_valid}")
        if violations:
            for v in violations:
                print(f"  - {v}")

        # Test anti-pattern detection
        print("\n\nTesting Anti-Pattern Detection...")

        detector = AntiPatternDetector(
            Path(__file__).parent.parent.parent / "anti_patterns"
        )
        print(f"Loaded {len(detector.runbooks)} runbooks")

        # Simulate hallucinated success
        detection = detector.detect_hallucinated_success("success", {"exit_code": 1})
        if detection:
            print(f"✓ Detected: {detection['anti_pattern_id']}")
    else:
        print(f"⚠️  PATTERN_INDEX.yaml not found at {pattern_index}")
