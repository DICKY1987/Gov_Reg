"""Template comparator - compare canonical model to template.

FILE_ID: 01260207233100000078
PURPOSE: Compare canonical model to template and detect gaps
PHASE: Phase 2 - Template Drift Reconciliation
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json
import sys

repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scripts.drift_reconciliation.P_01260207233100000077_template_projector import TemplateProjector


class TemplateComparator:
    """Compares canonical model to template and detects drift.
    
    Gap statuses:
    - MISSING: Item in canonical model but not in template
    - PARTIAL: Item partially represented in template
    - ALREADY_COVERED: Item fully represented in template
    """
    
    def __init__(
        self,
        project_root: Path,
        template_path: Path,
        projector: TemplateProjector | None = None
    ):
        """Initialize template comparator.
        
        Args:
            project_root: Project root directory
            template_path: Path to template JSON file
            projector: Optional template projector (creates if None)
        """
        self.project_root = project_root
        self.template_path = template_path
        self.projector = projector or TemplateProjector(project_root)
        
        # Load template
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = json.load(f)
        
        # Gap report
        self.gap_report: Dict[str, List[Dict[str, Any]]] = {
            "gates": [],
            "schema_fields": [],
            "artifacts": [],
            "policies": [],
            "identity_rules": []
        }
    
    def compare_gates(self, canonical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare gates between canonical and template.
        
        Args:
            canonical_model: Canonical model from projector
            
        Returns:
            List of gate gaps
        """
        gaps = []
        
        canonical_gates = canonical_model.get("gates", {})
        template_gates = self.template.get("validation_gates", [])
        
        # Build template gate index
        template_gate_ids = {g.get("gate_id") for g in template_gates if g.get("gate_id")}
        
        for gate_id, gate_info in canonical_gates.items():
            if gate_id not in template_gate_ids:
                gaps.append({
                    "item_type": "gate",
                    "item_id": gate_id,
                    "status": "MISSING",
                    "description": gate_info.get("description", ""),
                    "source_file": gate_info.get("file", ""),
                    "recommendation": f"Add gate {gate_id} to template validation_gates[]"
                })
        
        return gaps
    
    def compare_schema_fields(self, canonical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare schema fields between canonical and template.
        
        Args:
            canonical_model: Canonical model from projector
            
        Returns:
            List of schema field gaps
        """
        gaps = []
        
        canonical_fields = canonical_model.get("schema_fields", {})
        template_contracts = self.template.get("step_contracts", [])
        
        # Build template field index from step contracts
        template_field_names = set()
        for contract in template_contracts:
            if "fields" in contract:
                for field in contract["fields"]:
                    if isinstance(field, dict):
                        template_field_names.add(field.get("name"))
                    elif isinstance(field, str):
                        template_field_names.add(field)
        
        for field_name, field_info in canonical_fields.items():
            if field_name not in template_field_names:
                gaps.append({
                    "item_type": "schema_field",
                    "item_id": field_name,
                    "status": "MISSING",
                    "description": field_info.get("description", ""),
                    "source_file": field_info.get("source", ""),
                    "field_type": field_info.get("type", ""),
                    "recommendation": f"Add field {field_name} to appropriate step_contract"
                })
        
        return gaps
    
    def compare_artifacts(self, canonical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare artifacts between canonical and template.
        
        Args:
            canonical_model: Canonical model from projector
            
        Returns:
            List of artifact gaps
        """
        gaps = []
        
        canonical_artifacts = canonical_model.get("artifacts", {})
        template_artifacts = self.template.get("artifacts", [])
        
        # Build template artifact index
        template_artifact_ids = {a.get("artifact_id") for a in template_artifacts if a.get("artifact_id")}
        
        for artifact_id, artifact_info in canonical_artifacts.items():
            if artifact_id not in template_artifact_ids:
                gaps.append({
                    "item_type": "artifact",
                    "item_id": artifact_id,
                    "status": "MISSING",
                    "description": artifact_info.get("description", ""),
                    "recommendation": f"Add artifact {artifact_id} to template artifacts[]"
                })
        
        return gaps
    
    def compare_identity_rules(self, canonical_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compare identity rules between canonical and template.
        
        Args:
            canonical_model: Canonical model from projector
            
        Returns:
            List of identity rule gaps
        """
        gaps = []
        
        canonical_rules = canonical_model.get("identity_rules", {})
        
        # Check if template has identity rules section
        template_has_identity = "identity_canonicality" in self.template or "id_canonicality" in self.template
        
        if canonical_rules and not template_has_identity:
            gaps.append({
                "item_type": "identity_rules",
                "item_id": "id_canonicality_section",
                "status": "MISSING",
                "description": "Identity canonicality rules not represented in template",
                "recommendation": "Add identity_canonicality section to template"
            })
        
        return gaps
    
    def generate_gap_report(self) -> Dict[str, Any]:
        """Generate complete gap report.
        
        Returns:
            Gap report with all detected gaps
        """
        print("🔍 Comparing canonical model to template...")
        
        # Project canonical model
        canonical_model = self.projector.project_canonical_model()
        
        # Compare each category
        self.gap_report["gates"] = self.compare_gates(canonical_model)
        print(f"  ✅ Gates: {len(self.gap_report['gates'])} gaps found")
        
        self.gap_report["schema_fields"] = self.compare_schema_fields(canonical_model)
        print(f"  ✅ Schema fields: {len(self.gap_report['schema_fields'])} gaps found")
        
        self.gap_report["artifacts"] = self.compare_artifacts(canonical_model)
        print(f"  ✅ Artifacts: {len(self.gap_report['artifacts'])} gaps found")
        
        self.gap_report["identity_rules"] = self.compare_identity_rules(canonical_model)
        print(f"  ✅ Identity rules: {len(self.gap_report['identity_rules'])} gaps found")
        
        # Calculate totals
        total_gaps = sum(len(gaps) for gaps in self.gap_report.values())
        
        report = {
            "template_file": str(self.template_path),
            "canonical_sources": {
                "gates": len(canonical_model.get("gates", {})),
                "schema_fields": len(canonical_model.get("schema_fields", {})),
                "artifacts": len(canonical_model.get("artifacts", {})),
                "policies": len(canonical_model.get("policies", {})),
                "identity_rules": len(canonical_model.get("identity_rules", {}))
            },
            "gaps_by_category": {
                "gates": len(self.gap_report["gates"]),
                "schema_fields": len(self.gap_report["schema_fields"]),
                "artifacts": len(self.gap_report["artifacts"]),
                "identity_rules": len(self.gap_report["identity_rules"])
            },
            "total_gaps": total_gaps,
            "gaps": self.gap_report
        }
        
        return report
    
    def save_gap_report(self, output_path: Path, report: Dict[str, Any]) -> None:
        """Save gap report to JSON file.
        
        Args:
            output_path: Path to save report
            report: Gap report from generate_gap_report()
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Gap report saved: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compare canonical model to template")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--template", type=Path, required=True, help="Template JSON file")
    parser.add_argument("--output", type=Path, help="Output gap report JSON file")
    
    args = parser.parse_args()
    
    comparator = TemplateComparator(
        project_root=args.project_root,
        template_path=args.template
    )
    
    report = comparator.generate_gap_report()
    
    print(f"\n📊 Gap Report Summary:")
    print(f"  Total gaps: {report['total_gaps']}")
    print(f"  Gates: {report['gaps_by_category']['gates']}")
    print(f"  Schema fields: {report['gaps_by_category']['schema_fields']}")
    print(f"  Artifacts: {report['gaps_by_category']['artifacts']}")
    print(f"  Identity rules: {report['gaps_by_category']['identity_rules']}")
    
    if args.output:
        comparator.save_gap_report(args.output, report)
    
    sys.exit(0 if report['total_gaps'] == 0 else 1)
