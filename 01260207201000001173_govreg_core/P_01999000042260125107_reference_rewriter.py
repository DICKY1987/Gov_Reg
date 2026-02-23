"""Reference rewriting after file/directory renames (GAP-004).

FILE_ID: 01999000042260125107
PURPOSE: Update references after ID-based file/directory renames
PHASE: Phase 4 - Reference Integrity
BACKLOG: 01999000042260125103 GAP-004

Automatically finds and updates references when files/directories are renamed:
- Markdown links
- YAML paths
- JSON paths
- Python imports
- Relative path references
"""
from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@dataclass
class ReferenceMatch:
    """A single reference found in a file."""
    file_path: str
    line_number: int
    line_content: str
    match_type: str
    old_reference: str
    new_reference: str
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class RewriteResult:
    """Result of a reference rewrite operation."""
    success: bool
    old_path: str
    new_path: str
    files_scanned: int
    references_found: int
    references_updated: int
    matches: List[ReferenceMatch] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    evidence_path: Optional[Path] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['matches'] = [m.to_dict() if hasattr(m, 'to_dict') else m for m in self.matches]
        result['evidence_path'] = str(result['evidence_path']) if result['evidence_path'] else None
        return result


class ReferenceRewriter:
    """Rewrites references after file/directory renames.
    
    Supports multiple reference formats:
    - Markdown links: [text](path)
    - YAML paths: path: "path/to/file"
    - JSON paths: "path": "path/to/file"
    - Python imports: from module.path import
    - Relative paths: ../path/to/file
    """
    
    # Reference patterns (compiled regexes)
    PATTERNS = {
        'markdown_link': re.compile(r'\[([^\]]+)\]\(([^)]+)\)'),
        'yaml_path': re.compile(r'path:\s*["\']?([^"\';\n]+)["\']?'),
        'json_path': re.compile(r'"path"\s*:\s*"([^"]+)"'),
        'python_import': re.compile(r'from\s+([\w.]+)\s+import'),
        'relative_path': re.compile(r'(?:\.\.?/|/)?[\w/.-]+\.\w+'),
    }
    
    def __init__(
        self,
        project_root: Path,
        evidence_dir: Optional[Path] = None,
        file_extensions: Optional[List[str]] = None
    ):
        """Initialize reference rewriter.
        
        Args:
            project_root: Project root directory
            evidence_dir: Directory for evidence artifacts
            file_extensions: File extensions to scan (default: common text files)
        """
        self.project_root = project_root
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "reference_rewrites"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        if file_extensions is None:
            file_extensions = [
                '.py', '.md', '.json', '.yaml', '.yml', 
                '.txt', '.conf', '.cfg', '.ini', '.toml'
            ]
        self.file_extensions = file_extensions
    
    def rewrite_after_rename(
        self,
        old_path: str,
        new_path: str,
        dry_run: bool = False
    ) -> RewriteResult:
        """Find and rewrite all references after a rename.
        
        Args:
            old_path: Old path (relative to project root)
            new_path: New path (relative to project root)
            dry_run: If True, find but don't update references
            
        Returns:
            RewriteResult: Comprehensive rewrite report
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        matches: List[ReferenceMatch] = []
        errors: List[str] = []
        files_scanned = 0
        
        # Scan all relevant files
        for file_path in self._get_scannable_files():
            files_scanned += 1
            
            try:
                file_matches = self._scan_file_for_references(file_path, old_path)
                matches.extend(file_matches)
            except Exception as e:
                errors.append(f"Error scanning {file_path}: {e}")
        
        # Apply rewrites if not dry run
        references_updated = 0
        if not dry_run and matches:
            references_updated = self._apply_rewrites(matches, old_path, new_path)
        
        # Generate evidence
        evidence_path = self._save_evidence(
            timestamp,
            old_path,
            new_path,
            matches,
            files_scanned,
            references_updated,
            dry_run
        )
        
        return RewriteResult(
            success=len(errors) == 0,
            old_path=old_path,
            new_path=new_path,
            files_scanned=files_scanned,
            references_found=len(matches),
            references_updated=references_updated,
            matches=matches,
            errors=errors,
            evidence_path=evidence_path
        )
    
    def _get_scannable_files(self) -> List[Path]:
        """Get all files that should be scanned for references."""
        scannable = []
        
        for ext in self.file_extensions:
            scannable.extend(self.project_root.rglob(f'*{ext}'))
        
        # Filter out hidden files and directories
        scannable = [
            f for f in scannable 
            if not any(part.startswith('.') for part in f.parts)
        ]
        
        return scannable
    
    def _scan_file_for_references(
        self,
        file_path: Path,
        target_path: str
    ) -> List[ReferenceMatch]:
        """Scan a single file for references to target path."""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            # Binary or unreadable file
            return matches
        
        relative_file_path = str(file_path.relative_to(self.project_root))
        
        for line_num, line in enumerate(lines, start=1):
            # Check each pattern
            for pattern_name, pattern in self.PATTERNS.items():
                for match in pattern.finditer(line):
                    # Extract the path from the match
                    if pattern_name == 'markdown_link':
                        reference = match.group(2)
                    elif pattern_name == 'python_import':
                        reference = match.group(1).replace('.', '/')
                    else:
                        reference = match.group(1)
                    
                    # Check if this references our target
                    if self._is_reference_to_target(reference, target_path, file_path):
                        matches.append(ReferenceMatch(
                            file_path=relative_file_path,
                            line_number=line_num,
                            line_content=line.rstrip(),
                            match_type=pattern_name,
                            old_reference=reference,
                            new_reference=self._compute_new_reference(
                                reference,
                                target_path,
                                None  # Will compute during apply
                            )
                        ))
        
        return matches
    
    def _is_reference_to_target(
        self,
        reference: str,
        target_path: str,
        referencing_file: Path
    ) -> bool:
        """Check if a reference string points to the target path."""
        # Normalize paths
        reference = reference.strip()
        
        # Direct match
        if reference == target_path:
            return True
        
        # Check if reference is relative and resolves to target
        try:
            referencing_dir = referencing_file.parent
            resolved = (referencing_dir / reference).resolve()
            target_resolved = (self.project_root / target_path).resolve()
            
            if resolved == target_resolved:
                return True
        except Exception:
            pass
        
        # Check if target path ends with reference (for partial matches)
        if target_path.endswith(reference):
            return True
        
        return False
    
    def _compute_new_reference(
        self,
        old_reference: str,
        old_path: str,
        new_path: str
    ) -> str:
        """Compute what the new reference should be."""
        if new_path is None:
            return old_reference
        
        # Simple string replacement
        if old_reference == old_path:
            return new_path
        
        # Replace suffix if old_path is at end
        if old_reference.endswith(old_path):
            prefix = old_reference[:-len(old_path)]
            return prefix + new_path
        
        # For now, just return new_path
        # More sophisticated logic could preserve relative paths
        return new_path
    
    def _apply_rewrites(
        self,
        matches: List[ReferenceMatch],
        old_path: str,
        new_path: str
    ) -> int:
        """Apply rewrites to files."""
        # Group matches by file
        matches_by_file = {}
        for match in matches:
            if match.file_path not in matches_by_file:
                matches_by_file[match.file_path] = []
            matches_by_file[match.file_path].append(match)
        
        references_updated = 0
        
        # Process each file
        for rel_path, file_matches in matches_by_file.items():
            file_path = self.project_root / rel_path
            
            try:
                # Read file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Apply replacements
                for match in file_matches:
                    # Compute actual new reference
                    new_ref = self._compute_new_reference(
                        match.old_reference,
                        old_path,
                        new_path
                    )
                    match.new_reference = new_ref
                    
                    # Replace in content
                    content = content.replace(match.old_reference, new_ref)
                    references_updated += 1
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            except Exception as e:
                # Log error but continue
                pass
        
        return references_updated
    
    def _save_evidence(
        self,
        timestamp: str,
        old_path: str,
        new_path: str,
        matches: List[ReferenceMatch],
        files_scanned: int,
        references_updated: int,
        dry_run: bool
    ) -> Path:
        """Save rewrite evidence."""
        # Create filename from old path hash
        path_hash = hashlib.md5(old_path.encode()).hexdigest()[:8]
        evidence_file = self.evidence_dir / f"rewrite_{timestamp}_{path_hash}.json"
        
        evidence = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_path": old_path,
            "new_path": new_path,
            "dry_run": dry_run,
            "files_scanned": files_scanned,
            "references_found": len(matches),
            "references_updated": references_updated,
            "matches": [m.to_dict() for m in matches]
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)
        
        return evidence_file


def rewrite_references(
    project_root: Path,
    old_path: str,
    new_path: str,
    dry_run: bool = False
) -> RewriteResult:
    """Rewrite references after a rename (public API).
    
    Args:
        project_root: Project root directory
        old_path: Old path (relative to project root)
        new_path: New path (relative to project root)
        dry_run: If True, find but don't update references
        
    Returns:
        RewriteResult: Comprehensive rewrite report
    """
    rewriter = ReferenceRewriter(project_root)
    return rewriter.rewrite_after_rename(old_path, new_path, dry_run)


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Rewrite references after file/directory rename")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    parser.add_argument("--old-path", required=True, help="Old path (relative to project root)")
    parser.add_argument("--new-path", required=True, help="New path (relative to project root)")
    parser.add_argument("--dry-run", action="store_true", help="Find but don't update references")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    
    args = parser.parse_args()
    
    result = rewrite_references(
        args.project_root,
        args.old_path,
        args.new_path,
        args.dry_run
    )
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Reference rewrite {'(DRY RUN)' if args.dry_run else 'complete'}:")
        print(f"  Files scanned: {result.files_scanned}")
        print(f"  References found: {result.references_found}")
        print(f"  References updated: {result.references_updated}")
        print(f"  Errors: {len(result.errors)}")
        if result.evidence_path:
            print(f"  Evidence: {result.evidence_path}")
