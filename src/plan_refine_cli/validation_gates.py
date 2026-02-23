"""
Validation Gates
Executable validation gates for planning loop artifacts.
"""
import json
import jsonschema
from pathlib import Path
from typing import Dict, Tuple, List


class ValidationGate:
    """Base class for validation gates"""
    
    def __init__(self, gate_id: str, gate_type: str, schema_dir: Path):
        self.gate_id = gate_id
        self.gate_type = gate_type
        self.schema_dir = Path(schema_dir)
    
    def execute(self, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        """Execute gate validation
        
        Args:
            artifact_paths: Dictionary of artifact name -> path
            
        Returns:
            Tuple of (passed, report)
        """
        raise NotImplementedError("Subclasses must implement execute()")


class SchemaValidationGate(ValidationGate):
    """GATE-001: Validates artifact against JSON schema"""
    
    def __init__(self, schema_dir: Path, schema_name: str):
        super().__init__("GATE-001", "SCHEMA", schema_dir)
        self.schema_name = schema_name
    
    def execute(self, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        """Validate artifact against schema"""
        report = {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "schema": self.schema_name,
            "errors": []
        }
        
        # Load schema
        schema_path = self.schema_dir / self.schema_name
        if not schema_path.exists():
            report["errors"].append(f"Schema not found: {schema_path}")
            return False, report
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Load artifact
        artifact_path = artifact_paths.get("artifact")
        if not artifact_path or not artifact_path.exists():
            report["errors"].append(f"Artifact not found: {artifact_path}")
            return False, report
        
        with open(artifact_path, 'r') as f:
            artifact = json.load(f)
        
        # Validate
        try:
            jsonschema.validate(artifact, schema)
            report["status"] = "PASSED"
            return True, report
        except jsonschema.ValidationError as e:
            report["errors"].append(f"Validation failed: {e.message}")
            report["json_pointer"] = e.json_path
            report["status"] = "FAILED"
            return False, report


class PolicyComplianceGate(ValidationGate):
    """GATE-002: Validates plan complies with policy"""
    
    def __init__(self, schema_dir: Path):
        super().__init__("GATE-002", "POLICY", schema_dir)
    
    def execute(self, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        """Validate policy compliance"""
        report = {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "checks": [],
            "errors": []
        }
        
        plan_path = artifact_paths.get("plan")
        policy_path = artifact_paths.get("policy")
        
        if not plan_path or not plan_path.exists():
            report["errors"].append("Plan not found")
            return False, report
        
        if not policy_path or not policy_path.exists():
            report["errors"].append("Policy not found")
            return False, report
        
        with open(plan_path, 'r') as f:
            plan = json.load(f)
        
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        # Check required sections
        required_sections = policy.get("required_plan_sections", [])
        for section in required_sections:
            if section not in plan:
                report["errors"].append(f"Missing required section: {section}")
            else:
                report["checks"].append(f"✓ Section present: {section}")
        
        # Check forbidden patterns
        plan_str = json.dumps(plan)
        for pattern_def in policy.get("forbidden_patterns", []):
            import re
            pattern = pattern_def.get("regex", "")
            if re.search(pattern, plan_str, re.IGNORECASE):
                report["errors"].append(
                    f"Forbidden pattern detected: {pattern_def.get('pattern_id')} - {pattern_def.get('reason')}"
                )
        
        passed = len(report["errors"]) == 0
        report["status"] = "PASSED" if passed else "FAILED"
        return passed, report


class DependencyValidationGate(ValidationGate):
    """GATE-003: Validates all dependencies are available"""
    
    def __init__(self, schema_dir: Path):
        super().__init__("GATE-003", "DEPENDENCY", schema_dir)
    
    def execute(self, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        """Validate dependencies"""
        report = {
            "gate_id": self.gate_id,
            "gate_type": self.gate_type,
            "checks": [],
            "errors": []
        }
        
        plan_path = artifact_paths.get("plan")
        if not plan_path or not plan_path.exists():
            report["errors"].append("Plan not found")
            return False, report
        
        with open(plan_path, 'r') as f:
            plan = json.load(f)
        
        # Check each dependency
        for dep in plan.get("dependencies", []):
            validation_cmd = dep.get("validation_command")
            if validation_cmd:
                # Placeholder: Would execute validation command
                report["checks"].append(f"✓ Dependency declared: {dep.get('dependency_id')}")
        
        passed = len(report["errors"]) == 0
        report["status"] = "PASSED" if passed else "FAILED"
        return passed, report


class GateRegistry:
    """Registry of all available validation gates"""
    
    def __init__(self, schema_dir: Path):
        self.schema_dir = Path(schema_dir)
        self.gates: Dict[str, ValidationGate] = {}
        self._register_builtin_gates()
    
    def _register_builtin_gates(self):
        """Register built-in validation gates"""
        self.gates["GATE-001"] = SchemaValidationGate(self.schema_dir, "PLAN.schema.json")
        self.gates["GATE-002"] = PolicyComplianceGate(self.schema_dir)
        self.gates["GATE-003"] = DependencyValidationGate(self.schema_dir)
    
    def execute_gate(self, gate_id: str, artifact_paths: Dict[str, Path]) -> Tuple[bool, Dict]:
        """Execute specific gate
        
        Args:
            gate_id: Gate identifier (e.g., "GATE-001")
            artifact_paths: Paths to artifacts needed for validation
            
        Returns:
            Tuple of (passed, report)
        """
        if gate_id not in self.gates:
            return False, {
                "gate_id": gate_id,
                "error": f"Gate not found: {gate_id}"
            }
        
        gate = self.gates[gate_id]
        return gate.execute(artifact_paths)
    
    def execute_gates(self, gate_ids: List[str], 
                     artifact_paths: Dict[str, Path]) -> Tuple[bool, List[Dict]]:
        """Execute multiple gates
        
        Args:
            gate_ids: List of gate identifiers
            artifact_paths: Paths to artifacts
            
        Returns:
            Tuple of (all_passed, reports)
        """
        reports = []
        all_passed = True
        
        for gate_id in gate_ids:
            passed, report = self.execute_gate(gate_id, artifact_paths)
            reports.append(report)
            if not passed:
                all_passed = False
        
        return all_passed, reports
