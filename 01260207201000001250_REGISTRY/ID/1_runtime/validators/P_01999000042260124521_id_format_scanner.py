#!/usr/bin/env python3
"""ID Format Scanner - Identify files with missing or incorrect file ID format.

FILE_ID: 01999000042260124521
DOC_ID: P_01999000042260124521

This scanner identifies files that:
1. Have no ID prefix at all
2. Have incorrect ID format (wrong length, malformed)
3. Have old DOC- prefix format that needs conversion
4. Python files without P_ prefix
5. Files with mismatched ID formats

Standard ID formats:
- Regular files: {20-digit-ID}_{filename}
- Python files: P_{20-digit-ID}_{filename}
- Acceptable legacy: {17-19-digit-ID}_{filename} (to be migrated)
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime, timezone


class IDFormatScanner:
    """Scanner for identifying files with missing or incorrect ID formats."""
    
    # ID format patterns
    PATTERN_PYTHON_20 = re.compile(r'^P_\d{20}_')  # P_{20-digit}_{name}
    PATTERN_REGULAR_20 = re.compile(r'^\d{20}_')   # {20-digit}_{name}
    PATTERN_LEGACY = re.compile(r'^\d{17,19}_')    # {17-19-digit}_{name} (legacy)
    PATTERN_DOC_PREFIX = re.compile(r'^DOC-')      # DOC-* (old format)
    PATTERN_DOC_WITH_ID = re.compile(r'^DOC-[A-Z-]+-(\d{19,20})__')  # DOC-*-{ID}__*
    
    # Directories to exclude from scanning
    EXCLUDED_DIRS = {
        '.git', '__pycache__', '.pytest_cache', 'htmlcov', '.venv', 
        'venv', 'node_modules', 'dist', 'build', '.mypy_cache',
        '.tox', '.eggs', '*.egg-info', '.coverage'
    }
    
    # Files to exclude from scanning
    EXCLUDED_FILES = {
        '.gitignore', '.gitattributes', '.coverage', 'CACHEDIR.TAG',
        '.DS_Store', 'Thumbs.db', 'desktop.ini'
    }
    
    def __init__(self, root_path: Path):
        """Initialize scanner with root path.
        
        Args:
            root_path: Root directory to scan
        """
        self.root_path = root_path.resolve()
        
        # Results categories
        self.files_correct: List[Path] = []
        self.files_no_id: List[Path] = []
        self.files_wrong_format: List[Tuple[Path, str]] = []
        self.files_doc_prefix: List[Tuple[Path, str]] = []
        self.files_python_no_prefix: List[Path] = []
        self.files_legacy_format: List[Tuple[Path, str]] = []
    
    def scan(self, paths: List[Path] = None) -> Dict:
        """Scan directories for ID format issues.
        
        Args:
            paths: Optional list of specific paths to scan. If None, scans root_path.
            
        Returns:
            Dictionary with scan results and statistics
        """
        if paths is None:
            paths = [self.root_path]
        
        for path in paths:
            if path.is_file():
                self._check_file(path)
            elif path.is_dir():
                self._scan_directory(path)
        
        return self._generate_report()
    
    def _scan_directory(self, directory: Path):
        """Recursively scan a directory."""
        try:
            for item in directory.iterdir():
                # Skip excluded directories
                if item.is_dir():
                    if item.name in self.EXCLUDED_DIRS:
                        continue
                    self._scan_directory(item)
                elif item.is_file():
                    self._check_file(item)
        except PermissionError:
            print(f"⚠ Permission denied: {directory}", file=sys.stderr)
    
    def _check_file(self, file_path: Path):
        """Check a single file's ID format."""
        # Skip excluded files
        if file_path.name in self.EXCLUDED_FILES:
            return
        
        # Skip files without extension (likely binary or system files)
        if not file_path.suffix:
            return
        
        filename = file_path.name
        
        # Check for correct formats
        if self.PATTERN_PYTHON_20.match(filename):
            self.files_correct.append(file_path)
            return
        
        if self.PATTERN_REGULAR_20.match(filename):
            # Check if it's a Python file - should have P_ prefix
            if file_path.suffix == '.py':
                self.files_python_no_prefix.append(file_path)
            else:
                self.files_correct.append(file_path)
            return
        
        # Check for legacy format (acceptable but should be migrated)
        if self.PATTERN_LEGACY.match(filename):
            if file_path.suffix == '.py' and not filename.startswith('P_'):
                self.files_python_no_prefix.append(file_path)
            else:
                self.files_legacy_format.append((file_path, "Legacy ID format (17-19 digits)"))
            return
        
        # Check for old DOC- prefix format
        if self.PATTERN_DOC_PREFIX.match(filename):
            # Check if it has an embedded ID
            match = self.PATTERN_DOC_WITH_ID.search(filename)
            if match:
                embedded_id = match.group(1)
                self.files_doc_prefix.append((file_path, f"DOC- prefix with embedded ID: {embedded_id}"))
            else:
                self.files_doc_prefix.append((file_path, "DOC- prefix without embedded ID"))
            return
        
        # File has no ID prefix
        self.files_no_id.append(file_path)
    
    def _generate_report(self) -> Dict:
        """Generate report dictionary."""
        total_files = (
            len(self.files_correct) + 
            len(self.files_no_id) + 
            len(self.files_wrong_format) + 
            len(self.files_doc_prefix) + 
            len(self.files_python_no_prefix) +
            len(self.files_legacy_format)
        )
        
        issues_count = (
            len(self.files_no_id) + 
            len(self.files_wrong_format) + 
            len(self.files_doc_prefix) + 
            len(self.files_python_no_prefix)
        )
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "root_path": str(self.root_path),
            "total_files_scanned": total_files,
            "files_correct": len(self.files_correct),
            "files_with_issues": issues_count,
            "files_legacy_format": len(self.files_legacy_format),
            "issues": {
                "no_id": len(self.files_no_id),
                "wrong_format": len(self.files_wrong_format),
                "doc_prefix": len(self.files_doc_prefix),
                "python_no_p_prefix": len(self.files_python_no_prefix)
            },
            "files_no_id": [str(f.relative_to(self.root_path)) for f in self.files_no_id],
            "files_wrong_format": [(str(f.relative_to(self.root_path)), reason) for f, reason in self.files_wrong_format],
            "files_doc_prefix": [(str(f.relative_to(self.root_path)), reason) for f, reason in self.files_doc_prefix],
            "files_python_no_prefix": [str(f.relative_to(self.root_path)) for f in self.files_python_no_prefix],
            "files_legacy_format": [(str(f.relative_to(self.root_path)), reason) for f, reason in self.files_legacy_format]
        }
    
    def print_report(self, report: Dict = None, verbose: bool = False):
        """Print human-readable report.
        
        Args:
            report: Optional report dict. If None, generates from current state.
            verbose: If True, show all file details
        """
        if report is None:
            report = self._generate_report()
        
        print("=" * 70)
        print("  ID FORMAT SCANNER REPORT")
        print("=" * 70)
        print(f"\nScanned: {report['root_path']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"\nTotal files scanned: {report['total_files_scanned']}")
        print(f"Files with correct format: {report['files_correct']} ✓")
        print(f"Files with legacy format: {report['files_legacy_format']} ⚠")
        print(f"Files with issues: {report['files_with_issues']} ✗")
        
        if report['files_with_issues'] > 0:
            print("\n" + "=" * 70)
            print("  ISSUES FOUND")
            print("=" * 70)
            
            # Files without any ID
            if report['issues']['no_id'] > 0:
                print(f"\n📝 Files without ID prefix: {report['issues']['no_id']}")
                if verbose:
                    for file_path in report['files_no_id']:
                        print(f"   - {file_path}")
                else:
                    for file_path in report['files_no_id'][:5]:
                        print(f"   - {file_path}")
                    if report['issues']['no_id'] > 5:
                        print(f"   ... and {report['issues']['no_id'] - 5} more")
            
            # Files with DOC- prefix
            if report['issues']['doc_prefix'] > 0:
                print(f"\n🔄 Files with DOC- prefix (need conversion): {report['issues']['doc_prefix']}")
                if verbose:
                    for file_path, reason in report['files_doc_prefix']:
                        print(f"   - {file_path}")
                        print(f"     Reason: {reason}")
                else:
                    for file_path, reason in report['files_doc_prefix'][:5]:
                        print(f"   - {file_path}")
                        print(f"     Reason: {reason}")
                    if report['issues']['doc_prefix'] > 5:
                        print(f"   ... and {report['issues']['doc_prefix'] - 5} more")
            
            # Python files without P_ prefix
            if report['issues']['python_no_p_prefix'] > 0:
                print(f"\n🐍 Python files without P_ prefix: {report['issues']['python_no_p_prefix']}")
                if verbose:
                    for file_path in report['files_python_no_prefix']:
                        print(f"   - {file_path}")
                else:
                    for file_path in report['files_python_no_prefix'][:5]:
                        print(f"   - {file_path}")
                    if report['issues']['python_no_p_prefix'] > 5:
                        print(f"   ... and {report['issues']['python_no_p_prefix'] - 5} more")
            
            # Files with wrong format
            if report['issues']['wrong_format'] > 0:
                print(f"\n❌ Files with wrong format: {report['issues']['wrong_format']}")
                if verbose:
                    for file_path, reason in report['files_wrong_format']:
                        print(f"   - {file_path}")
                        print(f"     Reason: {reason}")
                else:
                    for file_path, reason in report['files_wrong_format'][:5]:
                        print(f"   - {file_path}")
                        print(f"     Reason: {reason}")
                    if report['issues']['wrong_format'] > 5:
                        print(f"   ... and {report['issues']['wrong_format'] - 5} more")
        
        # Legacy format (warning only)
        if len(report['files_legacy_format']) > 0:
            print("\n" + "=" * 70)
            print("  LEGACY FORMAT (consider migration)")
            print("=" * 70)
            print(f"\n⚠ Files with legacy ID format: {len(report['files_legacy_format'])}")
            if verbose:
                for file_path, reason in report['files_legacy_format']:
                    print(f"   - {file_path}")
            else:
                for file_path, reason in report['files_legacy_format'][:5]:
                    print(f"   - {file_path}")
                if len(report['files_legacy_format']) > 5:
                    print(f"   ... and {len(report['files_legacy_format']) - 5} more")
        
        print("\n" + "=" * 70)
        
        return report


def main():
    """CLI entry point."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(
        description="Scan directories for files with missing or incorrect ID formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory
  python P_01999000042260124521_id_format_scanner.py
  
  # Scan specific directory
  python P_01999000042260124521_id_format_scanner.py --path /path/to/dir
  
  # Scan multiple directories
  python P_01999000042260124521_id_format_scanner.py --path dir1 dir2 dir3
  
  # Verbose output (show all files)
  python P_01999000042260124521_id_format_scanner.py --verbose
  
  # Export to JSON
  python P_01999000042260124521_id_format_scanner.py --json report.json
        """
    )
    
    parser.add_argument(
        '--path', '-p',
        nargs='+',
        default=['.'],
        help='Path(s) to scan (default: current directory)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show all files in report (not just first 5)'
    )
    parser.add_argument(
        '--json', '-j',
        metavar='FILE',
        help='Export report to JSON file'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress console output (use with --json)'
    )
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    paths = [Path(p).resolve() for p in args.path]
    
    # Determine root path (common ancestor if multiple paths)
    if len(paths) == 1:
        root_path = paths[0] if paths[0].is_dir() else paths[0].parent
    else:
        # Find common ancestor
        root_path = Path(os.path.commonpath([str(p) for p in paths]))
    
    # Create scanner and run
    scanner = IDFormatScanner(root_path)
    report = scanner.scan(paths)
    
    # Print report unless quiet
    if not args.quiet:
        scanner.print_report(report, verbose=args.verbose)
    
    # Export to JSON if requested
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        if not args.quiet:
            print(f"\n✓ Report exported to: {args.json}")
    
    # Return exit code based on issues found
    sys.exit(0 if report['files_with_issues'] == 0 else 1)


if __name__ == '__main__':
    main()
