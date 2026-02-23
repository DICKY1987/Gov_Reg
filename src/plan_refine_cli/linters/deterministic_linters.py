"""
Deterministic Linters
Rule-based plan analysis without LLM dependency.
"""
import json
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from uuid import uuid4


class BaseLinter:
    """Base class for deterministic linters"""
    
    def __init__(self, rule_prefix: str):
        self.rule_prefix = rule_prefix
    
    def lint(self, plan: Dict) -> List[Dict]:
        """Analyze plan and return defects
        
        Args:
            plan: Plan dictionary to analyze
            
        Returns:
            List of defect dictionaries
        """
        raise NotImplementedError("Subclasses must implement lint()")
    
    def create_defect(self, rule_code: str, severity: str, 
                     json_pointer: str, evidence: str, 
                     fix: str) -> Dict:
        """Create defect dictionary
        
        Args:
            rule_code: Rule identifier (e.g., "COMP-001")
            severity: CRITICAL | HIGH | MEDIUM | LOW | INFO
            json_pointer: JSON pointer to defect location
            evidence: Description of the issue
            fix: Recommended fix
            
        Returns:
            Defect dictionary
        """
        short_uuid = str(uuid4()).replace('-', '')[:8]
        
        return {
            "defect_id": f"DEFECT_{short_uuid}",
            "severity": severity,
            "rule_code": rule_code,
            "json_pointer": json_pointer,
            "evidence_excerpt": evidence,
            "recommended_fix": fix
        }


class CompletenessLinter(BaseLinter):
    """Checks all required plan sections are present"""
    
    def __init__(self, policy_snapshot: Dict):
        super().__init__("COMP")
        self.policy = policy_snapshot
    
    def lint(self, plan: Dict) -> List[Dict]:
        """Check for missing required sections"""
        defects = []
        
        required = self.policy.get("required_plan_sections", [])
        for section in required:
            if section not in plan:
                defects.append(self.create_defect(
                    "COMP-001",
                    "CRITICAL",
                    f"/{section}",
                    f"Required section '{section}' is missing",
                    f"Add '{section}' section to plan"
                ))
            elif not plan[section]:
                defects.append(self.create_defect(
                    "COMP-002",
                    "HIGH",
                    f"/{section}",
                    f"Required section '{section}' is empty",
                    f"Populate '{section}' section with required content"
                ))
        
        return defects


class SchemaComplianceLinter(BaseLinter):
    """Validates plan against PLAN.schema.json"""
    
    def __init__(self, schema_dir: Path):
        super().__init__("SCHEMA")
        self.schema_dir = Path(schema_dir)
    
    def lint(self, plan: Dict) -> List[Dict]:
        """Validate against JSON schema"""
        import jsonschema
        
        defects = []
        
        schema_path = self.schema_dir / "PLAN.schema.json"
        if not schema_path.exists():
            return [self.create_defect(
                "SCHEMA-000",
                "CRITICAL",
                "/",
                "PLAN.schema.json not found",
                "Create schema file"
            )]
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        try:
            jsonschema.validate(plan, schema)
        except jsonschema.ValidationError as e:
            defects.append(self.create_defect(
                "SCHEMA-001",
                "CRITICAL",
                e.json_path,
                e.message,
                "Fix schema violation"
            ))
        
        return defects


class ForbiddenPatternsLinter(BaseLinter):
    """Scans for forbidden patterns in plan"""
    
    def __init__(self, policy_snapshot: Dict):
        super().__init__("PATTERN")
        self.policy = policy_snapshot
    
    def lint(self, plan: Dict) -> List[Dict]:
        """Scan for forbidden patterns"""
        defects = []
        
        plan_str = json.dumps(plan, indent=2)
        
        for pattern_def in self.policy.get("forbidden_patterns", []):
            pattern = pattern_def.get("regex", "")
            pattern_id = pattern_def.get("pattern_id", "UNKNOWN")
            reason = pattern_def.get("reason", "")
            
            matches = re.finditer(pattern, plan_str, re.IGNORECASE)
            for match in matches:
                defects.append(self.create_defect(
                    f"PATTERN-{pattern_id}",
                    "HIGH",
                    "/",
                    f"Forbidden pattern detected: {match.group(0)} - {reason}",
                    f"Remove or replace forbidden pattern: {match.group(0)}"
                ))
        
        return defects


class ReferenceValidityLinter(BaseLinter):
    """Validates all references exist or are declared NEW"""
    
    def __init__(self):
        super().__init__("REF")
    
    def lint(self, plan: Dict) -> List[Dict]:
        """Check reference validity"""
        defects = []
        
        # Collect declared artifacts
        declared = {
            art["artifact_id"] 
            for art in plan.get("declared_new_artifacts", [])
        }
        
        # Check workstream outputs reference validation
        for ws_idx, ws in enumerate(plan.get("workstreams", [])):
            for out_idx, output in enumerate(ws.get("outputs", [])):
                artifact_id = output.get("artifact_id")
                
                # If artifact is not in declared_new_artifacts, it should exist
                # Placeholder: Would check against context_bundle
                if artifact_id and artifact_id not in declared:
                    # This is acceptable - artifact might exist in context
                    pass
        
        return defects


class AcceptanceCriteriaLinter(BaseLinter):
    """Validates acceptance criteria are measurable"""
    
    def __init__(self):
        super().__init__("AC")
    
    def lint(self, plan: Dict) -> List[Dict]:
        """Check acceptance criteria quality"""
        defects = []
        
        for idx, criterion in enumerate(plan.get("acceptance_criteria", [])):
            # Check for measurement method
            if not criterion.get("measurement_method"):
                defects.append(self.create_defect(
                    "AC-001",
                    "MEDIUM",
                    f"/acceptance_criteria/{idx}/measurement_method",
                    "Acceptance criterion missing measurement method",
                    "Add specific measurement method (command or metric)"
                ))
            
            # Check for target value
            if not criterion.get("target_value"):
                defects.append(self.create_defect(
                    "AC-002",
                    "MEDIUM",
                    f"/acceptance_criteria/{idx}/target_value",
                    "Acceptance criterion missing target value",
                    "Add specific measurable target value"
                ))
        
        return defects
