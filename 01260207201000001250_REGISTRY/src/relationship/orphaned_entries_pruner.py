"""
orphaned_entries_pruner.py

Orphaned entries cleanup: Resolve or prune 243/245 orphaned entries.

Issue: FCA-013 (Critical)
Symptom: 243 out of 245 entries are orphaned (no parent relationship)
Root Cause: Relationship generation incomplete; empty edges[] not validated
Fix: Build parent-child relationships or mark as intentionally root-level

Contract: pass_fail_criteria_contract + mutation_safety_contract
Category: Gate + Mutation
Runner: Must validate relationship completeness before registry promotion
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class OrphanedEntriesPruner:
    """
    Resolve orphaned entries by building relationships or pruning invalid entries.
    
    Strategy:
    1. Identify orphaned entries (no incoming edges)
    2. Attempt to build relationships from file paths, imports, includes
    3. Mark legitimate root-level entries
    4. Prune truly orphaned/invalid entries
    5. Validate relationship graph completeness
    """
    
    def __init__(
        self,
        strict_mode: bool = True,
        allow_pruning: bool = False,
        evidence_dir: Optional[Path] = None
    ):
        """
        Initialize orphaned entries pruner.
        
        Args:
            strict_mode: If True, fail on unresolvable orphans
            allow_pruning: If True, allow deletion of orphaned entries
            evidence_dir: Directory for evidence artifacts
        """
        self.strict_mode = strict_mode
        self.allow_pruning = allow_pruning
        self.evidence_dir = evidence_dir or Path(".state/evidence/phase2")
        self.stats = {
            "entries_processed": 0,
            "orphans_found": 0,
            "relationships_built": 0,
            "marked_as_root": 0,
            "pruned": 0,
            "errors": 0
        }
    
    def analyze_orphans(self, entries: List[Dict]) -> Dict:
        """
        Analyze entries to identify orphans.
        
        Args:
            entries: List of registry entries with edges
        
        Returns:
            Analysis report with orphan statistics
        """
        entry_ids = {e.get("entry_id") for e in entries if "entry_id" in e}
        orphans = []
        roots = []
        connected = []
        
        for entry in entries:
            self.stats["entries_processed"] += 1
            entry_id = entry.get("entry_id")
            edges = entry.get("edges", [])
            
            # An entry has a parent if it has any outgoing edge pointing to another
            # known entry (child→parent convention). The original incoming-only check
            # failed when children store their parent reference in their own edge list
            # (e.g. {"source": child_id, "target": parent_id, "relationship": "child_of"}).
            has_parent = any(
                edge.get("target") in entry_ids and edge.get("target") != entry_id
                for edge in edges
            )
            
            if not has_parent:
                # Check if it's a legitimate root
                if self._is_legitimate_root(entry):
                    roots.append(entry_id)
                else:
                    orphans.append(entry_id)
                    self.stats["orphans_found"] += 1
            else:
                connected.append(entry_id)
        
        return {
            "total_entries": len(entries),
            "orphaned": len(orphans),
            "root_level": len(roots),
            "connected": len(connected),
            "orphan_rate": f"{(len(orphans) / len(entries) * 100):.1f}%" if entries else "0%",
            "orphan_ids": orphans,
            "root_ids": roots
        }
    
    def _is_legitimate_root(self, entry: Dict) -> bool:
        """
        Determine if an entry is a legitimate root-level entry.
        
        Root-level entries include:
        - Repository root directories
        - Top-level configuration files
        - Entry points (main.py, index.js, etc.)
        - README files
        """
        file_path = entry.get("file_path", "")
        file_name = Path(file_path).name if file_path else ""
        
        # Check for root indicators
        root_indicators = [
            ".git",
            "README",
            "LICENSE",
            "setup.py",
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "__init__.py",
            "index.js",
            "main.py",
            "main.go"
        ]
        
        return any(indicator.lower() in file_name.lower() for indicator in root_indicators)
    
    def build_relationships(self, entries: List[Dict]) -> List[Dict]:
        """
        Build parent-child relationships for orphaned entries.
        
        Args:
            entries: List of registry entries
        
        Returns:
            Updated entries with new relationships
        """
        updated_entries = []
        
        for entry in entries:
            updated_entry = entry.copy()
            
            # Skip if already has relationships
            if updated_entry.get("edges") and len(updated_entry["edges"]) > 0:
                updated_entries.append(updated_entry)
                continue
            
            # Try to build relationships
            new_edges = self._infer_relationships(updated_entry, entries)
            
            if new_edges:
                if "edges" not in updated_entry:
                    updated_entry["edges"] = []
                updated_entry["edges"].extend(new_edges)
                self.stats["relationships_built"] += len(new_edges)
                logger.info(f"Built {len(new_edges)} relationships for {updated_entry.get('entry_id')}")
            elif self._is_legitimate_root(updated_entry):
                # Mark as intentional root
                updated_entry["is_root"] = True
                self.stats["marked_as_root"] += 1
                logger.info(f"Marked as root: {updated_entry.get('entry_id')}")
            
            updated_entries.append(updated_entry)
        
        return updated_entries
    
    def _infer_relationships(self, entry: Dict, all_entries: List[Dict]) -> List[Dict]:
        """
        Infer relationships from file paths, imports, and context.
        
        Returns:
            List of new edge objects
        """
        new_edges = []
        file_path = entry.get("file_path", "")
        
        if not file_path:
            return new_edges
        
        path = Path(file_path)
        
        # Strategy 1: Parent directory relationship
        parent_entry = self._find_parent_directory(path, all_entries)
        if parent_entry:
            new_edges.append({
                "source": entry.get("entry_id"),
                "target": parent_entry.get("entry_id"),
                "relationship": "child_of",
                "inferred": True
            })
        
        # Strategy 2: Import relationships (for Python files)
        if path.suffix == ".py":
            import_edges = self._infer_python_imports(entry, all_entries)
            new_edges.extend(import_edges)
        
        return new_edges
    
    def _find_parent_directory(self, file_path: Path, all_entries: List[Dict]) -> Optional[Dict]:
        """Find the parent directory entry."""
        parent_path = file_path.parent
        
        for entry in all_entries:
            entry_path = entry.get("file_path", "")
            if entry_path and Path(entry_path) == parent_path:
                return entry
        
        return None
    
    def _infer_python_imports(self, entry: Dict, all_entries: List[Dict]) -> List[Dict]:
        """Infer relationships from Python import statements (stub)."""
        # TODO: Parse Python file and extract imports
        # For now, return empty list
        return []
    
    def prune_orphans(self, entries: List[Dict], orphan_ids: List[str]) -> List[Dict]:
        """
        Remove orphaned entries that cannot be resolved.
        
        Args:
            entries: List of all entries
            orphan_ids: List of orphaned entry IDs to prune
        
        Returns:
            Pruned list of entries
        """
        if not self.allow_pruning:
            logger.warning("Pruning disabled, skipping")
            return entries
        
        pruned_entries = [
            entry for entry in entries
            if entry.get("entry_id") not in orphan_ids
        ]
        
        self.stats["pruned"] = len(entries) - len(pruned_entries)
        logger.info(f"Pruned {self.stats['pruned']} orphaned entries")
        
        return pruned_entries
    
    def validate_relationships(self, entries: List[Dict]) -> Tuple[bool, Dict]:
        """
        Validate relationship graph completeness.
        
        Returns:
            (is_valid, validation_report)
        """
        analysis = self.analyze_orphans(entries)
        
        # Pass criteria: orphan rate < 10% (down from 99.2%)
        is_valid = float(analysis["orphan_rate"].rstrip("%")) < 10.0
        
        validation_report = {
            "is_valid": is_valid,
            "analysis": analysis,
            "threshold": "10%",
            "recommendation": "PASS" if is_valid else "FAIL - too many orphans"
        }
        
        return (is_valid, validation_report)
    
    def create_evidence(self, output_path: Path, analysis: Dict):
        """Generate evidence report for orphan resolution."""
        evidence = {
            "component": "orphaned_entries_pruner",
            "contracts": ["pass_fail_criteria_contract", "mutation_safety_contract"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "configuration": {
                "strict_mode": self.strict_mode,
                "allow_pruning": self.allow_pruning
            },
            "statistics": self.get_stats(),
            "orphan_analysis": analysis
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        logger.info(f"Evidence written to {output_path}")
    
    def get_stats(self) -> Dict:
        """Get pruning statistics."""
        return self.stats.copy()
