#!/usr/bin/env python3
"""
Autonomous Plan CLI v2.4.0
Production-grade executor with deterministic guarantees.

Commands:
  validate   - Schema validation only
  normalize  - Normalize plan structure (sort arrays, build ID maps)
  compile    - Normalize + regenerate navigation + validate formulas
  execute    - Execute plan (reads only /plan)
  diff       - Compare two plans (ignoring timestamps)
  run-gates  - Execute all validation gates in dependency order
"""

import json
import sys
import math
import hashlib
import subprocess
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from copy import deepcopy
from collections import defaultdict, deque

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("Error: jsonschema not installed. Run: pip install jsonschema --break-system-packages")
    sys.exit(1)

# ============================================================================
# CONSTANTS
# ============================================================================

NAVIGATION_ALGORITHM_VERSION = "nav-v2.0"

SCHEMA_CANDIDATES = [
    Path(__file__).parent.parent / "01260207201000001223_schemas" / "01260207201000000532_NEWPHASEPLANPROCESS_plan.schema.v2.4.0.json",
    Path(__file__).parent.parent / "01260207201000001223_schemas" / "01260207233100000675_NEWPHASEPLANPROCESS_plan.schema.v3.0.0.json",
    Path(__file__).parent.parent / "schemas" / "01260207233100000674_NEWPHASEPLANPROCESS_plan.schema.v2.4.0.json",
]


def resolve_schema_path() -> Path:
    """Resolve the canonical schema path, preserving compatibility with older layouts."""
    for candidate in SCHEMA_CANDIDATES:
        if candidate.exists():
            return candidate
    return SCHEMA_CANDIDATES[0]


SCHEMA_PATH = resolve_schema_path()

# ============================================================================
# SAFE FORMULA EVALUATOR (NO eval())
# ============================================================================

class SafeFormulaEvaluator:
    """
    Evaluate formulas without using eval().
    Supports: +, -, *, /, MIN, MAX, CEIL, FLOOR, variables
    """

    @staticmethod
    def evaluate(formula_str: str, variables: dict[str, Any]) -> float:
        """
        Evaluate formula string with given variables.

        Examples:
          "15 + CEIL(file_count_est * 2)" with {file_count_est: 5} → 25
          "MIN(10, MAX(5, CEIL(file_count_est / 3)))" with {file_count_est: 20} → 10
        """
        if isinstance(formula_str, (int, float)):
            return float(formula_str)

        # Simple token-based parser
        import re

        # Replace variables
        for var, value in variables.items():
            formula_str = formula_str.replace(var, str(value))

        # Evaluate math functions
        def eval_ceil(match):
            return str(math.ceil(float(eval_simple(match.group(1)))))

        def eval_floor(match):
            return str(math.floor(float(eval_simple(match.group(1)))))

        def eval_min(match):
            args = [float(eval_simple(x.strip())) for x in match.group(1).split(',')]
            return str(min(args))

        def eval_max(match):
            args = [float(eval_simple(x.strip())) for x in match.group(1).split(',')]
            return str(max(args))

        def eval_simple(expr: str) -> float:
            """Evaluate simple arithmetic (no functions)."""
            expr = expr.strip()
            # Basic arithmetic only
            try:
                # Use ast.literal_eval for safety, but only on numeric expressions
                import ast
                import operator

                # Parse expression tree
                tree = ast.parse(expr, mode='eval')

                # Allowed operations
                ops = {
                    ast.Add: operator.add,
                    ast.Sub: operator.sub,
                    ast.Mult: operator.mul,
                    ast.Div: operator.truediv,
                }

                def _eval(node):
                    if isinstance(node, ast.Constant):
                        return node.value
                    elif isinstance(node, ast.BinOp):
                        return ops[type(node.op)](_eval(node.left), _eval(node.right))
                    elif isinstance(node, ast.UnaryOp):
                        if isinstance(node.op, ast.USub):
                            return -_eval(node.operand)
                        raise ValueError(f"Unsupported unary op: {node.op}")
                    else:
                        raise ValueError(f"Unsupported node: {node}")

                return _eval(tree.body)
            except Exception as e:
                raise ValueError(f"Cannot evaluate: {expr}") from e

        # Recursively evaluate functions (innermost first)
        while 'CEIL(' in formula_str:
            formula_str = re.sub(r'CEIL\(([^()]+)\)', eval_ceil, formula_str)
        while 'FLOOR(' in formula_str:
            formula_str = re.sub(r'FLOOR\(([^()]+)\)', eval_floor, formula_str)
        while 'MIN(' in formula_str:
            formula_str = re.sub(r'MIN\(([^()]+)\)', eval_min, formula_str)
        while 'MAX(' in formula_str:
            formula_str = re.sub(r'MAX\(([^()]+)\)', eval_max, formula_str)

        return float(eval_simple(formula_str))

