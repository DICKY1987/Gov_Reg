#!/usr/bin/env python3
"""
Documentation Drift Detector

Detects drift between documentation and code using:
1. Hash mismatches (suite-index.yaml mfid vs. actual file hash)
2. Temporal drift (metadata timestamp < file mtime)
3. Cross-reference validation (broken doc_id links)
4. Module documentation gaps (code exists but no doc)

Exit codes: 0=no drift, 1=drift detected
"""
DOC_ID: DOC-CORE-2-VALIDATION-FIXING-DETECT-DOC-DRIFT-1158

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent directory to path for common module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from common module
from common import REPO_ROOT
from common.rules import DOC_ID_REGEX, validate_doc_id  # Phase 1: Use centralized rules
from common.utils import load_yaml

DOC_ID_PATTERN = DOC_ID_REGEX


@dataclass
class DriftFinding:
    drift_type: str
    severity: str
    file_path: str
    doc_id: Optional[str] = None
    reason: str = ""
    details: Optional[Dict] = None


class DocDriftDetector:
    def __init__(self, suite_index_path: Path, codebase_index_path: Path):
        self.suite_index = self._load_yaml(suite_index_path)
        self.codebase_index = self._load_yaml(codebase_index_path)
        self.findings: List[DriftFinding] = []
        self.stats = defaultdict(int)

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML file safely."""
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}", file=sys.stderr)
            return {}

    def _compute_mfid(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        try:
            return hashlib.sha256(file_path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def _extract_doc_ids_from_file(self, file_path: Path) -> Set[str]:
        """Extract all DOC_ID references from a file."""
        doc_ids = set()
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            doc_ids.update(DOC_ID_PATTERN.findall(content))
        except Exception:
            pass
        return doc_ids

    def detect_all_drift(self) -> bool:
        """Run all drift detection checks. Returns True if no drift detected."""
        self._detect_hash_mismatches()
        self._detect_temporal_drift()
        self._detect_broken_cross_references()
        self._detect_documentation_gaps()
        return len(self.findings) == 0

    def _detect_hash_mismatches(self):
        """Detect files where content changed but metadata hash didn't update."""
        self.stats["hash_checks"] = 0

        if "documents" not in self.suite_index:
            return

        for doc_id, doc_info in self.suite_index.get("documents", {}).items():
            file_path_str = doc_info.get("file_path")
            if not file_path_str:
                continue

            file_path = REPO_ROOT / file_path_str
            if not file_path.exists():
                continue

            self.stats["hash_checks"] += 1

            expected_hash = doc_info.get("mfid", "")
            actual_hash = self._compute_mfid(file_path)

            if expected_hash and actual_hash and expected_hash != actual_hash:
                self.findings.append(
                    DriftFinding(
                        drift_type="hash_mismatch",
                        severity="major",
                        file_path=str(file_path_str),
                        doc_id=doc_id,
                        reason="File content changed but metadata hash not updated",
                        details={
                            "expected_hash": expected_hash[:16] + "...",
                            "actual_hash": actual_hash[:16] + "...",
                        },
                    )
                )
                self.stats["hash_mismatches"] += 1

    def _detect_temporal_drift(self):
        """Detect files modified after their metadata timestamp."""
        self.stats["temporal_checks"] = 0

        if "documents" not in self.suite_index:
            return

        for doc_id, doc_info in self.suite_index.get("documents", {}).items():
            file_path_str = doc_info.get("file_path")
            if not file_path_str:
                continue

            file_path = REPO_ROOT / file_path_str
            if not file_path.exists():
                continue

            self.stats["temporal_checks"] += 1

            metadata_timestamp = doc_info.get("last_modified")
            if not metadata_timestamp:
                continue

            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                metadata_time = datetime.fromisoformat(
                    metadata_timestamp.replace("Z", "+00:00")
                )

                if file_mtime > metadata_time:
                    drift_days = (file_mtime - metadata_time).days
                    severity = "major" if drift_days > 30 else "minor"

                    self.findings.append(
                        DriftFinding(
                            drift_type="temporal_drift",
                            severity=severity,
                            file_path=str(file_path_str),
                            doc_id=doc_id,
                            reason=f"File modified {drift_days} days after metadata timestamp",
                            details={
                                "file_mtime": file_mtime.isoformat(),
                                "metadata_time": metadata_time.isoformat(),
                                "drift_days": drift_days,
                            },
                        )
                    )
                    self.stats["temporal_drifts"] += 1
            except Exception:
                pass

    def _detect_broken_cross_references(self):
        """Detect broken DOC_ID cross-references."""
        self.stats["cross_ref_checks"] = 0

        all_doc_ids = set(self.suite_index.get("documents", {}).keys())

        for doc_id, doc_info in self.suite_index.get("documents", {}).items():
            file_path_str = doc_info.get("file_path")
            if not file_path_str:
                continue

            file_path = REPO_ROOT / file_path_str
            if not file_path.exists():
                continue

            self.stats["cross_ref_checks"] += 1

            referenced_ids = self._extract_doc_ids_from_file(file_path)
            broken_refs = referenced_ids - all_doc_ids - {doc_id}

            if broken_refs:
                self.findings.append(
                    DriftFinding(
                        drift_type="broken_cross_reference",
                        severity="minor",
                        file_path=str(file_path_str),
                        doc_id=doc_id,
                        reason=f"References {len(broken_refs)} non-existent DOC_IDs",
                        details={"broken_refs": sorted(list(broken_refs))[:5]},
                    )
                )
                self.stats["broken_refs"] += len(broken_refs)

    def _detect_documentation_gaps(self):
        """Detect modules with code but missing documentation."""
        self.stats["gap_checks"] = 0

        modules = self.codebase_index.get("modules", [])
        if not modules:
            return

        for module_info in modules:
            if not isinstance(module_info, dict):
                continue

            module_path = module_info.get("path")
            if not module_path:
                continue

            self.stats["gap_checks"] += 1

            doc_path = module_info.get("documentation")
            if not doc_path:
                module_dir = REPO_ROOT / module_path
                if module_dir.exists():
                    py_files = list(module_dir.glob("**/*.py"))
                    if py_files:
                        self.findings.append(
                            DriftFinding(
                                drift_type="documentation_gap",
                                severity="minor",
                                file_path=module_path,
                                reason=f"Module has {len(py_files)} Python files but no documentation",
                                details={"py_file_count": len(py_files)},
                            )
                        )
                        self.stats["doc_gaps"] += 1

    def print_report(self):
        """Print human-readable drift report."""
        print(f"\n{'=' * 60}")
        print("DOCUMENTATION DRIFT DETECTION REPORT")
        print(f"{'=' * 60}\n")

        print(f"Total findings: {len(self.findings)}")
        print(f"  - Hash mismatches: {self.stats.get('hash_mismatches', 0)}")
        print(f"  - Temporal drifts: {self.stats.get('temporal_drifts', 0)}")
        print(f"  - Broken references: {self.stats.get('broken_refs', 0)}")
        print(f"  - Documentation gaps: {self.stats.get('doc_gaps', 0)}")
        print()

        if self.findings:
            by_severity = defaultdict(list)
            for finding in self.findings:
                by_severity[finding.severity].append(finding)

            for severity in ["critical", "major", "minor"]:
                findings = by_severity.get(severity, [])
                if findings:
                    print(f"\n{severity.upper()} ({len(findings)}):")
                    for f in findings[:10]:
                        print(f"  [{f.drift_type}] {f.file_path}")
                        print(f"    {f.reason}")
                        if f.doc_id:
                            print(f"    DOC_ID: {f.doc_id}")
                    if len(findings) > 10:
                        print(f"  ... and {len(findings) - 10} more")

        print(f"\n{'=' * 60}")
        print(
            f"Status: {'✅ NO DRIFT DETECTED' if len(self.findings) == 0 else '⚠️  DRIFT DETECTED'}"
        )
        print(f"{'=' * 60}\n")

    def save_report(self, output_path: Path):
        """Save drift report as JSON."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(self.findings),
                "hash_mismatches": self.stats.get("hash_mismatches", 0),
                "temporal_drifts": self.stats.get("temporal_drifts", 0),
                "broken_references": self.stats.get("broken_refs", 0),
                "documentation_gaps": self.stats.get("doc_gaps", 0),
            },
            "findings": [asdict(f) for f in self.findings],
            "stats": dict(self.stats),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"✅ Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Detect documentation drift")
    parser.add_argument(
        "--suite-index",
        type=Path,
        default=REPO_ROOT / "docs" / "DOC_.index" / "suite-index.yaml",
        help="Path to suite-index.yaml",
    )
    parser.add_argument(
        "--codebase-index",
        type=Path,
        default=REPO_ROOT / "docs" / "DOC_reference" / "CODEBASE_INDEX.yaml",
        help="Path to CODEBASE_INDEX.yaml",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=REPO_ROOT / ".state" / "doc_drift_report.json",
        help="Output path for JSON report",
    )
    parser.add_argument(
        "--ci-check",
        action="store_true",
        help="CI mode: exit with error if drift detected",
    )
    parser.add_argument(
        "--max-drift",
        type=int,
        default=20,
        help="Maximum allowed drift findings in CI mode",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print report only, don't save"
    )

    args = parser.parse_args()

    detector = DocDriftDetector(args.suite_index, args.codebase_index)
    no_drift = detector.detect_all_drift()
    detector.print_report()

    if not args.dry_run:
        detector.save_report(args.report)

    if args.ci_check:
        if len(detector.findings) > args.max_drift:
            print(
                f"❌ CI CHECK FAILED: {len(detector.findings)} findings exceeds threshold of {args.max_drift}"
            )
            sys.exit(1)
        else:
            print(
                f"✅ CI CHECK PASSED: {len(detector.findings)} findings within threshold of {args.max_drift}"
            )

    sys.exit(0 if no_drift else 1)


if __name__ == "__main__":
    main()

