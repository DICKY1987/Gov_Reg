"""Registry ↔ Filesystem Reconciliation (GAP-003).

FILE_ID: 01999000042260125106
PURPOSE: Bidirectional reconciliation between registry and filesystem
PHASE: Phase 3 - Data Integrity
BACKLOG: 01999000042260125103 GAP-003

Implements strict bidirectional sync checking:
- Registry orphans (paths in registry but not on disk)
- Unregistered files (files on disk but not in registry)
- ID mismatches (registry vs filesystem)
- Duplicate IDs/paths
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Literal, Set
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver


@dataclass
class ReconciliationIssue:
    """Single reconciliation issue found."""
    issue_type: Literal[
        'REGISTRY_ORPHAN',
        'DISK_UNREGISTERED', 
        'ID_MISMATCH',
        'DUPLICATE_FILE_ID',
        'DUPLICATE_PATH',
        'MISSING_DIR_ID'
    ]
    severity: Literal['ERROR', 'WARNING', 'INFO']
    defect_code: str
    path: str
    details: Dict[str, any]
    can_auto_fix: bool
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ReconciliationResult:
    """Result of a full reconciliation run."""
    timestamp: str
    zone: str
    total_registry_entries: int
    total_filesystem_files: int
    issues: List[ReconciliationIssue] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
    duration_seconds: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['issues'] = [issue.to_dict() if hasattr(issue, 'to_dict') else issue for issue in self.issues]
        return result


class RegistryFilesystemReconciler:
    """Bidirectional reconciliation between registry and filesystem.
    
    Performs strict checks:
    1. Every registry path exists on disk
    2. Every governed disk file exists in registry
    3. dir_id in registry matches parent .dir_id on disk
    4. file_id in registry matches filename prefix
    5. No duplicate file_ids
    6. No duplicate paths
    """
    
    def __init__(
        self,
        project_root: Path,
        registry_path: Path,
        zone_classifier: Optional[ZoneClassifier] = None,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize reconciler.
        
        Args:
            project_root: Project root directory
            registry_path: Path to registry JSON file
            zone_classifier: Zone classifier (creates if None)
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.registry_path = registry_path
        
        if zone_classifier is None:
            zone_classifier = ZoneClassifier()
        self.zone_classifier = zone_classifier
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "reconciliation"
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
    
    def reconcile(
        self,
        zone: str = "all",
        auto_fix: bool = False
    ) -> ReconciliationResult:
        """Perform full bidirectional reconciliation.
        
        Args:
            zone: Zone to reconcile ('all', 'governed', 'staging', etc.)
            auto_fix: If True, attempt automatic repairs
            
        Returns:
            ReconciliationResult: Comprehensive reconciliation report
        """
        start_time = datetime.now(timezone.utc)
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        
        issues: List[ReconciliationIssue] = []
        
        # Check 1: Registry → Filesystem (orphan detection)
        registry_orphans = self._check_registry_orphans(zone)
        issues.extend(registry_orphans)
        
        # Check 2: Filesystem → Registry (unregistered detection)
        unregistered = self._check_unregistered_files(zone)
        issues.extend(unregistered)
        
        # Check 3: ID mismatches
        id_mismatches = self._check_id_mismatches()
        issues.extend(id_mismatches)
        
        # Check 4: Duplicate file_ids
        duplicate_ids = self._check_duplicate_file_ids()
        issues.extend(duplicate_ids)
        
        # Check 5: Duplicate paths
        duplicate_paths = self._check_duplicate_paths()
        issues.extend(duplicate_paths)
        
        # Compute statistics
        stats = self._compute_stats(issues)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        result = ReconciliationResult(
            timestamp=start_time.isoformat(),
            zone=zone,
            total_registry_entries=len(self.registry.get('files', [])),
            total_filesystem_files=stats.get('total_filesystem_files', 0),
            issues=issues,
            stats=stats,
            duration_seconds=duration
        )
        
        # Save evidence
        self._save_evidence(result, timestamp)
        
        # Auto-fix if requested
        if auto_fix:
            self._apply_auto_fixes(issues, timestamp)
        
        return result
    
    def _check_registry_orphans(self, zone: str) -> List[ReconciliationIssue]:
        """Check for paths in registry that don't exist on disk."""
        issues = []
        
        for entry in self.registry.get('files', []):
            relative_path = entry.get('relative_path', '')
            if not relative_path:
                continue
            
            # Zone filtering
            if zone != "all":
                entry_zone = self.zone_classifier.compute_zone(self.project_root / relative_path)
                if entry_zone != zone:
                    continue
            
            # Check if file exists
            file_path = self.project_root / relative_path
            if not file_path.exists():
                issues.append(ReconciliationIssue(
                    issue_type='REGISTRY_ORPHAN',
                    severity='ERROR',
                    defect_code='REGISTRY-ORPHAN-001',
                    path=relative_path,
                    details={
                        'file_id': entry.get('file_id'),
                        'registry_index': self.registry['files'].index(entry)
                    },
                    can_auto_fix=True  # Can remove from registry
                ))
        
        return issues
    
    def _check_unregistered_files(self, zone: str) -> List[ReconciliationIssue]:
        """Check for files on disk that aren't in registry."""
        issues = []
        
        # Build registry path index
        registry_paths = {entry.get('relative_path') for entry in self.registry.get('files', []) if entry.get('relative_path')}
        
        # Walk filesystem
        filesystem_count = 0
        for file_path in self.project_root.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip metadata files
            if file_path.name.startswith('.'):
                continue
            
            filesystem_count += 1
            
            try:
                relative_path = str(file_path.relative_to(self.project_root))
            except ValueError:
                continue
            
            # Zone filtering
            file_zone = self.zone_classifier.compute_zone(file_path)
            if zone != "all" and file_zone != zone:
                continue
            
            # Skip non-governed zones
            if file_zone != 'governed':
                continue
            
            # Check if in registry
            if relative_path not in registry_paths:
                # Extract file_id from filename if present
                file_id = None
                name = file_path.name
                if '_' in name:
                    prefix = name.split('_')[0]
                    if prefix.isdigit() and len(prefix) == 20:
                        file_id = prefix
                
                issues.append(ReconciliationIssue(
                    issue_type='DISK_UNREGISTERED',
                    severity='WARNING',
                    defect_code='DISK-UNREGISTERED-002',
                    path=relative_path,
                    details={
                        'file_id': file_id,
                        'zone': file_zone,
                        'size_bytes': file_path.stat().st_size
                    },
                    can_auto_fix=True  # Can register
                ))
        
        # Store filesystem count for stats
        self._filesystem_count = filesystem_count
        
        return issues
    
    def _check_id_mismatches(self) -> List[ReconciliationIssue]:
        """Check for dir_id/file_id mismatches between registry and filesystem."""
        issues = []
        
        for entry in self.registry.get('files', []):
            relative_path = entry.get('relative_path', '')
            if not relative_path:
                continue
            
            file_path = self.project_root / relative_path
            if not file_path.exists():
                continue  # Already caught by orphan check
            
            # Check dir_id match
            registry_dir_id = entry.get('dir_id')
            if registry_dir_id:
                # Find parent .dir_id
                parent_dir = file_path.parent
                parent_dir_id_file = parent_dir / '.dir_id'
                
                if parent_dir_id_file.exists():
                    try:
                        with open(parent_dir_id_file, 'r', encoding='utf-8') as f:
                            parent_data = json.load(f)
                        filesystem_dir_id = parent_data.get('dir_id')
                        
                        if filesystem_dir_id and filesystem_dir_id != registry_dir_id:
                            issues.append(ReconciliationIssue(
                                issue_type='ID_MISMATCH',
                                severity='ERROR',
                                defect_code='ID-MISMATCH-003',
                                path=relative_path,
                                details={
                                    'file_id': entry.get('file_id'),
                                    'registry_dir_id': registry_dir_id,
                                    'filesystem_dir_id': filesystem_dir_id
                                },
                                can_auto_fix=True  # Can update registry
                            ))
                    except Exception:
                        pass  # Corrupt .dir_id - different issue
            
            # Check file_id match (if in filename)
            registry_file_id = entry.get('file_id')
            if registry_file_id:
                filename = file_path.name
                if '_' in filename:
                    prefix = filename.split('_')[0]
                    if prefix.isdigit() and len(prefix) == 20:
                        if prefix != registry_file_id:
                            issues.append(ReconciliationIssue(
                                issue_type='ID_MISMATCH',
                                severity='ERROR',
                                defect_code='ID-MISMATCH-003',
                                path=relative_path,
                                details={
                                    'registry_file_id': registry_file_id,
                                    'filename_file_id': prefix
                                },
                                can_auto_fix=False  # Requires manual review
                            ))
        
        return issues
    
    def _check_duplicate_file_ids(self) -> List[ReconciliationIssue]:
        """Check for duplicate file_ids in registry."""
        issues = []
        
        file_id_to_paths = defaultdict(list)
        
        for entry in self.registry.get('files', []):
            file_id = entry.get('file_id')
            relative_path = entry.get('relative_path', '')
            
            if file_id and relative_path:
                file_id_to_paths[file_id].append(relative_path)
        
        # Find duplicates
        for file_id, paths in file_id_to_paths.items():
            if len(paths) > 1:
                issues.append(ReconciliationIssue(
                    issue_type='DUPLICATE_FILE_ID',
                    severity='ERROR',
                    defect_code='DUPLICATE-FILE-ID-004',
                    path=', '.join(paths),
                    details={
                        'file_id': file_id,
                        'paths': paths,
                        'count': len(paths)
                    },
                    can_auto_fix=False  # Requires manual resolution
                ))
        
        return issues
    
    def _check_duplicate_paths(self) -> List[ReconciliationIssue]:
        """Check for duplicate paths in registry."""
        issues = []
        
        path_to_file_ids = defaultdict(list)
        
        for entry in self.registry.get('files', []):
            relative_path = entry.get('relative_path', '')
            file_id = entry.get('file_id')
            
            if relative_path and file_id:
                path_to_file_ids[relative_path].append(file_id)
        
        # Find duplicates
        for path, file_ids in path_to_file_ids.items():
            if len(file_ids) > 1:
                issues.append(ReconciliationIssue(
                    issue_type='DUPLICATE_PATH',
                    severity='ERROR',
                    defect_code='DUPLICATE-PATH-005',
                    path=path,
                    details={
                        'file_ids': file_ids,
                        'count': len(file_ids)
                    },
                    can_auto_fix=False  # Requires manual resolution
                ))
        
        return issues
    
    def _compute_stats(self, issues: List[ReconciliationIssue]) -> Dict[str, int]:
        """Compute statistics from issues."""
        stats = {
            'total_issues': len(issues),
            'total_filesystem_files': getattr(self, '_filesystem_count', 0)
        }
        
        # Count by type
        for issue in issues:
            key = f"count_{issue.issue_type.lower()}"
            stats[key] = stats.get(key, 0) + 1
        
        # Count by severity
        for issue in issues:
            key = f"severity_{issue.severity.lower()}"
            stats[key] = stats.get(key, 0) + 1
        
        # Count auto-fixable
        stats['auto_fixable'] = sum(1 for issue in issues if issue.can_auto_fix)
        
        return stats
    
    def _save_evidence(self, result: ReconciliationResult, timestamp: str):
        """Save reconciliation evidence."""
        evidence_file = self.evidence_dir / f"full_reconcile_{timestamp}.json"
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def _apply_auto_fixes(self, issues: List[ReconciliationIssue], timestamp: str):
        """Apply automatic fixes where possible."""
        fixes_applied = []
        
        for issue in issues:
            if not issue.can_auto_fix:
                continue
            
            try:
                if issue.issue_type == 'REGISTRY_ORPHAN':
                    # Remove from registry
                    self._remove_registry_entry(issue.details['registry_index'])
                    fixes_applied.append(issue)
                
                elif issue.issue_type == 'ID_MISMATCH' and 'registry_dir_id' in issue.details:
                    # Update registry dir_id
                    self._update_registry_dir_id(issue.path, issue.details['filesystem_dir_id'])
                    fixes_applied.append(issue)
                
                # DISK_UNREGISTERED would need registration logic - skip for now
                
            except Exception as e:
                # Log fix failure but continue
                pass
        
        # Save fixes evidence
        if fixes_applied:
            fixes_file = self.evidence_dir / f"auto_fixes_{timestamp}.json"
            with open(fixes_file, 'w', encoding='utf-8') as f:
                json.dump([issue.to_dict() for issue in fixes_applied], f, indent=2)
    
    def _remove_registry_entry(self, index: int):
        """Remove entry from registry by index."""
        if 0 <= index < len(self.registry['files']):
            del self.registry['files'][index]
            # Would save registry here in production
    
    def _update_registry_dir_id(self, path: str, new_dir_id: str):
        """Update dir_id in registry for given path."""
        for entry in self.registry['files']:
            if entry.get('relative_path') == path:
                entry['dir_id'] = new_dir_id
                # Would save registry here in production
                break


