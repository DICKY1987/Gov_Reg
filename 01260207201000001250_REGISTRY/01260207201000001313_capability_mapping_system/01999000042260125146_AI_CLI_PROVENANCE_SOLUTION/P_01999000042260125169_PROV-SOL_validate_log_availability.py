#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0994
"""
Log Availability Validator
Created: 2026-01-04

Validates availability and accessibility of AI CLI logs:
- Checks if log directories exist
- Counts available log files
- Checks file permissions
- Reports graceful degradation status

Usage:
    python validate_log_availability.py
    python validate_log_availability.py --verbose
    python validate_log_availability.py --output report.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from glob import glob


# ============================================================================
# LOG SOURCE CONFIGURATION
# ============================================================================

LOG_SOURCES = {
    'claude': {
        'name': 'Claude Code',
        'pattern': '.claude/projects/**/*.jsonl',
        'description': 'Claude Code project logs (JSONL format)'
    },
    'codex': {
        'name': 'Codex',
        'pattern': '.codex/sessions/**/*.jsonl',
        'description': 'Codex session logs (JSONL format)'
    },
    'copilot_history': {
        'name': 'GitHub Copilot (Command History)',
        'pattern': '.copilot/command-history-state.json',
        'description': 'Copilot command history (JSON format)'
    },
    'copilot_sessions': {
        'name': 'GitHub Copilot (Sessions)',
        'pattern': '.copilot/session-state/*.jsonl',
        'description': 'Copilot session state (JSONL format)'
    }
}


# ============================================================================
# LOG AVAILABILITY VALIDATOR
# ============================================================================

class LogAvailabilityValidator:
    """Validates AI CLI log availability."""

    def __init__(self, base_dir: Path = None, verbose: bool = False):
        """Initialize validator.

        Args:
            base_dir: Base directory to search (defaults to user home)
            verbose: Enable verbose output
        """
        self.base_dir = Path(base_dir) if base_dir else Path.home()
        self.verbose = verbose

    def check_source(self, source_id: str, config: Dict[str, str]) -> Dict[str, Any]:
        """Check availability of a log source.

        Args:
            source_id: Source identifier
            config: Source configuration

        Returns:
            Dictionary with availability status
        """
        result = {
            'source_id': source_id,
            'name': config['name'],
            'description': config['description'],
            'pattern': config['pattern'],
            'available': False,
            'file_count': 0,
            'files': [],
            'total_size_bytes': 0,
            'errors': []
        }

        # Build search pattern
        search_pattern = str(self.base_dir / config['pattern'])

        try:
            # Find matching files
            files = glob(search_pattern, recursive=True)
            result['file_count'] = len(files)
            result['available'] = len(files) > 0

            # Collect file info
            for file_path in files:
                try:
                    path = Path(file_path)
                    if path.exists():
                        size = path.stat().st_size
                        result['total_size_bytes'] += size
                        result['files'].append({
                            'path': str(path),
                            'size_bytes': size,
                            'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                        })
                except Exception as e:
                    result['errors'].append(f"Error reading {file_path}: {e}")

        except Exception as e:
            result['errors'].append(f"Error searching for files: {e}")

        return result

    def validate_all(self) -> Dict[str, Any]:
        """Validate all log sources.

        Returns:
            Validation report dictionary
        """
        report = {
            'base_dir': str(self.base_dir),
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'summary': {
                'total_sources': len(LOG_SOURCES),
                'available_sources': 0,
                'total_files': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0.0
            }
        }

        # Check each source
        for source_id, config in LOG_SOURCES.items():
            if self.verbose:
                print(f"Checking {config['name']}...")

            result = self.check_source(source_id, config)
            report['sources'][source_id] = result

            # Update summary
            if result['available']:
                report['summary']['available_sources'] += 1

            report['summary']['total_files'] += result['file_count']
            report['summary']['total_size_bytes'] += result['total_size_bytes']

        # Calculate total size in MB
        report['summary']['total_size_mb'] = report['summary']['total_size_bytes'] / (1024 * 1024)

        return report

    def print_report(self, report: Dict[str, Any]):
        """Print validation report to console.

        Args:
            report: Validation report dictionary
        """
        print(f"\n{'='*60}")
        print(f"AI CLI Log Availability Report")
        print(f"{'='*60}")
        print(f"Base Directory: {report['base_dir']}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"{'='*60}\n")

        # Summary
        summary = report['summary']
        print(f"Summary:")
        print(f"  Total Sources: {summary['total_sources']}")
        print(f"  Available Sources: {summary['available_sources']}")
        print(f"  Total Files: {summary['total_files']}")
        print(f"  Total Size: {summary['total_size_mb']:.2f} MB")
        print()

        # Individual sources
        for source_id, result in report['sources'].items():
            status = "✅ AVAILABLE" if result['available'] else "❌ NOT FOUND"
            print(f"{result['name']}: {status}")
            print(f"  Description: {result['description']}")
            print(f"  Pattern: {result['pattern']}")
            print(f"  Files Found: {result['file_count']}")

            if result['available']:
                print(f"  Total Size: {result['total_size_bytes'] / 1024:.2f} KB")

                if self.verbose and result['files']:
                    print(f"  Files:")
                    for file_info in result['files'][:5]:  # Show first 5
                        print(f"    - {file_info['path']} ({file_info['size_bytes']} bytes)")
                    if len(result['files']) > 5:
                        print(f"    ... and {len(result['files']) - 5} more")

            if result['errors']:
                print(f"  Errors:")
                for error in result['errors']:
                    print(f"    - {error}")

            print()

        # Graceful degradation message
        print(f"{'='*60}")
        if summary['available_sources'] == 0:
            print(f"⚠️  No AI CLI logs found")
            print(f"   The system will gracefully degrade:")
            print(f"   - Evidence queries will return default values")
            print(f"   - exists: false, session_count: 0, etc.")
        elif summary['available_sources'] < summary['total_sources']:
            print(f"⚠️  Some AI CLI logs missing ({summary['available_sources']}/{summary['total_sources']})")
            print(f"   Provenance data will be incomplete but system will function")
        else:
            print(f"✅ All AI CLI log sources available")

        print(f"{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate AI CLI log availability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_log_availability.py
  python validate_log_availability.py --verbose
  python validate_log_availability.py --base-dir /path/to/home
  python validate_log_availability.py --output report.json
        """
    )

    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Base directory to search (default: user home)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    # Run validation
    validator = LogAvailabilityValidator(args.base_dir, args.verbose)
    report = validator.validate_all()
    validator.print_report(report)

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if report['summary']['available_sources'] > 0 else 1)


if __name__ == "__main__":
    main()
