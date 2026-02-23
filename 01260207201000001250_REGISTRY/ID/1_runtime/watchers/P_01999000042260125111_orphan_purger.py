"""Orphan and dead-entry cleanup (GAP-006).

FILE_ID: 01999000042260125111
PURPOSE: Detect and purge orphaned .dir_id files and dead registry entries
PHASE: Phase 2 - Cleanup Operations
BACKLOG: 01999000042260125103 GAP-006
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000069_dir_id_handler import DirIdManager
from P_01260207233100000068_zone_classifier import ZoneClassifier


@dataclass
class OrphanPurgeReport:
    """Report from orphan purge operation."""
    purge_id: str
    timestamp: str
    orphans_detected: int
    orphans_quarantined: int
    orphans_purged: int
    orphan_types: Dict[str, int]
    quarantine_dir: Path
    registry_patch: Optional[Path]
    evidence_path: Path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        result = asdict(self)
        result['quarantine_dir'] = str(result['quarantine_dir'])
        result['registry_patch'] = str(result['registry_patch']) if result['registry_patch'] else None
        result['evidence_path'] = str(result['evidence_path'])
        return result


class OrphanPurger:
    """Detect and purge orphaned .dir_id files and dead registry entries."""
    
    def __init__(
        self,
        project_root: Path,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize purger.
        
        Args:
            project_root: Project root directory
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.dir_id_manager = DirIdManager()
        self.zone_classifier = ZoneClassifier()
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "orphan_purges"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def purge_orphans(
        self,
        registry_path: Path,
        quarantine: bool = True,
        dry_run: bool = False
    ) -> OrphanPurgeReport:
        """Detect and purge orphans.
        
        Args:
            registry_path: Path to governance registry
            quarantine: If True, quarantine orphans before deletion
            dry_run: If True, report orphans without purging
            
        Returns:
            OrphanPurgeReport: Purge outcome
        """
        purge_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        orphan_types = defaultdict(int)
        orphans_detected = 0
        orphans_quarantined = 0
        orphans_purged = 0
        
        # Setup quarantine directory
        quarantine_dir = self.project_root / ".quarantine" / "orphans" / purge_id
        if quarantine and not dry_run:
            quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect orphaned .dir_id in excluded zones
        dir_id_excluded = self._detect_dir_id_in_excluded_zone()
        orphan_types['dir_id_in_excluded_zone'] = len(dir_id_excluded)
        orphans_detected += len(dir_id_excluded)
        
        if not dry_run and dir_id_excluded:
            orphans_quarantined += self._quarantine_dir_ids(dir_id_excluded, quarantine_dir)
            orphans_purged += len(dir_id_excluded)
        
        # Detect registry entries with missing disk files
        registry_missing = self._detect_registry_entry_missing_disk_file(registry_path)
        orphan_types['registry_entry_missing_disk_file'] = len(registry_missing)
        orphans_detected += len(registry_missing)
        
        # Detect disk files in excluded zones but still registered
        registry_excluded = self._detect_disk_file_excluded_but_registered(registry_path)
        orphan_types['disk_file_excluded_but_registered'] = len(registry_excluded)
        orphans_detected += len(registry_excluded)
        
        # Detect .dir_id with no parent directory
        dir_id_no_parent = self._detect_dir_id_no_parent()
        orphan_types['dir_id_no_parent'] = len(dir_id_no_parent)
        orphans_detected += len(dir_id_no_parent)
        
        if not dry_run and dir_id_no_parent:
            orphans_quarantined += self._quarantine_dir_ids(dir_id_no_parent, quarantine_dir)
            orphans_purged += len(dir_id_no_parent)
        
        # Patch registry
        registry_patch_path = None
        if not dry_run and (registry_missing or registry_excluded):
            registry_patch_path = self._patch_registry(
                registry_path,
                registry_missing + registry_excluded,
                purge_id
            )
            orphans_purged += len(registry_missing) + len(registry_excluded)
        
        # Save evidence
        evidence_path = self._save_evidence(
            purge_id,
            timestamp,
            orphans_detected,
            orphans_quarantined,
            orphans_purged,
            orphan_types,
            quarantine_dir,
            registry_patch_path
        )
        
        return OrphanPurgeReport(
            purge_id=purge_id,
            timestamp=timestamp,
            orphans_detected=orphans_detected,
            orphans_quarantined=orphans_quarantined,
            orphans_purged=orphans_purged,
            orphan_types=dict(orphan_types),
            quarantine_dir=quarantine_dir,
            registry_patch=registry_patch_path,
            evidence_path=evidence_path
        )
    
    def _detect_dir_id_in_excluded_zone(self) -> List[Path]:
        """Detect .dir_id files in excluded zones."""
        orphans = []
        for dir_id_path in self.project_root.rglob(".dir_id"):
            parent_dir = dir_id_path.parent
            zone = self.zone_classifier.compute_zone(parent_dir)
            if zone == 'excluded':
                orphans.append(parent_dir)
        return orphans
    
    def _detect_registry_entry_missing_disk_file(self, registry_path: Path) -> List[str]:
        """Detect registry entries without disk files."""
        # Load registry
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        missing = []
        for entry in registry.get('files', []):
            relative_path = entry.get('relative_path', '')
            if relative_path:
                file_path = self.project_root / relative_path
                if not file_path.exists():
                    missing.append(relative_path)
        
        return missing
    
    def _detect_disk_file_excluded_but_registered(self, registry_path: Path) -> List[str]:
        """Detect registry entries for excluded files."""
        # Load registry
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        excluded_but_registered = []
        for entry in registry.get('files', []):
            relative_path = entry.get('relative_path', '')
            if relative_path:
                file_path = self.project_root / relative_path
                if file_path.exists():
                    zone = self.zone_classifier.compute_zone(file_path.parent)
                    if zone == 'excluded':
                        excluded_but_registered.append(relative_path)
        
        return excluded_but_registered
    
    def _detect_dir_id_no_parent(self) -> List[Path]:
        """Detect .dir_id files with deleted parent directories."""
        orphans = []
        for dir_id_path in self.project_root.rglob(".dir_id"):
            parent_dir = dir_id_path.parent
            # Check if parent's parent exists and has .dir_id
            if parent_dir.parent.exists():
                grandparent_dir_id = parent_dir.parent / ".dir_id"
                if not grandparent_dir_id.exists():
                    # Parent directory may be orphaned
                    orphans.append(parent_dir)
        return orphans
    
    def _quarantine_dir_ids(self, directories: List[Path], quarantine_dir: Path) -> int:
        """Quarantine .dir_id files."""
        quarantined = 0
        for directory in directories:
            dir_id_path = directory / ".dir_id"
            if dir_id_path.exists():
                # Create safe name
                relative_path = directory.relative_to(self.project_root)
                safe_name = str(relative_path).replace("/", "_").replace("\\", "_")
                quarantine_path = quarantine_dir / f"{safe_name}.dir_id"
                
                # Move to quarantine
                shutil.move(str(dir_id_path), str(quarantine_path))
                quarantined += 1
        
        return quarantined
    
    def _patch_registry(
        self,
        registry_path: Path,
        paths_to_remove: List[str],
        purge_id: str
    ) -> Path:
        """Patch registry to remove dead entries."""
        # Load registry
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        # Remove entries
        original_count = len(registry.get('files', []))
        registry['files'] = [
            entry for entry in registry.get('files', [])
            if entry.get('relative_path') not in paths_to_remove
        ]
        new_count = len(registry['files'])
        
        # Save patch
        patch_path = self.evidence_dir / f"{purge_id}_registry_patch.json"
        patch = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_count": original_count,
            "new_count": new_count,
            "removed_paths": paths_to_remove
        }
        
        with open(patch_path, 'w', encoding='utf-8') as f:
            json.dump(patch, f, indent=2)
        
        # Write back registry
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
        
        return patch_path
    
    def _save_evidence(
        self,
        purge_id: str,
        timestamp: str,
        orphans_detected: int,
        orphans_quarantined: int,
        orphans_purged: int,
        orphan_types: Dict[str, int],
        quarantine_dir: Path,
        registry_patch: Optional[Path]
    ) -> Path:
        """Save purge evidence."""
        evidence_file = self.evidence_dir / f"{purge_id}_purge.json"
        
        evidence = {
            "purge_id": purge_id,
            "timestamp": timestamp,
            "orphans_detected": orphans_detected,
            "orphans_quarantined": orphans_quarantined,
            "orphans_purged": orphans_purged,
            "orphan_types": orphan_types,
            "quarantine_dir": str(quarantine_dir),
            "registry_patch": str(registry_patch) if registry_patch else None
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_file


def purge_orphans(
    registry_path: Path,
    project_root: Path,
    quarantine: bool = True,
    dry_run: bool = False
) -> OrphanPurgeReport:
    """Purge orphans (public API).
    
    Args:
        registry_path: Path to governance registry
        project_root: Project root directory
        quarantine: If True, quarantine orphans before deletion
        dry_run: If True, report orphans without purging
        
    Returns:
        OrphanPurgeReport: Purge outcome
    """
    purger = OrphanPurger(project_root)
    return purger.purge_orphans(registry_path, quarantine, dry_run)