def reconcile_registry_filesystem(
    project_root: Path,
    registry_path: Path,
    zone: str = "all",
    auto_fix: bool = False
) -> ReconciliationResult:
    """Perform registry ↔ filesystem reconciliation (public API).
    
    Args:
        project_root: Project root directory
        registry_path: Path to registry JSON file
        zone: Zone to reconcile ('all', 'governed', etc.)
        auto_fix: If True, apply automatic fixes
        
    Returns:
        ReconciliationResult: Comprehensive reconciliation report
    """
    reconciler = RegistryFilesystemReconciler(project_root, registry_path)
    return reconciler.reconcile(zone=zone, auto_fix=auto_fix)


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Reconcile registry with filesystem")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--registry", type=Path, required=True, help="Path to registry JSON")
    parser.add_argument("--zone", default="all", help="Zone to reconcile")
    parser.add_argument("--auto-fix", action="store_true", help="Apply automatic fixes")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    
    args = parser.parse_args()
    
    result = reconcile_registry_filesystem(
        args.project_root,
        args.registry,
        args.zone,
        args.auto_fix
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Reconciliation complete:")
        print(f"  Total issues: {len(result.issues)}")
        print(f"  Errors: {result.stats.get('severity_error', 0)}")
        print(f"  Warnings: {result.stats.get('severity_warning', 0)}")
        print(f"  Auto-fixable: {result.stats.get('auto_fixable', 0)}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
