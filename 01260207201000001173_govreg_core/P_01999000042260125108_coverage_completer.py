"""Coverage completion for dir_id population (GAP-005).

FILE_ID: 01999000042260125108
PURPOSE: Analyze and complete dir_id coverage gaps in registry
PHASE: Phase 5 - Coverage Completion
BACKLOG: 01999000042260125103 GAP-005

Analyzes registry entries with null dir_id and provides remediation:
- Missing .dir_id anchors (can allocate)
- Paths outside governed zones (should exclude)
- Stale entries (path no longer exists)
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, asdict, field
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver


@dataclass
class CoverageGap:
    """A single coverage gap (null dir_id)."""
    file_id: str
    relative_path: str
    gap_type: Literal['missing_anchor', 'outside_governed', 'excluded', 'stale']
    can_auto_fix: bool
    details: Dict[str, any]
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CoverageAnalysis:
    """Result of coverage gap analysis."""
    timestamp: str
    total_entries: int
    entries_with_dir_id: int
    entries_without_dir_id: int
    coverage_percentage: float
    gaps: List[CoverageGap] = field(default_factory=list)
    remediation_plan: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['gaps'] = [gap.to_dict() if hasattr(gap, 'to_dict') else gap for gap in self.gaps]
        return result


class DirIdCoverageCompleter:
    """Analyzes and completes dir_id coverage gaps.
    
    Identifies reasons for null dir_id entries:
    1. Missing .dir_id anchor in parent directory
    2. Path outside governed zones
    3. Explicitly excluded zone
    4. Stale entry (path no longer exists)
    """
    
    def __init__(
        self,
        project_root: Path,
        registry_path: Path,
        project_root_id: str,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize coverage completer.
        
        Args:
            project_root: Project root directory
            registry_path: Path to registry JSON file
            project_root_id: Project root dir_id
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.registry_path = registry_path
        self.project_root_id = project_root_id
        
        self.zone_classifier = ZoneClassifier()
        self.resolver = DirectoryIdentityResolver(project_root, project_root_id, self.zone_classifier)
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "coverage"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Load registry
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Load registry with encoding handling."""
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except UnicodeDecodeError:
            with open(self.registry_path, 'r', encoding='latin-1') as f:
                return json.load(f)
    
    def analyze_gaps(self) -> CoverageAnalysis:
        """Analyze all coverage gaps in registry.
        
        Returns:
            CoverageAnalysis: Comprehensive gap analysis
        """
        timestamp = datetime.now(timezone.utc)
        gaps: List[CoverageGap] = []
        
        entries_with_dir_id = 0
        entries_without_dir_id = 0
        
        for entry in self.registry.get('files', []):
            dir_id = entry.get('dir_id')
            
            if dir_id:
                entries_with_dir_id += 1
                continue
            
            entries_without_dir_id += 1
            
            # Analyze why dir_id is missing
            gap = self._analyze_single_gap(entry)
            gaps.append(gap)
        
        total_entries = entries_with_dir_id + entries_without_dir_id
        coverage_percentage = (entries_with_dir_id / total_entries * 100) if total_entries > 0 else 0.0
        
        # Create remediation plan
        remediation_plan = self._create_remediation_plan(gaps)
        
        analysis = CoverageAnalysis(
            timestamp=timestamp.isoformat(),
            total_entries=total_entries,
            entries_with_dir_id=entries_with_dir_id,
            entries_without_dir_id=entries_without_dir_id,
            coverage_percentage=coverage_percentage,
            gaps=gaps,
            remediation_plan=remediation_plan
        )
        
        # Save evidence
        self._save_evidence(analysis, timestamp.strftime("%Y%m%d_%H%M%S"))
        
        return analysis
    
    def _analyze_single_gap(self, entry: Dict) -> CoverageGap:
        """Analyze a single entry with null dir_id."""
        file_id = entry.get('file_id', 'unknown')
        relative_path = entry.get('relative_path', '')
        
        file_path = self.project_root / relative_path
        
        # Check if path exists
        if not file_path.exists():
            return CoverageGap(
                file_id=file_id,
                relative_path=relative_path,
                gap_type='stale',
                can_auto_fix=True,  # Can remove from registry
                details={'reason': 'Path no longer exists'}
            )
        
        # Check zone
        zone = self.zone_classifier.compute_zone(file_path)
        
        if zone != 'governed':
            return CoverageGap(
                file_id=file_id,
                relative_path=relative_path,
                gap_type='outside_governed' if zone == 'unclassified' else 'excluded',
                can_auto_fix=True,  # Can mark with exclusion reason
                details={'zone': zone}
            )
        
        # Check if parent has .dir_id
        parent_dir = file_path.parent
        parent_dir_id_file = parent_dir / '.dir_id'
        
        if not parent_dir_id_file.exists():
            return CoverageGap(
                file_id=file_id,
                relative_path=relative_path,
                gap_type='missing_anchor',
                can_auto_fix=True,  # Can allocate .dir_id
                details={'parent_dir': str(parent_dir.relative_to(self.project_root))}
            )
        
        # Parent has .dir_id but entry doesn't - can fix
        return CoverageGap(
            file_id=file_id,
            relative_path=relative_path,
            gap_type='missing_anchor',
            can_auto_fix=True,
            details={'reason': 'Parent .dir_id exists but not populated in registry'}
        )
    
    def _create_remediation_plan(self, gaps: List[CoverageGap]) -> Dict[str, int]:
        """Create remediation plan from gaps."""
        plan = {
            'allocate_anchors': 0,
            'mark_excluded': 0,
            'purge_stale': 0,
            'not_fixable': 0
        }
        
        for gap in gaps:
            if gap.gap_type == 'missing_anchor':
                plan['allocate_anchors'] += 1
            elif gap.gap_type in ('outside_governed', 'excluded'):
                plan['mark_excluded'] += 1
            elif gap.gap_type == 'stale':
                plan['purge_stale'] += 1
            elif not gap.can_auto_fix:
                plan['not_fixable'] += 1
        
        return plan
    
    def complete_coverage(
        self,
        analysis: Optional[CoverageAnalysis] = None,
        auto_apply: bool = False
    ) -> Dict[str, int]:
        """Execute coverage completion based on analysis.
        
        Args:
            analysis: Pre-computed analysis (runs new if None)
            auto_apply: If True, apply fixes automatically
            
        Returns:
            Dict with counts of fixes applied
        """
        if analysis is None:
            analysis = self.analyze_gaps()
        
        fixes_applied = {
            'anchors_allocated': 0,
            'entries_marked_excluded': 0,
            'stale_entries_purged': 0,
            'total_fixed': 0
        }
        
        if not auto_apply:
            return fixes_applied
        
        # Process each gap
        for gap in analysis.gaps:
            if not gap.can_auto_fix:
                continue
            
            try:
                if gap.gap_type == 'missing_anchor':
                    self._allocate_anchor(gap.relative_path)
                    fixes_applied['anchors_allocated'] += 1
                
                elif gap.gap_type in ('outside_governed', 'excluded'):
                    self._mark_excluded(gap.file_id, gap.details.get('zone', 'unknown'))
                    fixes_applied['entries_marked_excluded'] += 1
                
                elif gap.gap_type == 'stale':
                    self._purge_entry(gap.file_id)
                    fixes_applied['stale_entries_purged'] += 1
                
                fixes_applied['total_fixed'] += 1
                
            except Exception:
                pass  # Log but continue
        
        return fixes_applied
    
    def _allocate_anchor(self, relative_path: str):
        """Allocate .dir_id anchor for path."""
        file_path = self.project_root / relative_path
        parent_dir = file_path.parent
        
        # Allocate dir_id for parent
        self.resolver.resolve_identity(parent_dir, allocate_if_missing=True)
    
    def _mark_excluded(self, file_id: str, zone: str):
        """Mark entry as excluded in registry."""
        for entry in self.registry['files']:
            if entry.get('file_id') == file_id:
                entry['dir_id'] = f"EXCLUDED_{zone.upper()}"
                break
        # Would save registry here
    
    def _purge_entry(self, file_id: str):
        """Remove stale entry from registry."""
        self.registry['files'] = [
            entry for entry in self.registry['files']
            if entry.get('file_id') != file_id
        ]
        # Would save registry here
    
    def _save_evidence(self, analysis: CoverageAnalysis, timestamp: str):
        """Save coverage analysis evidence."""
        evidence_file = self.evidence_dir / f"gap_analysis_{timestamp}.json"
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(analysis.to_dict(), f, indent=2)


