"""Patch generator - RFC-6902 patches for template updates.

FILE_ID: 01260207233100000079
PURPOSE: Generate JSON patches for template updates
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


class PatchGenerator:
    """Generates RFC-6902 JSON patches for template updates."""
    
    def __init__(self, gap_report: Dict[str, Any], template: Dict[str, Any]):
        self.gap_report = gap_report
        self.template = template
        self.patches: List[Dict[str, Any]] = []
    
    def generate_patches(self) -> List[Dict[str, Any]]:
        """Generate all patches from gap report."""
        for gate_gap in self.gap_report.get("gaps", {}).get("gates", []):
            self.patches.append({
                "op": "add",
                "path": "/validation_gates/-",
                "value": {"gate_id": gate_gap["item_id"], "description": gate_gap["description"]}
            })
        
        for field_gap in self.gap_report.get("gaps", {}).get("schema_fields", []):
            self.patches.append({
                "op": "add",
                "path": "/step_contracts/0/fields/-",
                "value": {"name": field_gap["item_id"], "type": field_gap.get("field_type", "string")}
            })
        
        return self.patches
    
    def save_patches(self, output_path: Path) -> None:
        with open(output_path, 'w') as f:
            json.dump(self.patches, f, indent=2)


if __name__ == "__main__":
    print("Patch generator ready")
