"""
GateEnforcer - Governance Enforcement Runtime

Provides unified gate enforcement with:
- Pre/post execution gate checks
- Integration with gate catalog
- Telemetry emission for gate results
- Evidence generation

FILE_ID: 01999000042260125143
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, Any, List, Tuple, Optional
from P_01999000042260125141_telemetry_emitter import TelemetryEmitter


@dataclass
class GateResult:
    """Result of a single gate check."""
    gate_id: str
    passed: bool
    severity: str
    violations: List[Dict[str, Any]]
    evidence_path: Optional[Path] = None
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        if self.evidence_path:
            result['evidence_path'] = str(self.evidence_path)
        return result


class GateEnforcer:
    """
    Unified gate enforcement runtime.
    
    Loads gate catalog, registers checkers, enforces gates, and emits telemetry.
    """
    
    def __init__(
        self,
        gate_catalog_path: Path,
        telemetry: TelemetryEmitter,
        run_bundle=None  # Optional RunBundle for evidence paths
    ):
        """
        Initialize gate enforcer.
        
        Args:
            gate_catalog_path: Path to GATE_CATALOG.json
            telemetry: TelemetryEmitter instance for result emission
            run_bundle: Optional RunBundle for evidence path generation
        """
        self.gate_catalog_path = Path(gate_catalog_path)
        self.telemetry = telemetry
        self.run_bundle = run_bundle
        self.gate_catalog = self._load_catalog()
        self.checkers: Dict[str, Callable] = {}
    
    def register_checker(self, gate_id: str, checker: Callable[[Dict], GateResult]) -> None:
        """
        Register a checker function for a gate.
        
        Args:
            gate_id: Gate identifier (e.g., "DIR-G1")
            checker: Callable that takes context dict and returns GateResult
        """
        self.checkers[gate_id] = checker
    
    def enforce_pre_execution_gates(self, context: Dict[str, Any]) -> Tuple[bool, List[GateResult]]:
        """
        Enforce all pre-execution gates.
        
        Args:
            context: Context dict with data needed by gate checkers
            
        Returns:
            Tuple of (all_passed, list_of_results)
        """
        pre_gates = [
            gate for gate in self.gate_catalog.get("gates", [])
            if gate.get("phase") == "pre_execution"
        ]
        
        return self._enforce_gates(pre_gates, context)
    
    def enforce_post_execution_gates(self, context: Dict[str, Any]) -> Tuple[bool, List[GateResult]]:
        """
        Enforce all post-execution gates.
        
        Args:
            context: Context dict with data needed by gate checkers
            
        Returns:
            Tuple of (all_passed, list_of_results)
        """
        post_gates = [
            gate for gate in self.gate_catalog.get("gates", [])
            if gate.get("phase") == "post_execution"
        ]
        
        return self._enforce_gates(post_gates, context)
    
    def enforce_single_gate(self, gate_id: str, context: Dict[str, Any]) -> GateResult:
        """
        Enforce a single gate by ID.
        
        Args:
            gate_id: Gate identifier
            context: Context dict with data needed by checker
            
        Returns:
            GateResult
        """
        if gate_id not in self.checkers:
            return GateResult(
                gate_id=gate_id,
                passed=False,
                severity="error",
                violations=[{"error": f"No checker registered for gate {gate_id}"}],
                message=f"No checker registered for gate {gate_id}"
            )
        
        checker = self.checkers[gate_id]
        result = checker(context)
        
        # Emit telemetry
        self.telemetry.emit_gate_result(
            gate_id=result.gate_id,
            passed=result.passed,
            violations=result.violations,
            evidence_path=result.evidence_path
        )
        
        # Write evidence if run_bundle available
        if self.run_bundle:
            evidence_path = self.run_bundle.gate_evidence_path(gate_id)
            report_path = evidence_path / "report.json"
            report_path.write_text(
                json.dumps(result.to_dict(), indent=2),
                encoding='utf-8'
            )
            result.evidence_path = evidence_path
        
        return result
    
    def _enforce_gates(self, gates: List[Dict], context: Dict[str, Any]) -> Tuple[bool, List[GateResult]]:
        """
        Enforce a list of gates.
        
        Returns:
            Tuple of (all_passed, results)
        """
        results = []
        all_passed = True
        
        for gate in gates:
            gate_id = gate.get("gate_id")
            if not gate_id:
                continue
            
            result = self.enforce_single_gate(gate_id, context)
            results.append(result)
            
            # Check if gate is BLOCK severity and failed
            severity = gate.get("severity", "WARN")
            if severity == "BLOCK" and not result.passed:
                all_passed = False
        
        return all_passed, results
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load gate catalog JSON."""
        if not self.gate_catalog_path.exists():
            return {"gates": []}
        
        with open(self.gate_catalog_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_gate_info(self, gate_id: str) -> Optional[Dict[str, Any]]:
        """
        Get gate definition from catalog.
        
        Args:
            gate_id: Gate identifier
            
        Returns:
            Gate definition dict or None if not found
        """
        for gate in self.gate_catalog.get("gates", []):
            if gate.get("gate_id") == gate_id:
                return gate
        return None