def complete_dir_id_coverage(
    project_root: Path,
    registry_path: Path,
    project_root_id: str,
    auto_apply: bool = False
) -> CoverageAnalysis:
    """Analyze and optionally complete dir_id coverage (public API).
    
    Args:
        project_root: Project root directory
        registry_path: Path to registry JSON file
        project_root_id: Project root dir_id
        auto_apply: If True, apply fixes automatically
        
    Returns:
        CoverageAnalysis: Comprehensive coverage analysis
    """
    completer = DirIdCoverageCompleter(project_root, registry_path, project_root_id)
    analysis = completer.analyze_gaps()
    
    if auto_apply:
        fixes = completer.complete_coverage(analysis, auto_apply=True)
        analysis.remediation_plan['fixes_applied'] = fixes
    
    return analysis


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze and complete dir_id coverage")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--registry", type=Path, required=True, help="Path to registry JSON")
    parser.add_argument("--root-id", required=True, help="Project root dir_id")
    parser.add_argument("--auto-apply", action="store_true", help="Apply fixes automatically")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    
    args = parser.parse_args()
    
    analysis = complete_dir_id_coverage(
        args.project_root,
        args.registry,
        args.root_id,
        args.auto_apply
    )
    
    if args.json:
        print(json.dumps(analysis.to_dict(), indent=2))
    else:
        print(f"Coverage Analysis:")
        print(f"  Total entries: {analysis.total_entries}")
        print(f"  With dir_id: {analysis.entries_with_dir_id}")
        print(f"  Without dir_id: {analysis.entries_without_dir_id}")
        print(f"  Coverage: {analysis.coverage_percentage:.1f}%")
        print(f"\nRemediation Plan:")
        for action, count in analysis.remediation_plan.items():
            print(f"  {action}: {count}")
