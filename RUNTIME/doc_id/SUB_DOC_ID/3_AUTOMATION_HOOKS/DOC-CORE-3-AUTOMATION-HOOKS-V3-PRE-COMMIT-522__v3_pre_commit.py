# DOC_LINK: DOC-CORE-3-AUTOMATION-HOOKS-V3-PRE-COMMIT-522
# TRIGGER_ID: TRIGGER-HOOK-V3-PRE-COMMIT-004
"""
Registry V3 Pre-Commit Hook
DOC_LINK: A-REGV3-PRECOMMIT-009
Work ID: WORK-REGV3-002

Validates Registry V3 consistency before allowing git commits.
Blocks commits if doc_id conflicts or schema violations detected.
"""

import sys
import sqlite3
from pathlib import Path

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def check_v3_database_exists(db_path: Path) -> bool:
    """Check if V3 database exists (graceful degradation)"""
    return db_path.exists()


def check_schema_integrity(db_path: Path) -> tuple[bool, list[str]]:
    """Verify Tier 2 tables exist"""
    issues = []

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check code_symbols table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='code_symbols'")
        if not cursor.fetchone():
            issues.append("Missing table: code_symbols")

        # Check code_edges table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='code_edges'")
        if not cursor.fetchone():
            issues.append("Missing table: code_edges")

        conn.close()

    except Exception as e:
        issues.append(f"Database error: {e}")

    return len(issues) == 0, issues


def check_doc_id_conflicts(db_path: Path) -> tuple[bool, list[str]]:
    """Check for doc_id conflicts in vw_doc_id_conflicts view"""
    issues = []

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if view exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='vw_doc_id_conflicts'")
        if not cursor.fetchone():
            # View doesn't exist - skip check
            conn.close()
            return True, []

        # Query for conflicts
        cursor.execute("SELECT COUNT(*) FROM vw_doc_id_conflicts")
        conflict_count = cursor.fetchone()[0]

        if conflict_count > 0:
            cursor.execute("SELECT doc_id, file_count FROM vw_doc_id_conflicts LIMIT 5")
            for doc_id, file_count in cursor.fetchall():
                issues.append(f"Conflict: doc_id '{doc_id}' appears in {file_count} files")

        conn.close()

    except Exception as e:
        issues.append(f"Conflict check error: {e}")

    return len(issues) == 0, issues


def main():
    """Run pre-commit validation"""
    repo_root = Path(__file__).parent.parent.parent
    db_path = repo_root / "SUB_DOC_ID" / "migration_v3" / "data" / "registry_v3.db"

    print(f"\n{YELLOW}[Registry V3 Pre-Commit Validation]{RESET}")

    # Check if V3 database exists
    if not check_v3_database_exists(db_path):
        print(f"{YELLOW}⚠ V3 database not found - skipping validation{RESET}")
        sys.exit(0)  # Graceful degradation

    print(f"✓ V3 database found: {db_path}")

    all_checks_passed = True

    # Check 1: Schema integrity
    print("\nChecking schema integrity...")
    schema_ok, schema_issues = check_schema_integrity(db_path)
    if schema_ok:
        print(f"{GREEN}✓ Schema integrity validated{RESET}")
    else:
        print(f"{RED}✗ Schema integrity FAILED:{RESET}")
        for issue in schema_issues:
            print(f"  - {issue}")
        all_checks_passed = False

    # Check 2: Doc ID conflicts
    print("\nChecking for doc_id conflicts...")
    conflicts_ok, conflict_issues = check_doc_id_conflicts(db_path)
    if conflicts_ok:
        print(f"{GREEN}✓ No doc_id conflicts detected{RESET}")
    else:
        print(f"{RED}✗ Doc ID conflicts detected:{RESET}")
        for issue in conflict_issues:
            print(f"  - {issue}")
        all_checks_passed = False

    # Final result
    if all_checks_passed:
        print(f"\n{GREEN}✅ All V3 validation checks passed - commit allowed{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}❌ V3 validation FAILED - commit blocked{RESET}")
        print(f"{YELLOW}Fix the issues above and try again.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
