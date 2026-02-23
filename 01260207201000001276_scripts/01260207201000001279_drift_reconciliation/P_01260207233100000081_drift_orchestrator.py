"""Drift orchestrator - main pipeline for template drift reconciliation.

FILE_ID: 01260207233100000081
PURPOSE: Orchestrate template drift reconciliation pipeline
PHASE: Phase 2 - Template Drift Reconciliation
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import sys

repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scripts.drift_reconciliation.P_01260207233100000077_template_projector import TemplateProjector
from scripts.drift_reconciliation.P_01260207233100000078_template_comparator import TemplateComparator
from scripts.drift_reconciliation.P_01260207233100000079_patch_generator import PatchGenerator
from scripts.drift_reconciliation.P_01260207233100000080_justification_generator import JustificationGenerator


class DriftOrchestrator:
    """Orchestrates complete template drift reconciliation pipeline."""
    
    def __init__(self, project_root: Path, template_path: Path, dry_run: bool = True):
        self.project_root = project_root
        self.template_path = template_path
        self.dry_run = dry_run
    
    def run_pipeline(self) -> Dict[str, Any]:
        """Run complete drift reconciliation pipeline."""
        print("🚀 Starting Template Drift Reconciliation Pipeline")
        print(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE'}\n")
        
        # Step 1: Project canonical model
        print("Step 1: Projecting canonical model...")
        projector = TemplateProjector(self.project_root)
        canonical_model = projector.project_canonical_model()
        
        # Step 2: Compare to template
        print("\nStep 2: Comparing to template...")
        comparator = TemplateComparator(self.project_root, self.template_path, projector)
        gap_report = comparator.generate_gap_report()
        
        # Step 3: Generate patches
        print("\nStep 3: Generating patches...")
        with open(self.template_path, 'r') as f:
            template = json.load(f)
        
        generator = PatchGenerator(gap_report, template)
        patches = generator.generate_patches()
        print(f"   Generated {len(patches)} patches")
        
        # Step 4: Generate justification
        print("\nStep 4: Generating justification...")
        justification = JustificationGenerator(gap_report, patches)
        
        # Save outputs
        output_dir = self.project_root / "template_drift_analysis"
        output_dir.mkdir(exist_ok=True)
        
        comparator.save_gap_report(output_dir / "gap_report.json", gap_report)
        generator.save_patches(output_dir / "patches.json")
        justification.save_justification(output_dir / "justification.md")
        
        print(f"\n✅ Pipeline complete. Outputs saved to: {output_dir}")
        
        return {
            "gaps_found": gap_report["total_gaps"],
            "patches_generated": len(patches),
            "dry_run": self.dry_run
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run template drift reconciliation")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    
    args = parser.parse_args()
    
    orchestrator = DriftOrchestrator(args.project_root, args.template, dry_run=not args.live)
    result = orchestrator.run_pipeline()
    
    sys.exit(0 if result["gaps_found"] == 0 else 1)
