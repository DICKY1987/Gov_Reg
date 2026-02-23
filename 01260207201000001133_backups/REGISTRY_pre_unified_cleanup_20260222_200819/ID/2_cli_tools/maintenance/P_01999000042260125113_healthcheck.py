"""Nightly ID and registry health check (GAP-008).

FILE_ID: 01999000042260125113
PURPOSE: Scheduled health check for ID lifecycle and registry system
PHASE: Phase 3 - Health Monitoring
BACKLOG: 01999000042260125103 GAP-008
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import sys

# Add parent to path for imports
repo_root = Path(__file__).parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent.parent / "01260207201000001173_govreg_core"))
from P_01260207233100000071_scanner_service import ScannerService
from P_01999000042260125108_registry_fs_reconciler import RegistryFilesystemReconciler
from P_01999000042260125111_orphan_purger import OrphanPurger


@dataclass
class HealthCheckViolation:
    """A health check violation."""
    violation_code: str
    severity: str  # "CRITICAL", "ERROR", "WARNING"
    category: str  # "dir_id", "registry", "orphans", "references"
    message: str
    count: int


@dataclass
class HealthCheckReport:
    """Report from health check operation."""
    healthcheck_id: str
    timestamp: str
    total_checks: int
    checks_passed: int
    checks_failed: int
    critical_violations: int
    error_violations: int
    warning_violations: int
    violations: List[HealthCheckViolation]
    exit_code: int
    evidence_path: Path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        result = asdict(self)
        result['evidence_path'] = str(result['evidence_path'])
        return result


class HealthChecker:
    """Comprehensive health check for ID lifecycle and registry system."""
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize health checker.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root dir_id
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "healthchecks"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.scanner = ScannerService(project_root, project_root_id)
        self.reconciler = RegistryFilesystemReconciler(project_root)
        self.purger = OrphanPurger(project_root)
    
    def nightly_id_registry_healthcheck(
        self,
        config_path: Path,
        fail_on_critical: bool = True,
        emit_evidence: bool = True
    ) -> HealthCheckReport:
        """Run comprehensive health check.
        
        Args:
            config_path: Path to IDPKG config
            fail_on_critical: Exit non-zero on critical violations
            emit_evidence: Emit evidence artifacts
            
        Returns:
            HealthCheckReport: Health check outcome
        """
        healthcheck_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        violations: List[HealthCheckViolation] = []
        total_checks = 5
        checks_passed = 0
        checks_failed = 0
        
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        registry_path = Path(config.get('registry_path', 'governance_registry_unified.json'))
        if not registry_path.is_absolute():
            registry_path = self.project_root / registry_path
        
        # Check 1: Scanner check for .dir_id violations
        print("  [1/5] Checking .dir_id integrity...")
        scanner_violations = self._check_dir_id_integrity()
        if scanner_violations:
            checks_failed += 1
            violations.extend(scanner_violations)
        else:
            checks_passed += 1
        
        # Check 2: Registry-filesystem reconciliation
        print("  [2/5] Checking registry-filesystem sync...")
        reconcile_violations = self._check_registry_fs_sync(registry_path)
        if reconcile_violations:
            checks_failed += 1
            violations.extend(reconcile_violations)
        else:
            checks_passed += 1
        
        # Check 3: Orphan detection
        print("  [3/5] Checking for orphaned entries...")
        orphan_violations = self._check_orphans(registry_path)
        if orphan_violations:
            checks_failed += 1
            violations.extend(orphan_violations)
        else:
            checks_passed += 1
        
        # Check 4: Duplicate dir_id detection
        print("  [4/5] Checking for duplicate dir_ids...")
        duplicate_violations = self._check_duplicate_dir_ids()
        if duplicate_violations:
            checks_failed += 1
            violations.extend(duplicate_violations)
        else:
            checks_passed += 1
        
        # Check 5: Coverage check
        print("  [5/5] Checking dir_id coverage...")
        coverage_violations = self._check_coverage(registry_path)
        if coverage_violations:
            checks_failed += 1
            violations.extend(coverage_violations)
        else:
            checks_passed += 1
        
        # Count violations by severity
        critical_violations = sum(1 for v in violations if v.severity == "CRITICAL")
        error_violations = sum(1 for v in violations if v.severity == "ERROR")
        warning_violations = sum(1 for v in violations if v.severity == "WARNING")
        
        # Determine exit code
        exit_code = 0
        if fail_on_critical and critical_violations > 0:
            exit_code = 1
        elif error_violations > 0:
            exit_code = 2
        
        # Save evidence
        evidence_path = self.evidence_dir / f"{healthcheck_id}_healthcheck.json"
        if emit_evidence:
            self._save_evidence(
                evidence_path,
                healthcheck_id,
                timestamp,
                total_checks,
                checks_passed,
                checks_failed,
                critical_violations,
                error_violations,
                warning_violations,
                violations
            )
        
        return HealthCheckReport(
            healthcheck_id=healthcheck_id,
            timestamp=timestamp,
            total_checks=total_checks,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            critical_violations=critical_violations,
            error_violations=error_violations,
            warning_violations=warning_violations,
            violations=violations,
            exit_code=exit_code,
            evidence_path=evidence_path
        )
    
    def _check_dir_id_integrity(self) -> List[HealthCheckViolation]:
        """Check .dir_id integrity via scanner."""
        violations = []
        
        try:
            scan_report = self.scanner.scan(self.project_root, repair=False)
            
            if scan_report.violations_found > 0:
                # Group by violation code
                violation_counts = {}
                for v in scan_report.violations:
                    code = v.violation_code
                    violation_counts[code] = violation_counts.get(code, 0) + 1
                
                for code, count in violation_counts.items():
                    violations.append(HealthCheckViolation(
                        violation_code=code,
                        severity="CRITICAL" if "IDENTITY" in code else "ERROR",
                        category="dir_id",
                        message=f"{count} .dir_id violations detected",
                        count=count
                    ))
        except Exception as e:
            violations.append(HealthCheckViolation(
                violation_code="HC-SCANNER-FAILED",
                severity="CRITICAL",
                category="dir_id",
                message=f"Scanner check failed: {e}",
                count=1
            ))
        
        return violations
    
    def _check_registry_fs_sync(self, registry_path: Path) -> List[HealthCheckViolation]:
        """Check registry-filesystem synchronization."""
        violations = []
        
        try:
            reconcile_report = self.reconciler.registry_fs_reconcile(
                registry_path,
                auto_repair=False,
                emit_evidence=False
            )
            
            if reconcile_report.checks_failed > 0:
                # Group by defect code
                defect_counts = {}
                for defect in reconcile_report.defects:
                    code = defect.defect_code
                    defect_counts[code] = defect_counts.get(code, 0) + 1
                
                for code, count in defect_counts.items():
                    violations.append(HealthCheckViolation(
                        violation_code=code,
                        severity="ERROR",
                        category="registry",
                        message=f"{count} registry sync issues detected",
                        count=count
                    ))
        except Exception as e:
            violations.append(HealthCheckViolation(
                violation_code="HC-RECONCILE-FAILED",
                severity="CRITICAL",
                category="registry",
                message=f"Reconciliation check failed: {e}",
                count=1
            ))
        
        return violations
    
    def _check_orphans(self, registry_path: Path) -> List[HealthCheckViolation]:
        """Check for orphaned entries."""
        violations = []
        
        try:
            purge_report = self.purger.purge_orphans(
                registry_path,
                quarantine=False,
                dry_run=True
            )
            
            if purge_report.orphans_detected > 0:
                for orphan_type, count in purge_report.orphan_types.items():
                    if count > 0:
                        violations.append(HealthCheckViolation(
                            violation_code=f"ORPHAN-{orphan_type.upper()}",
                            severity="WARNING",
                            category="orphans",
                            message=f"{count} orphaned {orphan_type.replace('_', ' ')} detected",
                            count=count
                        ))
        except Exception as e:
            violations.append(HealthCheckViolation(
                violation_code="HC-ORPHAN-CHECK-FAILED",
                severity="ERROR",
                category="orphans",
                message=f"Orphan check failed: {e}",
                count=1
            ))
        
        return violations
    
    def _check_duplicate_dir_ids(self) -> List[HealthCheckViolation]:
        """Check for duplicate dir_ids."""
        violations = []
        
        try:
            seen_dir_ids = {}
            duplicates = []
            
            for dir_id_path in self.project_root.rglob(".dir_id"):
                try:
                    with open(dir_id_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    dir_id = data.get('dir_id')
                    if dir_id:
                        if dir_id in seen_dir_ids:
                            duplicates.append((dir_id, str(dir_id_path), seen_dir_ids[dir_id]))
                        else:
                            seen_dir_ids[dir_id] = str(dir_id_path)
                except Exception:
                    pass
            
            if duplicates:
                violations.append(HealthCheckViolation(
                    violation_code="HC-DUPLICATE-DIR-ID",
                    severity="CRITICAL",
                    category="dir_id",
                    message=f"{len(duplicates)} duplicate dir_ids detected",
                    count=len(duplicates)
                ))
        except Exception as e:
            violations.append(HealthCheckViolation(
                violation_code="HC-DUPLICATE-CHECK-FAILED",
                severity="ERROR",
                category="dir_id",
                message=f"Duplicate check failed: {e}",
                count=1
            ))
        
        return violations
    
    def _check_coverage(self, registry_path: Path) -> List[HealthCheckViolation]:
        """Check dir_id coverage."""
        violations = []
        
        try:
            # Load registry
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            files = registry.get('files', [])
            if not files:
                return violations
            
            # Count null dir_ids
            null_count = sum(1 for f in files if not f.get('dir_id'))
            total_count = len(files)
            coverage = ((total_count - null_count) / total_count * 100) if total_count > 0 else 0
            
            # Warn if coverage < 90%
            if coverage < 90:
                violations.append(HealthCheckViolation(
                    violation_code="HC-LOW-COVERAGE",
                    severity="WARNING" if coverage >= 80 else "ERROR",
                    category="coverage",
                    message=f"Low dir_id coverage: {coverage:.1f}% ({null_count}/{total_count} null)",
                    count=null_count
                ))
        except Exception as e:
            violations.append(HealthCheckViolation(
                violation_code="HC-COVERAGE-CHECK-FAILED",
                severity="ERROR",
                category="coverage",
                message=f"Coverage check failed: {e}",
                count=1
            ))
        
        return violations
    
    def _save_evidence(
        self,
        evidence_path: Path,
        healthcheck_id: str,
        timestamp: str,
        total_checks: int,
        checks_passed: int,
        checks_failed: int,
        critical_violations: int,
        error_violations: int,
        warning_violations: int,
        violations: List[HealthCheckViolation]
    ):
        """Save health check evidence."""
        evidence = {
            "healthcheck_id": healthcheck_id,
            "timestamp": timestamp,
            "total_checks": total_checks,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "critical_violations": critical_violations,
            "error_violations": error_violations,
            "warning_violations": warning_violations,
            "violations": [asdict(v) for v in violations]
        }
        
        with open(evidence_path, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)


def nightly_id_registry_healthcheck(
    config_path: Path,
    fail_on_critical: bool = True,
    emit_evidence: bool = True
) -> HealthCheckReport:
    """Run nightly health check (public API).
    
    Args:
        config_path: Path to IDPKG config
        fail_on_critical: Exit non-zero on critical violations
        emit_evidence: Emit evidence artifacts
        
    Returns:
        HealthCheckReport: Health check outcome
    """
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    project_root = Path(config.get('project_root', Path.cwd()))
    project_root_id = config.get('project_root_id', '01260207201000000000')
    
    checker = HealthChecker(project_root, project_root_id)
    return checker.nightly_id_registry_healthcheck(config_path, fail_on_critical, emit_evidence)


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Nightly ID and registry health check")
    parser.add_argument("--config", type=Path, required=True, help="Path to IDPKG config")
    parser.add_argument("--no-fail-on-critical", action="store_true", help="Don't exit non-zero on critical violations")
    parser.add_argument("--no-evidence", action="store_true", help="Don't emit evidence artifacts")
    
    args = parser.parse_args()
    
    print("Running nightly health check...")
    report = nightly_id_registry_healthcheck(
        args.config,
        fail_on_critical=not args.no_fail_on_critical,
        emit_evidence=not args.no_evidence
    )
    
    print(f"\n{'='*60}")
    print("Health Check Report")
    print(f"{'='*60}")
    print(f"Checks: {report.checks_passed}/{report.total_checks} passed")
    print(f"Violations: {report.critical_violations} critical, {report.error_violations} errors, {report.warning_violations} warnings")
    
    if report.violations:
        print(f"\nViolations:")
        for v in report.violations:
            print(f"  [{v.severity}] {v.violation_code}: {v.message}")
    
    print(f"\nEvidence saved to: {report.evidence_path}")
    print(f"Exit code: {report.exit_code}")
    
    sys.exit(report.exit_code)
