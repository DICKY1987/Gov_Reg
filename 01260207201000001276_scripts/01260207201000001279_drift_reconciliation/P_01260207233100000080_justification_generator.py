"""Justification generator - evidence-linked update justifications.

FILE_ID: 01260207233100000080
PURPOSE: Generate justification reports for template updates
PHASE: Phase 2 - Template Drift Reconciliation
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json
import sys

repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


class JustificationGenerator:
    """Generates justification reports with evidence chains."""
    
    def __init__(self, gap_report: Dict[str, Any], patches: list):
        self.gap_report = gap_report
        self.patches = patches
    
    def generate_markdown(self) -> str:
        """Generate markdown justification report."""
        md = "# Template Update Justification\n\n"
        md += f"**Total Patches**: {len(self.patches)}\n\n"
        
        for idx, patch in enumerate(self.patches, 1):
            md += f"## Patch {idx}: {patch['op'].upper()} {patch['path']}\n\n"
            md += f"**Value**: `{patch.get('value')}`\n\n"
            md += f"**Justification**: Gap detected in canonical model comparison\n\n"
        
        return md
    
    def save_justification(self, output_path: Path) -> None:
        with open(output_path, 'w') as f:
            f.write(self.generate_markdown())


if __name__ == "__main__":
    print("Justification generator ready")