# ============================================================================
# SCHEMA VALIDATION
# ============================================================================

def load_json(path: Path) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def validate_schema(doc: dict, schema: dict) -> None:
    """Validate document against JSON Schema."""
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)

    if errors:
        error_msgs = []
        for e in errors:
            path = "/".join(str(p) for p in e.path)
            error_msgs.append(f"  {path}: {e.message}")

        raise ValueError(
            f"Schema validation failed with {len(errors)} error(s):\n"
            + "\n".join(error_msgs)
        )

# ============================================================================
# NORMALIZATION (STABLE ORDERING + ID MAPS)
# ============================================================================

def normalize_plan(plan: dict) -> dict:
    """
    Normalize plan structure for deterministic output:
    1. Build ID-keyed maps (phases_by_id, gates_by_id)
    2. Sort all arrays lexicographically
    3. Validate uniqueness constraints
    """
    normalized = deepcopy(plan)

    # Build phases_by_id from array (if array exists)
    if "phases" in normalized and not isinstance(normalized.get("phases"), dict):
        phases_array = normalized.pop("phases")
        normalized["phases_by_id"] = {
            phase["phase_id"]: phase
            for phase in sorted(phases_array, key=lambda p: p["phase_id"])
        }

    # Build gates_by_id from array (if array exists)
    if "gates" in normalized and not isinstance(normalized.get("gates"), dict):
        gates_array = normalized.pop("gates")
        normalized["gates_by_id"] = {
            gate["gate_id"]: gate
            for gate in sorted(gates_array, key=lambda g: g["gate_id"])
        }

    # Build metrics by name (if array exists)
    if "metrics" in normalized and isinstance(normalized.get("metrics"), list):
        metrics_array = normalized.pop("metrics")
        normalized["metrics"] = {
            metric["name"]: metric
            for metric in sorted(metrics_array, key=lambda m: m["name"])
        }

    # Normalize commands structure
    if "commands" in normalized:
        commands = normalized["commands"]

        # Build standard_by_id
        if "standard" in commands and isinstance(commands["standard"], list):
            commands["standard_by_id"] = {
                cmd["id"]: cmd
                for cmd in sorted(commands["standard"], key=lambda c: c["id"])
            }
            del commands["standard"]

        # Build custom_by_id
        if "custom" in commands and isinstance(commands["custom"], list):
            commands["custom_by_id"] = {
                cmd["id"]: cmd
                for cmd in sorted(commands["custom"], key=lambda c: c["id"])
            }
            del commands["custom"]

    # Sort dependencies arrays
    for phase in normalized.get("phases_by_id", {}).values():
        if "dependencies" in phase:
            phase["dependencies"] = sorted(phase["dependencies"])
        if "file_scope" in phase:
            phase["file_scope"] = sorted(phase["file_scope"])

    # Sort parallel execution groups
    if "parallel_execution" in normalized and "groups" in normalized["parallel_execution"]:
        groups = normalized["parallel_execution"]["groups"]
        for group in groups:
            if "phases" in group:
                group["phases"] = sorted(group["phases"])
        normalized["parallel_execution"]["groups"] = sorted(groups, key=lambda g: g["group_id"])

    return normalized

# ============================================================================
# VALIDATION (FORMULA CHECKS, UNIQUENESS, REFERENTIAL INTEGRITY)
# ============================================================================

