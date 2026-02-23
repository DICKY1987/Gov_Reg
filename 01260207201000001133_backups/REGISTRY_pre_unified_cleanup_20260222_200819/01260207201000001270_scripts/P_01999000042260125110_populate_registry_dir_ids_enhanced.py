"""Enhanced dir_id population with coverage analysis (GAP-005).

FILE_ID: 01999000042260125110
PURPOSE: Enhanced populate_registry_dir_ids with null explanation and remediation
PHASE: Phase 2 - Coverage Enhancement
BACKLOG: 01999000042260125103 GAP-005
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))
from P_01260207233100000069_dir_id_handler import DirIdManager
from P_01260207233100000068_zone_classifier import ZoneClassifier


@dataclass
class NullExplanation:
    """Explanation for a null dir_id."""
    relative_path: str
    reason: str  # 'excluded_zone', 'missing_dir_id_anchor', 'path_outside_governed_root', 'stale_entry'
    details: Dict[str, Any]


@dataclass
class RemediationAction:
    """Remediation action for null dir_id."""
    relative_path: str
    action: str  # 'allocate_anchor', 'exclude_from_registry', 'move_to_governed', 'purge_stale'
    priority: str  # 'high', 'medium', 'low'


@dataclass
class CoverageReport:
    """Coverage report for dir_id population."""
    coverage_id: str
    timestamp: str
    total_entries: int
    dir_id_populated: int
    dir_id_null: int
    coverage_percentage: float
    coverage_by_zone: Dict[str, float]
    null_explanations: List[NullExplanation]
    remediation_plan: List[RemediationAction]
    evidence_path: Path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        result = asdict(self)
        result['evidence_path'] = str(result['evidence_path'])
        return result


class EnhancedDirIdPopulator:
    """Enhanced dir_id population with coverage analysis."""
    
    def __init__(
        self,
        project_root: Path,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize populator.
        
        Args:
            project_root: Project root directory
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.dir_id_manager = DirIdManager()
        self.zone_classifier = ZoneClassifier()
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "coverage"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def populate_registry_dir_ids_full(
        self,
        registry_path: Path,
        explain_nulls: bool = True,
        generate_remediation: bool = True
    ) -> CoverageReport:
        """Populate dir_ids with coverage analysis.
        
        Args:
            registry_path: Path to governance registry
            explain_nulls: Generate explanation for each null dir_id
            generate_remediation: Generate remediation plan for nulls
            
        Returns:
            CoverageReport: Coverage analysis and remediation plan
        """
        coverage_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Load registry
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        files = registry.get('files', [])
        total_entries = len(files)
        
        # Populate dir_ids
        dir_id_populated = 0
        dir_id_null = 0
        null_explanations: List[NullExplanation] = []
        zone_stats = defaultdict(lambda: {'total': 0, 'populated': 0})
        
        for entry in files:
            relative_path = entry.get('relative_path', '')
            current_dir_id = entry.get('dir_id')
            
            if not relative_path:
                continue
            
            file_path = self.project_root / relative_path
            
            # Get zone
            zone = 'unknown'
            if file_path.exists():
                zone = self.zone_classifier.compute_zone(file_path.parent)
            
            zone_stats[zone]['total'] += 1
            
            if current_dir_id:
                dir_id_populated += 1
                zone_stats[zone]['populated'] += 1
            else:
                dir_id_null += 1
                
                # Explain null if requested
                if explain_nulls:
                    explanation = self._explain_null_dir_id(file_path, zone)
                    null_explanations.append(explanation)
        
        # Calculate coverage
        coverage_percentage = (dir_id_populated / total_entries * 100) if total_entries > 0 else 0.0
        
        coverage_by_zone = {
            zone: (stats['populated'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
            for zone, stats in zone_stats.items()
        }
        
        # Generate remediation plan
        remediation_plan: List[RemediationAction] = []
        if generate_remediation:
            remediation_plan = self._generate_remediation_plan(null_explanations)
        
        # Save evidence
        evidence_path = self._save_evidence(
            coverage_id,
            timestamp,
            total_entries,
            dir_id_populated,
            dir_id_null,
            coverage_percentage,
            coverage_by_zone,
            null_explanations,
            remediation_plan
        )
        
        return CoverageReport(
            coverage_id=coverage_id,
            timestamp=timestamp,
            total_entries=total_entries,
            dir_id_populated=dir_id_populated,
            dir_id_null=dir_id_null,
            coverage_percentage=coverage_percentage,
            coverage_by_zone=coverage_by_zone,
            null_explanations=null_explanations,
            remediation_plan=remediation_plan,
            evidence_path=evidence_path
        )
    
    def _explain_null_dir_id(self, file_path: Path, zone: str) -> NullExplanation:
        """Explain why dir_id is null."""
        relative_path = str(file_path.relative_to(self.project_root))
        
        # Check if file exists
        if not file_path.exists():
            return NullExplanation(
                relative_path=relative_path,
                reason='stale_entry',
                details={'message': 'File no longer exists on disk'}
            )
        
        # Check zone
        if zone == 'excluded':
            return NullExplanation(
                relative_path=relative_path,
                reason='excluded_zone',
                details={'zone': zone, 'message': 'File in excluded zone (expected null)'}
            )
        
        # Check if parent has .dir_id
        parent_dir = file_path.parent
        dir_id_path = parent_dir / ".dir_id"
        
        if not dir_id_path.exists():
            return NullExplanation(
                relative_path=relative_path,
                reason='missing_dir_id_anchor',
                details={'parent_directory': str(parent_dir.relative_to(self.project_root))}
            )
        
        # Check if outside governed root
        if zone not in ['governed', 'excluded']:
            return NullExplanation(
                relative_path=relative_path,
                reason='path_outside_governed_root',
                details={'zone': zone, 'message': 'Path not under any governed zone'}
            )
        
        # Unknown reason
        return NullExplanation(
            relative_path=relative_path,
            reason='unknown',
            details={'zone': zone}
        )
    
    def _generate_remediation_plan(
        self,
        null_explanations: List[NullExplanation]
    ) -> List[RemediationAction]:
        """Generate remediation plan for null dir_ids."""
        actions = []
        
        for explanation in null_explanations:
            if explanation.reason == 'missing_dir_id_anchor':
                actions.append(RemediationAction(
                    relative_path=explanation.relative_path,
                    action='allocate_anchor',
                    priority='high'
                ))
            elif explanation.reason == 'stale_entry':
                actions.append(RemediationAction(
                    relative_path=explanation.relative_path,
                    action='purge_stale',
                    priority='high'
                ))
            elif explanation.reason == 'path_outside_governed_root':
                actions.append(RemediationAction(
                    relative_path=explanation.relative_path,
                    action='exclude_from_registry',
                    priority='medium'
                ))
            elif explanation.reason == 'excluded_zone':
                # Expected - no action needed
                pass
        
        return actions
    
    def _save_evidence(
        self,
        coverage_id: str,
        timestamp: str,
        total_entries: int,
        dir_id_populated: int,
        dir_id_null: int,
        coverage_percentage: float,
        coverage_by_zone: Dict[str, float],
        null_explanations: List[NullExplanation],
        remediation_plan: List[RemediationAction]
    ) -> Path:
        """Save coverage evidence."""
        evidence_file = self.evidence_dir / f"{coverage_id}_coverage.json"
        
        evidence = {
            "coverage_id": coverage_id,
            "timestamp": timestamp,
            "total_entries": total_entries,
            "dir_id_populated": dir_id_populated,
            "dir_id_null": dir_id_null,
            "coverage_percentage": coverage_percentage,
            "coverage_by_zone": coverage_by_zone,
            "null_explanations": [asdict(e) for e in null_explanations],
            "remediation_plan": [asdict(a) for a in remediation_plan]
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_file


def populate_registry_dir_ids_full(
    registry_path: Path,
    config_path: Path,
    explain_nulls: bool = True,
    generate_remediation: bool = True
) -> CoverageReport:
    """Populate dir_ids with coverage analysis (public API).
    
    Args:
        registry_path: Path to governance registry
        config_path: Path to IDPKG config
        explain_nulls: Generate explanation for each null dir_id
        generate_remediation: Generate remediation plan for nulls
        
    Returns:
        CoverageReport: Coverage analysis and remediation plan
    """
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    project_root = Path(config.get('project_root', Path.cwd()))
    
    populator = EnhancedDirIdPopulator(project_root)
    return populator.populate_registry_dir_ids_full(
        registry_path,
        explain_nulls,
        generate_remediation
    )


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced dir_id population with coverage analysis")
    parser.add_argument("--registry", type=Path, required=True, help="Path to governance registry")
    parser.add_argument("--config", type=Path, required=True, help="Path to IDPKG config")
    parser.add_argument("--no-explain", action="store_true", help="Skip null explanations")
    parser.add_argument("--no-remediation", action="store_true", help="Skip remediation plan")
    
    args = parser.parse_args()
    
    print(f"Running enhanced dir_id population...")
    report = populate_registry_dir_ids_full(
        args.registry,
        args.config,
        explain_nulls=not args.no_explain,
        generate_remediation=not args.no_remediation
    )
    
    print(f"\nCoverage Report:")
    print(f"  Total entries: {report.total_entries}")
    print(f"  Populated: {report.dir_id_populated} ({report.coverage_percentage:.1f}%)")
    print(f"  Null: {report.dir_id_null}")
    print(f"\nCoverage by zone:")
    for zone, coverage in report.coverage_by_zone.items():
        print(f"  {zone}: {coverage:.1f}%")
    print(f"\nRemediation actions: {len(report.remediation_plan)}")
    print(f"Evidence saved to: {report.evidence_path}")
