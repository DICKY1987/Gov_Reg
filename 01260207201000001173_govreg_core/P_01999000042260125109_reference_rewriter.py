"""Reference rewriter after ID-based renames (GAP-004).

FILE_ID: 01999000042260125109
PURPOSE: Rewrite references in markdown, JSON, YAML, Python after path renames
PHASE: Phase 2 - Reference Management
BACKLOG: 01999000042260125103 GAP-004
"""
from __future__ import annotations

import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@dataclass
class ChangeRecord:
    """Record of a reference rewrite change."""
    file_path: str
    line_number: int
    old_text: str
    new_text: str
    pattern_type: str


@dataclass
class ReferenceRewriteReport:
    """Report from reference rewrite operation."""
    rewrite_id: str
    timestamp: str
    files_scanned: int
    references_found: int
    references_rewritten: int
    changes: List[ChangeRecord]
    evidence_path: Path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        result = asdict(self)
        result['evidence_path'] = str(result['evidence_path'])
        return result


class ReferenceRewriter:
    """Rewrite references after ID-based renames."""
    
    # Rewrite patterns for different file types
    PATTERNS = {
        'markdown': [
            (r'\[([^\]]+)\]\(([^)]+)\)', 2),  # [text](path)
            (r'!\[([^\]]+)\]\(([^)]+)\)', 2),  # ![alt](path)
        ],
        'json': [
            (r'"(?:path|file|relative_path|source|target|module_path)"\s*:\s*"([^"]+)"', 1),
        ],
        'yaml': [
            (r'(?:path|file|relative_path|source|target|module_path):\s*([^\n]+)', 1),
        ],
        'python': [
            (r'from\s+([\w.]+)\s+import', 1),
            (r'import\s+([\w.]+)', 1),
        ]
    }
    
    def __init__(
        self,
        project_root: Path,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize rewriter.
        
        Args:
            project_root: Project root directory
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "reference_rewrites"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def rewrite_references_after_rename(
        self,
        old_path: str,
        new_path: str,
        scope: Optional[List[Path]] = None,
        dry_run: bool = False
    ) -> ReferenceRewriteReport:
        """Rewrite references after a rename operation.
        
        Args:
            old_path: Original file/directory path (relative to project root)
            new_path: New file/directory path after ID-rename
            scope: Files to scan and rewrite (default: entire project)
            dry_run: If True, report changes without applying
            
        Returns:
            ReferenceRewriteReport: Outcome of rewrite operation
        """
        rewrite_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Determine scope
        if scope is None:
            scope = self._get_default_scope()
        
        changes: List[ChangeRecord] = []
        files_scanned = 0
        references_found = 0
        
        # Scan files
        for file_path in scope:
            if not file_path.is_file():
                continue
            
            files_scanned += 1
            file_changes = self._rewrite_file(file_path, old_path, new_path, dry_run)
            changes.extend(file_changes)
            references_found += len(file_changes)
        
        # Save evidence
        evidence_path = self._save_evidence(
            rewrite_id,
            timestamp,
            files_scanned,
            references_found,
            len(changes),
            changes
        )
        
        return ReferenceRewriteReport(
            rewrite_id=rewrite_id,
            timestamp=timestamp,
            files_scanned=files_scanned,
            references_found=references_found,
            references_rewritten=len(changes) if not dry_run else 0,
            changes=changes,
            evidence_path=evidence_path
        )
    
    def _get_default_scope(self) -> List[Path]:
        """Get default scope (all relevant files in project)."""
        extensions = ['.md', '.json', '.yaml', '.yml', '.py']
        files = []
        
        for ext in extensions:
            files.extend(self.project_root.rglob(f"*{ext}"))
        
        # Filter out excluded paths
        excluded_patterns = ['.git', '__pycache__', 'node_modules', '.state', '.quarantine']
        return [
            f for f in files
            if not any(pattern in f.parts for pattern in excluded_patterns)
        ]
    
    def _rewrite_file(
        self,
        file_path: Path,
        old_path: str,
        new_path: str,
        dry_run: bool
    ) -> List[ChangeRecord]:
        """Rewrite references in a single file."""
        changes = []
        
        # Determine file type
        file_type = self._get_file_type(file_path)
        if not file_type:
            return changes
        
        try:
            # Read file
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            new_lines = lines.copy()
            
            # Get patterns for this file type
            patterns = self.PATTERNS.get(file_type, [])
            
            for pattern, group_idx in patterns:
                for line_num, line in enumerate(lines):
                    matches = list(re.finditer(pattern, line))
                    for match in matches:
                        matched_path = match.group(group_idx)
                        
                        # Check if this matches old_path
                        if self._path_matches(matched_path, old_path):
                            # Replace
                            new_text = line.replace(matched_path, new_path)
                            
                            changes.append(ChangeRecord(
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_num + 1,
                                old_text=line,
                                new_text=new_text,
                                pattern_type=file_type
                            ))
                            
                            new_lines[line_num] = new_text
            
            # Write back if not dry run
            if changes and not dry_run:
                file_path.write_text('\n'.join(new_lines), encoding='utf-8')
        
        except Exception as e:
            # Skip files that can't be processed
            pass
        
        return changes
    
    def _get_file_type(self, file_path: Path) -> Optional[str]:
        """Determine file type from extension."""
        suffix = file_path.suffix.lower()
        
        if suffix == '.md':
            return 'markdown'
        elif suffix == '.json':
            return 'json'
        elif suffix in ['.yaml', '.yml']:
            return 'yaml'
        elif suffix == '.py':
            return 'python'
        else:
            return None
    
    def _path_matches(self, matched_path: str, target_path: str) -> bool:
        """Check if matched path corresponds to target path."""
        # Normalize paths
        matched_norm = Path(matched_path).as_posix()
        target_norm = Path(target_path).as_posix()
        
        # Check exact match or substring match
        return matched_norm == target_norm or target_norm in matched_norm or matched_norm in target_norm
    
    def _save_evidence(
        self,
        rewrite_id: str,
        timestamp: str,
        files_scanned: int,
        references_found: int,
        references_rewritten: int,
        changes: List[ChangeRecord]
    ) -> Path:
        """Save rewrite evidence."""
        evidence_file = self.evidence_dir / f"{rewrite_id}_rewrite.json"
        
        evidence = {
            "rewrite_id": rewrite_id,
            "timestamp": timestamp,
            "files_scanned": files_scanned,
            "references_found": references_found,
            "references_rewritten": references_rewritten,
            "changes": [asdict(c) for c in changes]
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_file


def rewrite_references_after_rename(
    old_path: str,
    new_path: str,
    scope: Optional[List[Path]] = None,
    dry_run: bool = False,
    project_root: Optional[Path] = None
) -> ReferenceRewriteReport:
    """Rewrite references after rename (public API).
    
    Args:
        old_path: Original file/directory path (relative to project root)
        new_path: New file/directory path after ID-rename
        scope: Files to scan and rewrite (default: entire project)
        dry_run: If True, report changes without applying
        project_root: Optional project root (auto-detected if None)
        
    Returns:
        ReferenceRewriteReport: Outcome of rewrite operation
    """
    if project_root is None:
        # Auto-detect project root
        project_root = Path.cwd()
        while project_root.parent != project_root:
            if (project_root / ".git").exists():
                break
            project_root = project_root.parent
    
    rewriter = ReferenceRewriter(project_root)
    return rewriter.rewrite_references_after_rename(old_path, new_path, scope, dry_run)
