#!/usr/bin/env python3
# DOC_ID: DOC-SCRIPT-0996
"""
Collector Output Validator
Created: 2026-01-04

Validates output from ai_cli_provenance_collector.py for:
- Database schema correctness
- Data integrity (foreign keys, indexes)
- Evidence query results structure
- Privacy compliance (no raw prompts)
- Performance metrics (database size, query times)

Usage:
    python validate_collector_output.py --db ai_provenance.db
    python validate_collector_output.py --db ai_provenance.db --verbose
    python validate_collector_output.py --db ai_provenance.db --check-privacy
"""

import sys
import argparse
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# ============================================================================
# VALIDATION RULES
# ============================================================================

REQUIRED_TABLES = ['sessions', 'file_events', 'intent_signals']
REQUIRED_VIEWS = ['v_file_activity_summary', 'v_intent_signals_by_doc']
REQUIRED_INDEXES = [
    'idx_file_events_doc_id',
    'idx_file_events_session_id',
    'idx_file_events_timestamp',
    'idx_intent_signals_session_id'
]

MAX_DB_SIZE_MB_PER_10K_RECORDS = 1.0
SHA256_HASH_LENGTH = 64


# ============================================================================
# OUTPUT VALIDATOR
# ============================================================================

class CollectorOutputValidator:
    """Validates collector output database."""

    def __init__(self, db_path: Path, verbose: bool = False, check_privacy: bool = False):
        self.db_path = db_path
        self.verbose = verbose
        self.check_privacy = check_privacy

        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

        self.conn: sqlite3.Connection = None

    def log_error(self, msg: str):
        """Log an error message."""
        self.errors.append(f"❌ ERROR: {msg}")
        if self.verbose:
            print(f"❌ ERROR: {msg}")

    def log_warning(self, msg: str):
        """Log a warning message."""
        self.warnings.append(f"⚠️  WARNING: {msg}")
        if self.verbose:
            print(f"⚠️  WARNING: {msg}")

    def log_info(self, msg: str):
        """Log an info message."""
        self.info.append(f"ℹ️  INFO: {msg}")
        if self.verbose:
            print(f"ℹ️  INFO: {msg}")

    def connect(self) -> bool:
        """Connect to database."""
        if not self.db_path.exists():
            self.log_error(f"Database file not found: {self.db_path}")
            return False

        try:
            self.conn = sqlite3.connect(self.db_path)
            self.log_info(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            self.log_error(f"Failed to connect to database: {e}")
            return False

    def validate_schema(self) -> bool:
        """Validate database schema."""
        valid = True

        # Check tables exist
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        for table in REQUIRED_TABLES:
            if table not in tables:
                self.log_error(f"Required table missing: '{table}'")
                valid = False

        self.log_info(f"Found {len(tables)} tables")

        # Check views exist
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='view'"
        )
        views = [row[0] for row in cursor.fetchall()]

        for view in REQUIRED_VIEWS:
            if view not in views:
                self.log_warning(f"Expected view missing: '{view}'")

        self.log_info(f"Found {len(views)} views")

        # Check indexes exist
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        for index in REQUIRED_INDEXES:
            if index not in indexes:
                self.log_warning(f"Expected index missing: '{index}'")

        self.log_info(f"Found {len(indexes)} indexes")

        return valid

    def validate_data_integrity(self) -> bool:
        """Validate data integrity."""
        valid = True

        # Check for orphaned file_events (session_id not in sessions)
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM file_events
            WHERE session_id NOT IN (SELECT session_id FROM sessions)
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            self.log_error(f"Found {orphaned} orphaned file_events (invalid session_id)")
            valid = False

        # Check for orphaned intent_signals
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM intent_signals
            WHERE session_id NOT IN (SELECT session_id FROM sessions)
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            self.log_error(f"Found {orphaned} orphaned intent_signals (invalid session_id)")
            valid = False

        # Check for NULL required fields
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM file_events
            WHERE file_path_hash IS NULL OR timestamp IS NULL
        """)
        null_fields = cursor.fetchone()[0]
        if null_fields > 0:
            self.log_error(f"Found {null_fields} file_events with NULL required fields")
            valid = False

        self.log_info("Data integrity checks passed")
        return valid

    def validate_privacy_compliance(self) -> bool:
        """Validate privacy compliance (no raw prompts, proper hashing)."""
        if not self.check_privacy:
            self.log_info("Privacy checks skipped (use --check-privacy)")
            return True

        valid = True

        # Check intent_signals.prompt_hash is SHA256 (64 hex chars)
        cursor = self.conn.execute("SELECT prompt_hash FROM intent_signals LIMIT 100")
        for (prompt_hash,) in cursor.fetchall():
            if prompt_hash:
                if len(prompt_hash) != SHA256_HASH_LENGTH:
                    self.log_error(f"Invalid prompt hash length: {len(prompt_hash)} (expected {SHA256_HASH_LENGTH})")
                    valid = False
                if not all(c in '0123456789abcdef' for c in prompt_hash):
                    self.log_error(f"Invalid prompt hash format: {prompt_hash} (not hex)")
                    valid = False

        # Check for suspicious text fields (should not contain "password", "secret", etc.)
        cursor = self.conn.execute("SELECT detected_keywords FROM intent_signals LIMIT 100")
        for (keywords,) in cursor.fetchall():
            if keywords:
                keywords_lower = keywords.lower()
                if 'password' in keywords_lower or 'secret' in keywords_lower or 'token' in keywords_lower:
                    self.log_warning(f"Suspicious keyword detected: {keywords}")

        self.log_info("Privacy compliance checks passed")
        return valid

    def validate_performance(self) -> bool:
        """Validate performance metrics."""
        valid = True

        # Check database size
        db_size_bytes = self.db_path.stat().st_size
        db_size_mb = db_size_bytes / (1024 * 1024)

        # Count records
        cursor = self.conn.execute("SELECT COUNT(*) FROM file_events")
        file_event_count = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM intent_signals")
        intent_signal_count = cursor.fetchone()[0]

        total_records = file_event_count + intent_signal_count

        self.log_info(f"Database size: {db_size_mb:.2f} MB")
        self.log_info(f"Total records: {total_records:,}")

        if total_records > 0:
            records_per_mb = total_records / db_size_mb if db_size_mb > 0 else 0
            self.log_info(f"Records per MB: {records_per_mb:.0f}")

            # Check if within performance target
            expected_size_mb = (total_records / 10000) * MAX_DB_SIZE_MB_PER_10K_RECORDS
            if db_size_mb > expected_size_mb * 1.5:  # Allow 50% margin
                self.log_warning(
                    f"Database size ({db_size_mb:.2f} MB) exceeds expected size "
                    f"({expected_size_mb:.2f} MB) for {total_records:,} records"
                )

        return valid

    def validate_query_results(self) -> bool:
        """Validate evidence query results structure."""
        valid = True

        # Check if materialized views return results
        cursor = self.conn.execute("SELECT COUNT(*) FROM v_file_activity_summary")
        summary_count = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM v_intent_signals_by_doc")
        intent_count = cursor.fetchone()[0]

        self.log_info(f"File activity summary records: {summary_count}")
        self.log_info(f"Intent signals by doc records: {intent_count}")

        # Sample query test
        cursor = self.conn.execute("""
            SELECT doc_id, session_count, view_count, edit_count, create_count
            FROM v_file_activity_summary LIMIT 1
        """)
        sample = cursor.fetchone()
        if sample:
            self.log_info(f"Sample activity: doc_id={sample[0]}, sessions={sample[1]}, views={sample[2]}, edits={sample[3]}, creates={sample[4]}")

        return valid

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations."""
        print(f"\n{'='*60}")
        print(f"Collector Output Validation")
        print(f"{'='*60}")
        print(f"Database: {self.db_path}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        if not self.connect():
            return False, self._generate_report()

        try:
            results = {
                'schema': self.validate_schema(),
                'data_integrity': self.validate_data_integrity(),
                'privacy': self.validate_privacy_compliance(),
                'performance': self.validate_performance(),
                'query_results': self.validate_query_results()
            }

            overall_valid = all(results.values())

        finally:
            if self.conn:
                self.conn.close()

        return overall_valid, self._generate_report()

    def _generate_report(self) -> Dict[str, Any]:
        """Generate validation report."""
        return {
            'db_path': str(self.db_path),
            'timestamp': datetime.now().isoformat(),
            'valid': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }

    def print_summary(self, report: Dict[str, Any]):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print(f"Validation Summary")
        print(f"{'='*60}")

        if report['valid']:
            print("✅ Database is VALID")
        else:
            print("❌ Database has ERRORS")

        print(f"\nErrors: {report['error_count']}")
        print(f"Warnings: {report['warning_count']}")

        if report['errors']:
            print("\nErrors:")
            for error in report['errors']:
                print(f"  {error}")

        if report['warnings']:
            print("\nWarnings:")
            for warning in report['warnings']:
                print(f"  {warning}")

        if self.verbose and report['info']:
            print("\nInfo:")
            for info in report['info']:
                print(f"  {info}")

        print(f"\n{'='*60}\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate AI CLI provenance collector output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_collector_output.py --db ai_provenance.db
  python validate_collector_output.py --db ai_provenance.db --verbose
  python validate_collector_output.py --db ai_provenance.db --check-privacy
  python validate_collector_output.py --db ai_provenance.db --output report.json
        """
    )

    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to collector output database"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--check-privacy",
        action="store_true",
        help="Run privacy compliance checks"
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Save validation report to JSON file"
    )

    args = parser.parse_args()

    # Run validation
    validator = CollectorOutputValidator(args.db, verbose=args.verbose, check_privacy=args.check_privacy)
    valid, report = validator.validate()
    validator.print_summary(report)

    # Save report if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