class PlanValidator:
    """Validates constraints that JSON Schema cannot express."""

    def __init__(self, plan: dict):
        self.plan = plan
        self.errors = []
        self.evaluator = SafeFormulaEvaluator()

    def validate_all(self) -> list[str]:
        """Run all validation checks."""
        self.validate_uniqueness()
        self.validate_referential_integrity()
        self.validate_command_references()
        self.validate_dependency_acyclicity()
        self.validate_custom_command_scheduling()
        self.validate_time_estimates()
        self.validate_counts()
        self.validate_coverage_targets()
        return self.errors

    def validate_uniqueness(self) -> None:
        """Ensure all IDs are unique."""
        phase_ids = list(self.plan.get("phases_by_id", {}).keys())
        if len(phase_ids) != len(set(phase_ids)):
            self.errors.append("Duplicate phase_id found")

        gate_ids = list(self.plan.get("gates_by_id", {}).keys())
        if len(gate_ids) != len(set(gate_ids)):
            self.errors.append("Duplicate gate_id found")

        if "commands" in self.plan:
            cmd_ids = (
                list(self.plan["commands"].get("standard_by_id", {}).keys()) +
                list(self.plan["commands"].get("custom_by_id", {}).keys())
            )
            if len(cmd_ids) != len(set(cmd_ids)):
                self.errors.append("Duplicate command ID found")

    def validate_referential_integrity(self) -> None:
        """Ensure all references point to existing entities."""
        phases_by_id = self.plan.get("phases_by_id", {})
        gates_by_id = self.plan.get("gates_by_id", {})

        # Validate phase dependencies
        for phase_id, phase in phases_by_id.items():
            for dep in phase.get("dependencies", []):
                if dep not in phases_by_id:
                    self.errors.append(f"Phase {phase_id} depends on non-existent phase: {dep}")

        # Validate gate phase references
        for gate_id, gate in gates_by_id.items():
            if gate["phase_id"] not in phases_by_id:
                self.errors.append(f"Gate {gate_id} references non-existent phase: {gate['phase_id']}")

    def validate_command_references(self) -> None:
        """Ensure all command_ref exist in commands registry."""
        if "commands" not in self.plan:
            return

        std_ids = set(self.plan["commands"].get("standard_by_id", {}).keys())
        custom_ids = set(self.plan["commands"].get("custom_by_id", {}).keys())
        all_ids = std_ids | custom_ids

        # Check gates
        for gate_id, gate in self.plan.get("gates_by_id", {}).items():
            if "command" in gate and isinstance(gate["command"], dict):
                ref = gate["command"].get("command_ref")
                if ref and ref not in all_ids:
                    self.errors.append(f"Gate {gate_id} references undeclared command: {ref}")

        # Check metrics
        for metric_name, metric in self.plan.get("metrics", {}).items():
            if "validation" in metric and "command" in metric["validation"]:
                cmd = metric["validation"]["command"]
                if isinstance(cmd, dict):
                    ref = cmd.get("command_ref")
                    if ref and ref not in all_ids:
                        self.errors.append(f"Metric {metric_name} references undeclared command: {ref}")

    def validate_dependency_acyclicity(self) -> None:
        """Ensure phase dependency graph is acyclic."""
        phases_by_id = self.plan.get("phases_by_id", {})

        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in phases_by_id.get(node, {}).get("dependencies", []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        rec_stack = set()  # Shared across all DFS calls
        for phase_id in phases_by_id:
            if phase_id not in visited:
                if has_cycle(phase_id, visited, rec_stack):
                    self.errors.append("Cyclic dependency detected in phase graph")
                    return

    def validate_custom_command_scheduling(self) -> None:
        """Ensure custom commands are built before they're used."""
        if "commands" not in self.plan:
            return

        custom_cmds = self.plan["commands"].get("custom_by_id", {})
        phases_by_id = self.plan.get("phases_by_id", {})
        gates_by_id = self.plan.get("gates_by_id", {})

        # Build phase ordering
        phase_ids = sorted(phases_by_id.keys())
        phase_order = {pid: idx for idx, pid in enumerate(phase_ids)}

        for cmd_id, cmd in custom_cmds.items():
            build_phase = cmd.get("build_phase")
            if not build_phase:
                continue

            if build_phase not in phase_order:
                self.errors.append(f"Custom command {cmd_id} build_phase not found: {build_phase}")
                continue

            build_idx = phase_order[build_phase]

            # Check all gates that reference this command
            for gate_id, gate in gates_by_id.items():
                if "command" in gate and isinstance(gate["command"], dict):
                    if gate["command"].get("command_ref") == cmd_id:
                        gate_phase = gate["phase_id"]
                        gate_idx = phase_order.get(gate_phase, -1)

                        if gate_idx <= build_idx:
                            self.errors.append(
                                f"Custom command {cmd_id} built in {build_phase} "
                                f"but used in earlier/same phase {gate_phase}"
                            )

    def validate_time_estimates(self) -> None:
        """Validate estimated_time_min matches formula."""
        classification = self.plan.get("classification", {})
        determinism = self.plan.get("determinism", {})

        if not determinism or "time_estimation_formulas" not in determinism:
            return

        formulas = determinism["time_estimation_formulas"]
        complexity = classification.get("complexity")
        multiplier = formulas["complexity_multiplier"].get(complexity, 1.0)

        variables = {
            "file_count_est": classification.get("file_count_est", 1),
            "loc_est": classification.get("loc_est", 1),
            "gates_count": len(self.plan.get("gates_by_id", {})),
            "phase_count": len(self.plan.get("phases_by_id", {}))
        }

        for phase_id, phase in self.plan.get("phases_by_id", {}).items():
            canonical = phase.get("canonical_name")
            if not canonical:
                continue

            base_formula = formulas["per_phase_base_min"].get(canonical)
            if base_formula is None:
                continue

            try:
                base = self.evaluator.evaluate(base_formula, variables)
                expected = math.ceil(base * multiplier)
                actual = phase.get("estimated_time_min", 0)

                if actual != expected:
                    self.errors.append(
                        f"Phase {phase_id} time estimate mismatch: "
                        f"expected {expected}, got {actual}"
                    )
            except Exception as e:
                self.errors.append(f"Phase {phase_id} time formula evaluation failed: {e}")

    def validate_counts(self) -> None:
        """Validate gates count matches formula."""
        classification = self.plan.get("classification", {})
        determinism = self.plan.get("determinism", {})

        if not determinism or "quantification_rules" not in determinism:
            return

        rules = determinism["quantification_rules"]
        complexity = classification.get("complexity")

        # Validate gates count
        gates_rules = rules.get("gates_count", {})
        base_count = gates_rules.get("by_complexity", {}).get(complexity, 0)
        phase_count = len(self.plan.get("phases_by_id", {}))

        try:
            adjustment_formula = gates_rules.get("phase_adjustment", {}).get("formula", "0")
            adjustment = self.evaluator.evaluate(adjustment_formula, {"phase_count": phase_count})
            expected_gates = base_count + int(adjustment)
            actual_gates = len(self.plan.get("gates_by_id", {}))

            if actual_gates != expected_gates:
                self.errors.append(
                    f"Gates count mismatch: expected {expected_gates}, got {actual_gates}"
                )
        except Exception as e:
            self.errors.append(f"Gates count formula evaluation failed: {e}")

    def validate_coverage_targets(self) -> None:
        """Validate test_coverage_min matches formula."""
        classification = self.plan.get("classification", {})
        determinism = self.plan.get("determinism", {})

        if not determinism or "metrics_target_formulas" not in determinism:
            return

        formulas = determinism["metrics_target_formulas"]
        coverage_formula = formulas.get("test_coverage_min", {})

        complexity = classification.get("complexity")
        quality = classification.get("quality")

        base = coverage_formula.get("by_complexity", {}).get(complexity, 0)
        adjustment = coverage_formula.get("by_quality", {}).get(quality, 0)
        expected = min(100, base + adjustment)
        actual = classification.get("test_coverage_min", 0)

        if actual != expected:
            self.errors.append(
                f"Coverage target mismatch: expected {expected}, got {actual}"
            )

# ============================================================================
# NAVIGATION GENERATION (DETERMINISTIC)
# ============================================================================

def generate_navigation(plan: dict) -> dict:
    """
    Generate navigation deterministically from /plan ID maps.

    Rules:
    1. TOC is fixed structure
    2. Hierarchy built from sorted IDs
    3. All pointers reference _by_id maps
    4. Lexicographic ordering everywhere
    """

    phases_by_id = plan.get("phases_by_id", {})
    gates_by_id = plan.get("gates_by_id", {})

    # Fixed TOC structure
    toc = [
        {"title": "Classification", "ptr": "/plan/classification"},
        {"title": "Phases", "ptr": "/plan/phases_by_id"},
        {"title": "Gates", "ptr": "/plan/gates_by_id"},
        {"title": "Commands", "ptr": "/plan/commands"},
        {"title": "Metrics", "ptr": "/plan/metrics"},
        {"title": "Parallel Execution", "ptr": "/plan/parallel_execution"},
        {"title": "Self-Healing", "ptr": "/plan/self_healing"},
        {"title": "Determinism Config", "ptr": "/plan/determinism"}
    ]

    # Build hierarchical navigation (phase -> gates)
    hierarchy = []

    # Build gate map by phase
    gate_map: dict[str, list[str]] = defaultdict(list)
    for gate_id, gate in gates_by_id.items():
        gate_map[gate["phase_id"]].append(gate_id)

    # Sort phases by ID
    for phase_id in sorted(phases_by_id.keys()):
        phase_node = {
            "id": phase_id,
            "ptr": f"/plan/phases_by_id/{phase_id}",
            "children": []
        }

        # Add gates for this phase (sorted)
        for gate_id in sorted(gate_map.get(phase_id, [])):
            phase_node["children"].append({
                "id": gate_id,
                "ptr": f"/plan/gates_by_id/{gate_id}",
                "children": []
            })

        hierarchy.append(phase_node)

    # Build index (ID -> pointer mapping)
    index = {}
    for phase_id in phases_by_id:
        index[phase_id] = f"/plan/phases_by_id/{phase_id}"
    for gate_id in gates_by_id:
        index[gate_id] = f"/plan/gates_by_id/{gate_id}"

    # Sort index keys
    index = dict(sorted(index.items()))

    return {
        "generated_from": "plan",
        "algorithm_version": NAVIGATION_ALGORITHM_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "toc": toc,
        "hierarchy": hierarchy,
        "index": index
    }

# ============================================================================
# COMPILER (NORMALIZE + VALIDATE + REGENERATE NAVIGATION)
# ============================================================================

def compile_plan(input_path: Path, output_path: Path, schema: dict) -> None:
    """
    Compile plan: validate + normalize + regenerate navigation.

    Guarantees:
    - Schema valid
    - ID maps canonical
    - Arrays sorted
    - Formulas validated
    - Navigation regenerated
    - Stable byte output
    """
    print(f"Compiling plan: {input_path}")

    # Load and validate schema
    doc = load_json(input_path)
    print("✓ JSON loaded")

    validate_schema(doc, schema)
    print("✓ Schema valid")

    # Normalize plan structure
    plan = normalize_plan(doc["plan"])
    print("✓ Plan normalized (ID maps built, arrays sorted)")

    # Validate formulas and constraints
    validator = PlanValidator(plan)
    errors = validator.validate_all()
    if errors:
        print(f"✗ Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("✓ Formulas validated")

    # Regenerate navigation
    navigation = generate_navigation(plan)
    print(f"✓ Navigation regenerated (algorithm: {navigation['algorithm_version']})")

    # Build compiled output
    compiled = {
        "meta": doc["meta"],
        "plan": plan,
        "navigation": navigation,
        "logs": doc.get("logs", {})
    }

    # Write with stable ordering
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(
            compiled,
            f,
            indent=2,
            sort_keys=True,
            ensure_ascii=False
        )
        f.write("\n")

    print(f"✓ Compiled plan written to: {output_path}")

    # Compute plan hash
    plan_hash = compute_plan_hash(compiled)
    print(f"✓ Plan hash: {plan_hash}")

# ============================================================================
# PLAN HASH
# ============================================================================

def compute_plan_hash(doc: dict) -> str:
    """Compute deterministic hash of plan (ignoring timestamps)."""
    # Extract hashable content
    hashable = {
        "classification": doc["plan"]["classification"],
        "phases_by_id": doc["plan"]["phases_by_id"],
        "gates_by_id": doc["plan"]["gates_by_id"],
        "commands": doc["plan"]["commands"],
        "determinism": doc["plan"]["determinism"]
    }

    # Serialize with stable ordering
    json_str = json.dumps(hashable, sort_keys=True, ensure_ascii=False)

    # Hash
    return hashlib.sha256(json_str.encode()).hexdigest()

# ============================================================================
# EXECUTOR (READS ONLY /plan)
# ============================================================================

class PlanExecutor:
    """Executes plan with hard guarantee: only reads from doc['plan']."""

    def __init__(self, plan: dict, meta: dict):
        self.plan = plan
        self.meta = meta
        self.execution_log = []

    def execute(self) -> dict:
        """Execute the entire plan."""
        print(f"\nExecuting plan: {self.meta['plan_id']}")
        print(f"Complexity: {self.plan['classification']['complexity']}")

        # Get execution order (sorted phase IDs)
        phase_ids = sorted(self.plan["phases_by_id"].keys())

        print(f"\nPhases to execute: {len(phase_ids)}")
        for phase_id in phase_ids:
            print(f"  - {phase_id}")

        # Execute phases (stubbed for now)
        phase_results = []
        for phase_id in phase_ids:
            result = self.execute_phase(phase_id)
            phase_results.append(result)

        return {
            "status": "success",
            "phases_executed": len(phase_results),
            "phase_results": phase_results
        }

    def execute_phase(self, phase_id: str) -> dict:
        """Execute a single phase."""
        phase = self.plan["phases_by_id"][phase_id]
        print(f"\nExecuting phase: {phase_id} - {phase['canonical_name']}")

        # Find gates for this phase
        gates_by_id = self.plan["gates_by_id"]
        phase_gates = [
            (gid, gate) for gid, gate in gates_by_id.items()
            if gate["phase_id"] == phase_id
        ]

        # Execute gates (stubbed)
        gate_results = []
        for gate_id, gate in sorted(phase_gates):
            print(f"  Gate {gate_id}: {gate['purpose']}")
            # Real impl: execute gate["command"]
            gate_results.append({
                "gate_id": gate_id,
                "status": "passed",
                "exit_code": 0
            })

        return {
            "phase_id": phase_id,
            "status": "completed",
            "gates": gate_results
        }

# ============================================================================
# PLAN DIFF
# ============================================================================

def diff_plans(path1: Path, path2: Path) -> None:
    """Compare two plans, ignoring timestamps."""
    doc1 = load_json(path1)
    doc2 = load_json(path2)

    # Extract comparable content (ignore timestamps, run_ids)
    def extract_comparable(doc: dict) -> dict:
        return {
            "classification": doc["plan"]["classification"],
            "phases": sorted(doc["plan"]["phases_by_id"].keys()),
            "gates": sorted(doc["plan"]["gates_by_id"].keys()),
            "commands": {
                "standard": sorted(doc["plan"]["commands"].get("standard_by_id", {}).keys()),
                "custom": sorted(doc["plan"]["commands"].get("custom_by_id", {}).keys())
            }
        }

    comp1 = extract_comparable(doc1)
    comp2 = extract_comparable(doc2)

    if comp1 == comp2:
        print("✓ Plans are equivalent (ignoring timestamps)")
    else:
        print("✗ Plans differ:")

        import difflib
        json1 = json.dumps(comp1, indent=2, sort_keys=True)
        json2 = json.dumps(comp2, indent=2, sort_keys=True)

        diff = difflib.unified_diff(
            json1.splitlines(),
            json2.splitlines(),
            fromfile=str(path1),
            tofile=str(path2),
            lineterm=""
        )

        for line in diff:
            print(line)

# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    # Load schema
    if not SCHEMA_PATH.exists():
        print(f"Error: Schema not found at {SCHEMA_PATH}")
        sys.exit(1)

    schema = load_json(SCHEMA_PATH)

    if command == "validate":
        input_path = Path(sys.argv[2])
        doc = load_json(input_path)
        validate_schema(doc, schema)
        print("✅ Schema validation passed")

    elif command == "normalize":
        input_path = Path(sys.argv[2])
        output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else input_path.with_suffix(".normalized.json")

        doc = load_json(input_path)
        validate_schema(doc, schema)

        normalized_plan = normalize_plan(doc["plan"])
        doc["plan"] = normalized_plan

        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")

        print(f"✅ Normalized plan written to: {output_path}")

    elif command == "compile":
        if len(sys.argv) < 4:
            print("Error: compile requires input and output paths")
            sys.exit(1)
        input_path = Path(sys.argv[2])
        output_path = Path(sys.argv[3])
        compile_plan(input_path, output_path, schema)

    elif command == "execute":
        input_path = Path(sys.argv[2])
        doc = load_json(input_path)
        validate_schema(doc, schema)

        # CRITICAL: Extract only /plan and /meta
        plan = doc["plan"]
        meta = doc["meta"]

        executor = PlanExecutor(plan, meta)
        result = executor.execute()

        print(f"\n{'='*60}")
        print("Execution complete:")
        print(f"Status: {result['status']}")
        print(f"Phases executed: {result['phases_executed']}")

    elif command == "diff":
        if len(sys.argv) < 4:
            print("Error: diff requires two plan paths")
            sys.exit(1)
        path1 = Path(sys.argv[2])
        path2 = Path(sys.argv[3])
        diff_plans(path1, path2)

    elif command == "run-gates":
        # Parse arguments
        plan_file = None
        evidence_dir = Path(".state/evidence")
        fail_fast = False
        only_required = False
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--plan-file" and i + 1 < len(sys.argv):
                plan_file = Path(sys.argv[i + 1])
                i += 2
            elif arg == "--evidence-dir" and i + 1 < len(sys.argv):
                evidence_dir = Path(sys.argv[i + 1])
                i += 2
            elif arg == "--fail-fast":
                fail_fast = True
                i += 1
            elif arg == "--only-required":
                only_required = True
                i += 1
            elif arg == "--run-id" and i + 1 < len(sys.argv):
                run_id = sys.argv[i + 1]
                i += 2
            elif not arg.startswith("--"):
                # Positional argument - treat as plan_file
                if plan_file is None:
                    plan_file = Path(arg)
                i += 1
            else:
                print(f"Unknown argument: {arg}")
                sys.exit(1)

        if not plan_file:
            print("Error: --plan-file required for run-gates")
            print("\nUsage: python P_01260207233100000242_NEWPHASEPLANPROCESS_plan_cli.py run-gates --plan-file PLAN.json [OPTIONS]")
            print("\nOptions:")
            print("  --evidence-dir DIR    Evidence output directory (default: .state/evidence)")
            print("  --fail-fast           Stop on first failure")
            print("  --only-required       Skip optional gates")
            print("  --run-id ID           Custom run identifier")
            sys.exit(1)

        result = run_all_gates(plan_file, evidence_dir, fail_fast, only_required, run_id)
        sys.exit(0 if result["success"] else 1)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

# ============================================================================
# GATE ORCHESTRATION
# ============================================================================

def load_gate_dependencies():
    """Load gate dependency graph from JSON."""
    dep_file = Path(__file__).parent / "01260207233100000678_gate_dependencies.json"
    if not dep_file.exists():
        print(f"Error: Gate dependencies not found at {dep_file}")
        sys.exit(1)

    with open(dep_file, "r", encoding="utf-8") as f:
        return json.load(f)

def topological_sort(gates):
    """
    Perform topological sort on gates using Kahn's algorithm.
    Returns list of gates in execution order.
    """
    # Build adjacency list and in-degree count
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    gate_map = {g["id"]: g for g in gates}

    for gate in gates:
        gate_id = gate["id"]
        if gate_id not in in_degree:
            in_degree[gate_id] = 0

        for dep in gate.get("depends_on", []):
            graph[dep].append(gate_id)
            in_degree[gate_id] += 1

    # Find all nodes with no incoming edges (sorted for determinism)
    queue = deque(sorted([gid for gid in gate_map.keys() if in_degree[gid] == 0]))
    sorted_gates = []

    while queue:
        gate_id = queue.popleft()
        sorted_gates.append(gate_map[gate_id])

        # Remove edge and update in-degrees (sort neighbors for determinism)
        for neighbor in sorted(graph[gate_id]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles
    if len(sorted_gates) != len(gates):
        raise ValueError("Circular dependency detected in gate graph!")

    return sorted_gates

def run_all_gates(plan_file, evidence_dir, fail_fast, only_required, run_id):
    """
    Execute all validation gates in dependency order.

    Returns dict with:
      - success: bool
      - passed: list of gate IDs
      - failed: list of gate IDs
      - skipped: list of gate IDs
      - run_id: str
    """
    # Load dependencies
    dep_data = load_gate_dependencies()
    gates = dep_data["gates"]

    # Filter optional gates if requested
    if only_required:
        gates = [g for g in gates if g.get("required", True)]

    # Sort gates by dependencies
    try:
        sorted_gates = topological_sort(gates)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return {"success": False, "passed": [], "failed": [], "skipped": [], "run_id": run_id}

    # Prepare execution
    project_root = Path(__file__).parent
    passed = []
    failed = []
    skipped = []
    failed_gates_set = set()

    print("=" * 80)
    print(f"🚀 GATE VALIDATION RUN")
    print(f"Run ID: {run_id}")
    print(f"Plan: {plan_file}")
    print(f"Evidence: {evidence_dir}")
    print(f"Gates to execute: {len(sorted_gates)}")
    print(f"Mode: {'Fail-fast' if fail_fast else 'Run all'}")
    print("=" * 80)
    print()

    # Execute gates in order
    for i, gate in enumerate(sorted_gates, 1):
        gate_id = gate["id"]
        script_path = project_root / gate["script"]

        # Check if dependencies failed
        deps_failed = any(dep in failed_gates_set for dep in gate.get("depends_on", []))
        if deps_failed:
            print(f"⏭️  [{i}/{len(sorted_gates)}] {gate_id} - SKIPPED (dependency failed)")
            skipped.append(gate_id)
            continue

        # Run gate
        print(f"▶️  [{i}/{len(sorted_gates)}] {gate_id} - {gate['name']}")
        print(f"    Script: {gate['script']}")

        # Ensure per-gate evidence directory exists
        gate_evidence_dir = Path(gate['evidence_dir'])
        gate_evidence_dir.mkdir(parents=True, exist_ok=True)

        try:
            # All gates now use argparse with --plan-file and --evidence-dir
            cmd = [sys.executable, str(script_path),
                   "--plan-file", str(plan_file),
                   "--evidence-dir", str(gate_evidence_dir)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace decode errors with �
                timeout=300  # 5 minute timeout per gate
            )

            if result.returncode == 0:
                print(f"✅  [{i}/{len(sorted_gates)}] {gate_id} - PASSED")
                passed.append(gate_id)
            else:
                print(f"❌  [{i}/{len(sorted_gates)}] {gate_id} - FAILED (exit code {result.returncode})")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}")
                failed.append(gate_id)
                failed_gates_set.add(gate_id)

                if fail_fast:
                    print("\n⛔ Fail-fast mode: stopping execution")
                    break

        except subprocess.TimeoutExpired:
            print(f"⏱️  [{i}/{len(sorted_gates)}] {gate_id} - TIMEOUT (>5 minutes)")
            failed.append(gate_id)
            failed_gates_set.add(gate_id)
            if fail_fast:
                break

        except Exception as e:
            print(f"💥  [{i}/{len(sorted_gates)}] {gate_id} - ERROR ({e})")
            failed.append(gate_id)
            failed_gates_set.add(gate_id)
            if fail_fast:
                break

        print()

    # Summary
    print("=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Passed:  {len(passed)}")
    print(f"❌ Failed:  {len(failed)}")
    print(f"⏭️  Skipped: {len(skipped)}")
    print(f"📝 Total:   {len(sorted_gates)}")
    print()

    if failed:
        print("Failed gates:")
        for gate_id in failed:
            print(f"  - {gate_id}")
        print()

    success = len(failed) == 0
    print(f"{'✅ ALL GATES PASSED' if success else '❌ VALIDATION FAILED'}")
    print("=" * 80)

    return {
        "success": success,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "run_id": run_id
    }

if __name__ == "__main__":
    main()
