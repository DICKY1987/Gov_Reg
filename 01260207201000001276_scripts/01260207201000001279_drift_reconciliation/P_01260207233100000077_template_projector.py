"""Template projector - deterministic projection from authoritative sources.

FILE_ID: 01260207233100000077
PURPOSE: Project canonical template from schemas/policies/gates
PHASE: Phase 2 - Template Drift Reconciliation
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
import sys
import yaml

repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


class TemplateProjector:
    """Projects canonical template from authoritative sources.
    
    Authoritative sources (in precedence order):
    1. Schemas (contracts/schemas/)
    2. Policies (policies/)
    3. Gates (gates/)
    4. Execution rules (scripts/)
    """
    
    def __init__(self, project_root: Path):
        """Initialize template projector.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.schemas_dir = project_root / "contracts"
        self.policies_dir = project_root / "policies"
        self.gates_dir = project_root / "gates"
        self.scripts_dir = project_root / "scripts"
        
        # Canonical model (in-memory)
        self.canonical_model: Dict[str, Any] = {
            "gates": {},
            "schema_fields": {},
            "artifacts": {},
            "policies": {},
            "identity_rules": {}
        }
    
    def load_gates(self) -> Dict[str, Any]:
        """Load all gate definitions.
        
        Returns:
            Dictionary of gates by gate_id
        """
        gates = {}
        
        if not self.gates_dir.exists():
            return gates
        
        for gate_file in self.gates_dir.glob("*.py"):
            # Extract gate metadata from file
            gate_id = gate_file.stem
            
            with open(gate_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse docstring for gate metadata
            gate_info = {
                "gate_id": gate_id,
                "file": str(gate_file.relative_to(self.project_root)),
                "description": self._extract_docstring(content),
                "violation_codes": self._extract_violation_codes(content)
            }
            
            gates[gate_id] = gate_info
        
        return gates
    
    def load_schema_fields(self) -> Dict[str, Any]:
        """Load schema field definitions.
        
        Returns:
            Dictionary of schema fields
        """
        fields = {}
        
        # Load main registry schema
        schema_files = list(self.project_root.glob("*_governance_registry_schema*.json"))
        
        for schema_file in schema_files:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Extract properties
            if "properties" in schema:
                for field_name, field_spec in schema["properties"].items():
                    fields[field_name] = {
                        "name": field_name,
                        "type": field_spec.get("type"),
                        "description": field_spec.get("description"),
                        "derivation": field_spec.get("derivation"),
                        "source": str(schema_file.relative_to(self.project_root))
                    }
        
        # Load schema extensions
        if self.schemas_dir.exists():
            for schema_file in self.schemas_dir.glob("*.json"):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    try:
                        schema = json.load(f)
                        # Extract additional fields
                        if isinstance(schema, dict) and "properties" in schema:
                            for field_name, field_spec in schema["properties"].items():
                                if field_name not in fields:
                                    fields[field_name] = {
                                        "name": field_name,
                                        "type": field_spec.get("type"),
                                        "description": field_spec.get("description"),
                                        "source": str(schema_file.relative_to(self.project_root))
                                    }
                    except json.JSONDecodeError:
                        pass
        
        return fields
    
    def load_artifacts(self) -> Dict[str, Any]:
        """Load artifact definitions.
        
        Returns:
            Dictionary of artifacts
        """
        artifacts = {}
        
        # Load from policies
        if self.policies_dir.exists():
            for policy_file in self.policies_dir.glob("*.yaml"):
                with open(policy_file, 'r', encoding='utf-8') as f:
                    try:
                        policy = yaml.safe_load(f)
                        
                        if isinstance(policy, dict) and "artifacts" in policy:
                            for artifact in policy["artifacts"]:
                                artifact_id = artifact.get("artifact_id")
                                if artifact_id:
                                    artifacts[artifact_id] = artifact
                    except yaml.YAMLError:
                        pass
        
        return artifacts
    
    def load_policies(self) -> Dict[str, Any]:
        """Load policy definitions.
        
        Returns:
            Dictionary of policies
        """
        policies = {}
        
        if not self.policies_dir.exists():
            return policies
        
        for policy_file in self.policies_dir.glob("*.yaml"):
            with open(policy_file, 'r', encoding='utf-8') as f:
                try:
                    policy = yaml.safe_load(f)
                    
                    if isinstance(policy, dict):
                        policy_id = policy_file.stem
                        policies[policy_id] = {
                            "policy_id": policy_id,
                            "file": str(policy_file.relative_to(self.project_root)),
                            "content": policy
                        }
                except yaml.YAMLError:
                    pass
        
        return policies
    
    def load_identity_rules(self) -> Dict[str, Any]:
        """Load identity canonicality rules.
        
        Returns:
            Dictionary of identity rules
        """
        rules = {}
        
        # Load from contracts
        if self.schemas_dir.exists():
            canon_law = self.schemas_dir / "DIR_ID_CANONICALITY_LAW.json"
            if canon_law.exists():
                with open(canon_law, 'r', encoding='utf-8') as f:
                    rules["dir_id_canonicality"] = json.load(f)
        
        return rules
    
    def project_canonical_model(self) -> Dict[str, Any]:
        """Project canonical model from all authoritative sources.
        
        Returns:
            Complete canonical model
        """
        print("📊 Projecting canonical model from authoritative sources...")
        
        self.canonical_model["gates"] = self.load_gates()
        print(f"  ✅ Gates: {len(self.canonical_model['gates'])} loaded")
        
        self.canonical_model["schema_fields"] = self.load_schema_fields()
        print(f"  ✅ Schema fields: {len(self.canonical_model['schema_fields'])} loaded")
        
        self.canonical_model["artifacts"] = self.load_artifacts()
        print(f"  ✅ Artifacts: {len(self.canonical_model['artifacts'])} loaded")
        
        self.canonical_model["policies"] = self.load_policies()
        print(f"  ✅ Policies: {len(self.canonical_model['policies'])} loaded")
        
        self.canonical_model["identity_rules"] = self.load_identity_rules()
        print(f"  ✅ Identity rules: {len(self.canonical_model['identity_rules'])} loaded")
        
        return self.canonical_model
    
    def _extract_docstring(self, content: str) -> str:
        """Extract module docstring from Python file.
        
        Args:
            content: File content
            
        Returns:
            Docstring or empty string
        """
        lines = content.split('\n')
        in_docstring = False
        docstring = []
        
        for line in lines:
            if '"""' in line or "'''" in line:
                if in_docstring:
                    break
                in_docstring = True
                continue
            if in_docstring:
                docstring.append(line)
        
        return '\n'.join(docstring).strip()
    
    def _extract_violation_codes(self, content: str) -> List[str]:
        """Extract violation codes from gate file.
        
        Args:
            content: File content
            
        Returns:
            List of violation codes
        """
        codes = []
        for line in content.split('\n'):
            if 'violation_code=' in line or 'gate_id=' in line:
                # Extract code from string
                if '"' in line:
                    parts = line.split('"')
                    if len(parts) >= 2:
                        code = parts[1]
                        if code.startswith('GATE-') or code.startswith('DIR-'):
                            codes.append(code)
        return list(set(codes))


if __name__ == "__main__":
    projector = TemplateProjector(Path(__file__).parent.parent.parent)
    
    model = projector.project_canonical_model()
    
    print(f"\n📋 Canonical Model Summary:")
    print(f"  Gates: {len(model['gates'])}")
    print(f"  Schema fields: {len(model['schema_fields'])}")
    print(f"  Artifacts: {len(model['artifacts'])}")
    print(f"  Policies: {len(model['policies'])}")
    print(f"  Identity rules: {len(model['identity_rules'])}")
