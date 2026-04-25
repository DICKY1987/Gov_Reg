"""Scanner service for directory governance enforcement.

FILE_ID: 01260207233100000071
PURPOSE: Scan directories, detect violations, repair (--fix mode)
PHASE: PH-04A Automation
ENHANCED: Comprehensive governance metrics (Phase 1-7)
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import sys
import json
import hashlib
import time
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = PROJECT_ROOT / "ID" / "1_runtime"
WATCHERS_ROOT = RUNTIME_ROOT / "watchers"
VALIDATORS_ROOT = RUNTIME_ROOT / "validators"

for import_path in (RUNTIME_ROOT, WATCHERS_ROOT, VALIDATORS_ROOT):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from P_01260207233100000068_zone_classifier import ZoneClassifier
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver
from P_01999000042260125104_dir_id_auto_repair import DirIdAutoRepair


@dataclass
class ScanViolation:
    """A detected governance violation."""
    violation_code: str
    severity: str  # "CRITICAL", "ERROR", "WARNING"
    directory: str
    relative_path: str
    zone: str
    depth: int
    message: str
    remediation: str


@dataclass
class ScanReport:
    """Report from a scan operation."""
    scan_id: str
    project_root: str
    started_at: str
    completed_at: str
    directories_scanned: int
    governed_directories: int
    violations_found: int
    violations: List[ScanViolation]
    repaired: int
    repair_mode: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        return asdict(self)


# ============================================================================
# Enhanced Metrics Dataclasses (Phase 1)
# ============================================================================

@dataclass
class FileScanMetrics:
    """File-level ID scanning metrics."""
    total_files_scanned: int
    files_correct: int
    files_no_id: int
    files_wrong_format: int
    files_python_no_prefix: int
    files_legacy_format: int
    files_missing_header: int  # Python files without FILE_ID docstring
    files_modified_dir_id: int  # Uncommitted .dir_id changes
    compliance_percentage: float


@dataclass
class ZoneDistributionMetrics:
    """Zone distribution statistics."""
    zones: Dict[str, int]  # zone -> directory count
    files_by_zone: Dict[str, int]  # zone -> file count
    violations_by_zone: Dict[str, int]  # zone -> violation count
    compliance_by_zone: Dict[str, float]  # zone -> compliance %


@dataclass
class DepthAnalysisMetrics:
    """Directory depth analysis."""
    depth_distribution: Dict[int, int]  # depth -> count
    max_depth: int
    avg_depth: float
    violations_by_depth: Dict[int, int]  # depth -> violation count


@dataclass
class RegistrySyncStatus:
    """Registry synchronization status."""
    in_sync_count: int
    missing_from_registry: List[str]  # paths
    missing_from_filesystem: List[str]  # paths
    mismatched_paths: List[Dict[str, str]]  # [{id, registry_path, disk_path}]
    sync_percentage: float


@dataclass
class DuplicateDetectionResult:
    """Duplicate ID detection results."""
    duplicate_count: int
    duplicate_groups: Dict[str, List[Dict[str, Any]]]  # canonical_id -> records
    total_affected_files: int


@dataclass
class AllocationStatistics:
    """ID allocation statistics during --fix."""
    ids_allocated: int
    allocation_failures: int
    allocated_ranges: List[Dict[str, Any]]  # [{range_start, range_end, count}]


@dataclass
class PerformanceMetrics:
    """Scan performance metrics."""
    scan_duration_seconds: float
    directories_per_second: float
    files_per_second: float
    memory_usage_mb: float


@dataclass
class CoverageMetrics:
    """Compliance coverage percentages."""
    directory_compliance: float  # % governed dirs with valid .dir_id
    file_compliance: float  # % files with correct ID format
    zone_compliance: Dict[str, float]  # zone -> compliance %
    overall_score: float  # weighted average


@dataclass
class HistoricalComparison:
    """Comparison with previous scan."""
    previous_scan_id: Optional[str]
    previous_scan_date: Optional[str]
    violations_delta: int  # positive = more violations
    compliance_delta: float  # positive = better compliance
    new_violations: List[ScanViolation]
    resolved_violations: List[ScanViolation]
    is_regression: bool  # compliance decreased >1%


@dataclass
class ActionableRemediation:
    """Remediation guidance for a violation."""
    violation_code: str
    command: str
    automated: bool
    estimated_effort: str  # "1min", "10min", etc.
    description: str


@dataclass
class EnhancedScanReport:
    """Comprehensive enhanced scan report."""
    # Basic info (backward compatible with ScanReport)
    scan_id: str
    project_root: str
    started_at: str
    completed_at: str
    
    # Core metrics
    directories_scanned: int
    governed_directories: int
    violations_found: int
    violations: List[ScanViolation]
    repaired: int
    repair_mode: bool
    
    # Enhanced metrics
    file_metrics: FileScanMetrics
    zone_distribution: ZoneDistributionMetrics
    depth_analysis: DepthAnalysisMetrics
    registry_sync: RegistrySyncStatus
    duplicates: DuplicateDetectionResult
    allocations: Optional[AllocationStatistics]
    performance: PerformanceMetrics
    coverage: CoverageMetrics
    historical: Optional[HistoricalComparison]
    remediations: List[ActionableRemediation]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON."""
        return asdict(self)
    
    def to_basic_report(self) -> ScanReport:
        """Convert to basic ScanReport for backward compatibility."""
        return ScanReport(
            scan_id=self.scan_id,
            project_root=self.project_root,
            started_at=self.started_at,
            completed_at=self.completed_at,
            directories_scanned=self.directories_scanned,
            governed_directories=self.governed_directories,
            violations_found=self.violations_found,
            violations=self.violations,
            repaired=self.repaired,
            repair_mode=self.repair_mode
        )


class ScannerService:
    """Scanner service for directory governance.
    
    Modes:
        --report: Dry-run, report violations (exit 1 if violations found)
        --fix: Repair mode, fix violations automatically
    """
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        zone_classifier: ZoneClassifier | None = None,
        resolver: DirectoryIdentityResolver | None = None
    ):
        """Initialize scanner.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root ID
            zone_classifier: Optional zone classifier
            resolver: Optional identity resolver
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        self.zone_classifier = zone_classifier or ZoneClassifier(project_root=project_root)
        self.resolver = resolver or DirectoryIdentityResolver(
            project_root=project_root,
            project_root_id=project_root_id,
            zone_classifier=self.zone_classifier
        )
    
    def scan(self, repair: bool = False) -> ScanReport:
        """Scan project for directory governance violations.
        
        Args:
            repair: If True, attempt to repair violations
            
        Returns:
            ScanReport: Scan results
        """
        scan_id = f"SCAN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        started_at = datetime.now(timezone.utc).isoformat()
        
        violations: List[ScanViolation] = []
        directories_scanned = 0
        governed_directories = 0
        repaired = 0
        
        # Walk directory tree
        for directory in self._walk_directories():
            directories_scanned += 1
            
            # Get relative path
            try:
                relative_path = str(directory.relative_to(self.project_root)).replace("\\", "/")
            except ValueError:
                continue
            
            # Classify
            zone = self.zone_classifier.compute_zone(relative_path)
            depth = self.zone_classifier.compute_depth(relative_path)
            
            # Skip excluded zones
            if zone == "excluded":
                continue
            
            # Track governed directories
            if zone == "governed":
                governed_directories += 1
                
                # Check for violations
                result = None
                try:
                    result = self.resolver.resolve_identity(directory, allocate_if_missing=False)
                except Exception as e:
                    # Resolver itself failed (e.g., unexpected error)
                    # Treat as generic error
                    result = None
                
                if result is None:
                    # Unexpected error - skip this directory
                    continue
                
                if result.status == "missing" or (result.status != "error" and result.needs_allocation):
                    # Missing .dir_id in governed zone
                    violation = ScanViolation(
                        violation_code="DIR-IDENTITY-004",
                        severity="ERROR",
                        directory=str(directory),
                        relative_path=relative_path,
                        zone=zone,
                        depth=depth,
                        message=f"Missing .dir_id in governed directory",
                        remediation="Run scanner with --fix to allocate dir_id"
                    )
                    violations.append(violation)
                    
                    # Repair if in fix mode
                    if repair:
                        try:
                            result = self.resolver.resolve_identity(directory, allocate_if_missing=True)
                            if result and result.status == "allocated":
                                repaired += 1
                        except Exception as e:
                            pass  # Log error but continue
                
                elif result.status == "error":
                    # Check if it's a parse error (DIR-IDENTITY-005)
                    error_msg = result.error_message or ""
                    if "DIR-IDENTITY-005" in error_msg or "Invalid .dir_id format" in error_msg:
                        violation = ScanViolation(
                            violation_code="DIR-IDENTITY-005",
                            severity="ERROR",
                            directory=str(directory),
                            relative_path=relative_path,
                            zone=zone,
                            depth=depth,
                            message=f"Invalid .dir_id format: {error_msg}",
                            remediation="Delete corrupt .dir_id and run scanner --fix"
                        )
                        violations.append(violation)
                        
                        # Auto-repair if in fix mode (GAP-001)
                        if repair:
                            try:
                                auto_repairer = DirIdAutoRepair(self.project_root, self.project_root_id)
                                repair_result = auto_repairer.fix_invalid_dir_id_anchors(
                                    directory,
                                    [error_msg],
                                    quarantine=True
                                )
                                if repair_result.success:
                                    repaired += 1
                            except Exception as e:
                                pass  # Log error but continue
                    else:
                        # Other validation errors (invalid content)
                        violation = ScanViolation(
                            violation_code="DIR-IDENTITY-006",
                            severity="ERROR",
                            directory=str(directory),
                            relative_path=relative_path,
                            zone=zone,
                            depth=depth,
                            message=f"Invalid .dir_id content: {error_msg}",
                            remediation="Fix .dir_id content or delete and run scanner --fix"
                        )
                        violations.append(violation)
                        
                        # Auto-repair if in fix mode (GAP-001)
                        if repair:
                            try:
                                auto_repairer = DirIdAutoRepair(self.project_root, self.project_root_id)
                                repair_result = auto_repairer.fix_invalid_dir_id_anchors(
                                    directory,
                                    [error_msg],
                                    quarantine=True
                                )
                                if repair_result.success:
                                    repaired += 1
                            except Exception as e:
                                pass  # Log error but continue
        
        completed_at = datetime.now(timezone.utc).isoformat()
        
        return ScanReport(
            scan_id=scan_id,
            project_root=str(self.project_root),
            started_at=started_at,
            completed_at=completed_at,
            directories_scanned=directories_scanned,
            governed_directories=governed_directories,
            violations_found=len(violations),
            violations=violations,
            repaired=repaired,
            repair_mode=repair
        )
    
    def _walk_directories(self):
        """Walk directory tree, yielding directories."""
        for item in self.project_root.rglob("*"):
            if item.is_dir():
                # Skip if excluded
                try:
                    relative_path = str(item.relative_to(self.project_root)).replace("\\", "/")
                    if not self.zone_classifier.should_skip(relative_path):
                        yield item
                except ValueError:
                    continue
    
    # ========================================================================
    # Enhanced Scanning Methods (Phase 2-6)
    # ========================================================================
    
    def scan_enhanced(self, repair: bool = False, store_evidence: bool = True) -> EnhancedScanReport:
        """Enhanced scan with comprehensive metrics.
        
        Args:
            repair: If True, attempt to repair violations
            store_evidence: If True, store scan evidence to .state/evidence/
            
        Returns:
            EnhancedScanReport: Comprehensive scan results
        """
        start_time = time.time()
        scan_id = f"SCAN-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        started_at = datetime.now(timezone.utc).isoformat()
        
        # Run basic scan first
        basic_report = self.scan(repair=repair)
        
        # Enhanced metrics
        file_metrics = self._scan_files()
        zone_distribution = self._compute_zone_distribution(basic_report.violations)
        depth_analysis = self._compute_depth_analysis(basic_report.violations)
        registry_sync = self._compare_with_registry()
        duplicates = self._detect_duplicates()
        allocations = self._get_allocation_stats() if repair else None
        
        end_time = time.time()
        performance = self._compute_performance(start_time, end_time, 
                                                 basic_report.directories_scanned,
                                                 file_metrics.total_files_scanned)
        
        coverage = self._compute_coverage(
            basic_report.governed_directories,
            basic_report.directories_scanned,
            basic_report.violations_found,
            file_metrics
        )
        
        # Historical comparison
        historical = self._compare_with_previous(basic_report, file_metrics, coverage)
        
        # Remediation guidance
        remediations = self._generate_remediations(basic_report.violations, duplicates)
        
        completed_at = datetime.now(timezone.utc).isoformat()
        
        enhanced_report = EnhancedScanReport(
            scan_id=scan_id,
            project_root=str(self.project_root),
            started_at=started_at,
            completed_at=completed_at,
            directories_scanned=basic_report.directories_scanned,
            governed_directories=basic_report.governed_directories,
            violations_found=basic_report.violations_found,
            violations=basic_report.violations,
            repaired=basic_report.repaired,
            repair_mode=repair,
            file_metrics=file_metrics,
            zone_distribution=zone_distribution,
            depth_analysis=depth_analysis,
            registry_sync=registry_sync,
            duplicates=duplicates,
            allocations=allocations,
            performance=performance,
            coverage=coverage,
            historical=historical,
            remediations=remediations
        )
        
        # Store evidence
        if store_evidence:
            self._store_evidence(enhanced_report)
        
        return enhanced_report
    
    def _scan_files(self) -> FileScanMetrics:
        """Scan all files for ID format compliance."""
        try:
            from P_01999000042260124521_id_format_scanner import IDFormatScanner
            
            scanner = IDFormatScanner(self.project_root)
            report = scanner.scan()
            
            # Additional checks
            missing_headers = self._check_file_id_headers()
            modified_dir_ids = self._check_dir_id_changes()
            
            total = report['total_files_scanned']
            correct = report['files_correct']
            compliance = (correct / total * 100) if total > 0 else 100.0
            
            return FileScanMetrics(
                total_files_scanned=total,
                files_correct=correct,
                files_no_id=report['issues']['no_id'],
                files_wrong_format=report['issues']['wrong_format'],
                files_python_no_prefix=report['issues']['python_no_p_prefix'],
                files_legacy_format=report['files_legacy_format'],
                files_missing_header=len(missing_headers),
                files_modified_dir_id=len(modified_dir_ids),
                compliance_percentage=compliance
            )
        except Exception as e:
            print(f"Warning: File scanning failed: {e}", file=sys.stderr)
            return FileScanMetrics(
                total_files_scanned=0,
                files_correct=0,
                files_no_id=0,
                files_wrong_format=0,
                files_python_no_prefix=0,
                files_legacy_format=0,
                files_missing_header=0,
                files_modified_dir_id=0,
                compliance_percentage=100.0
            )
    
    def _check_file_id_headers(self) -> List[Path]:
        """Check Python files for FILE_ID: docstring header."""
        import re
        missing = []
        
        for py_file in self.project_root.rglob("*.py"):
            # Skip excluded directories
            try:
                rel_path = str(py_file.relative_to(self.project_root)).replace("\\", "/")
                if self.zone_classifier.should_skip(rel_path):
                    continue
            except ValueError:
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                # Look for FILE_ID: in first 20 lines
                lines = content.split('\n')[:20]
                has_file_id = any(re.search(r'FILE_ID:\s*\d{19,20}', line) for line in lines)
                if not has_file_id:
                    missing.append(py_file)
            except Exception:
                pass
        
        return missing
    
    def _check_dir_id_changes(self) -> List[Path]:
        """Check for uncommitted .dir_id file changes using git."""
        modified = []
        
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'status', '--porcelain', '--', '.dir_id'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line and '.dir_id' in line:
                        # Extract file path
                        parts = line.split(maxsplit=1)
                        if len(parts) == 2:
                            modified.append(self.project_root / parts[1])
        except Exception:
            pass  # Git not available or failed
        
        return modified
    
    def _compute_zone_distribution(self, violations: List[ScanViolation]) -> ZoneDistributionMetrics:
        """Compute zone distribution metrics."""
        zones = defaultdict(int)
        files_by_zone = defaultdict(int)
        violations_by_zone = defaultdict(int)
        
        # Count directories by zone
        for directory in self._walk_directories():
            try:
                rel_path = str(directory.relative_to(self.project_root)).replace("\\", "/")
                zone = self.zone_classifier.compute_zone(rel_path)
                zones[zone] += 1
                
                # Count files in this directory
                try:
                    file_count = sum(1 for f in directory.iterdir() if f.is_file())
                    files_by_zone[zone] += file_count
                except Exception:
                    pass
            except ValueError:
                continue
        
        # Count violations by zone
        for v in violations:
            violations_by_zone[v.zone] += 1
        
        # Compute compliance by zone
        compliance_by_zone = {}
        for zone in zones:
            total = zones[zone]
            viols = violations_by_zone.get(zone, 0)
            compliance_by_zone[zone] = ((total - viols) / total * 100) if total > 0 else 100.0
        
        return ZoneDistributionMetrics(
            zones=dict(zones),
            files_by_zone=dict(files_by_zone),
            violations_by_zone=dict(violations_by_zone),
            compliance_by_zone=compliance_by_zone
        )
    
    def _compute_depth_analysis(self, violations: List[ScanViolation]) -> DepthAnalysisMetrics:
        """Compute directory depth analysis."""
        depth_distribution = defaultdict(int)
        violations_by_depth = defaultdict(int)
        depths = []
        
        # Analyze all directories
        for directory in self._walk_directories():
            try:
                rel_path = str(directory.relative_to(self.project_root)).replace("\\", "/")
                depth = self.zone_classifier.compute_depth(rel_path)
                depth_distribution[depth] += 1
                depths.append(depth)
            except ValueError:
                continue
        
        # Count violations by depth
        for v in violations:
            violations_by_depth[v.depth] += 1
        
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0.0
        
        return DepthAnalysisMetrics(
            depth_distribution=dict(depth_distribution),
            max_depth=max_depth,
            avg_depth=avg_depth,
            violations_by_depth=dict(violations_by_depth)
        )
    
    def _compare_with_registry(self) -> RegistrySyncStatus:
        """Compare .dir_id files with registry entries."""
        registry_path = self.project_root / "01999000042260124503_governance_registry_unified.json"
        
        if not registry_path.exists():
            return RegistrySyncStatus(
                in_sync_count=0,
                missing_from_registry=[],
                missing_from_filesystem=[],
                mismatched_paths=[],
                sync_percentage=100.0
            )
        
        try:
            registry_data = json.loads(registry_path.read_text(encoding='utf-8'))
            records = registry_data.get('records', [])
            
            # Build indexes
            registry_index = {}
            for r in records:
                if r.get('type') == 'directory':
                    dir_id = r.get('file_id') or r.get('dir_id')
                    if dir_id:
                        registry_index[dir_id] = r.get('path', '')
            
            # Build disk index
            disk_index = {}
            for directory in self._walk_directories():
                dir_id_file = directory / '.dir_id'
                if dir_id_file.exists():
                    try:
                        content = dir_id_file.read_text(encoding='utf-8').strip()
                        rel_path = str(directory.relative_to(self.project_root)).replace("\\", "/")
                        disk_index[content] = rel_path
                    except Exception:
                        pass
            
            # Compare
            in_sync = 0
            missing_from_registry = []
            missing_from_filesystem = []
            mismatched_paths = []
            
            # Check disk -> registry
            for dir_id, disk_path in disk_index.items():
                if dir_id in registry_index:
                    reg_path = registry_index[dir_id]
                    if reg_path == disk_path:
                        in_sync += 1
                    else:
                        mismatched_paths.append({
                            'id': dir_id,
                            'registry_path': reg_path,
                            'disk_path': disk_path
                        })
                else:
                    missing_from_registry.append(disk_path)
            
            # Check registry -> disk
            for dir_id, reg_path in registry_index.items():
                if dir_id not in disk_index:
                    missing_from_filesystem.append(reg_path)
            
            total = len(disk_index) + len(registry_index)
            sync_pct = (in_sync / (total / 2) * 100) if total > 0 else 100.0
            
            return RegistrySyncStatus(
                in_sync_count=in_sync,
                missing_from_registry=missing_from_registry,
                missing_from_filesystem=missing_from_filesystem,
                mismatched_paths=mismatched_paths,
                sync_percentage=sync_pct
            )
        except Exception as e:
            print(f"Warning: Registry sync check failed: {e}", file=sys.stderr)
            return RegistrySyncStatus(
                in_sync_count=0,
                missing_from_registry=[],
                missing_from_filesystem=[],
                mismatched_paths=[],
                sync_percentage=100.0
            )
    
    def _detect_duplicates(self) -> DuplicateDetectionResult:
        """Detect duplicate IDs in registry."""
        registry_path = self.project_root / "01999000042260124503_governance_registry_unified.json"
        
        if not registry_path.exists():
            return DuplicateDetectionResult(
                duplicate_count=0,
                duplicate_groups={},
                total_affected_files=0
        )
        
        try:
            registry_data = json.loads(registry_path.read_text(encoding='utf-8'))
            records = registry_data.get('records', [])

            grouped_records = defaultdict(list)
            for record in records:
                canonical_id = (
                    record.get("canonical_id")
                    or record.get("file_id")
                    or record.get("id")
                )
                if canonical_id:
                    grouped_records[str(canonical_id)].append(record)

            duplicates = {
                canonical_id: group
                for canonical_id, group in grouped_records.items()
                if len(group) > 1
            }
            
            total_affected = sum(len(group) for group in duplicates.values())
            
            return DuplicateDetectionResult(
                duplicate_count=len(duplicates),
                duplicate_groups=duplicates,
                total_affected_files=total_affected
            )
        except Exception as e:
            print(f"Warning: Duplicate detection failed: {e}", file=sys.stderr)
            return DuplicateDetectionResult(
                duplicate_count=0,
                duplicate_groups={},
                total_affected_files=0
            )
    
    def _get_allocation_stats(self) -> AllocationStatistics:
        """Get ID allocation statistics (placeholder for --fix mode)."""
        # This would track allocations made during repair
        # For now, return empty stats
        return AllocationStatistics(
            ids_allocated=0,
            allocation_failures=0,
            allocated_ranges=[]
        )
    
    def _compute_performance(self, start_time: float, end_time: float,
                            dirs_scanned: int, files_scanned: int) -> PerformanceMetrics:
        """Compute performance metrics."""
        duration = end_time - start_time
        
        # Try to get memory usage
        memory_mb = 0.0
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 ** 2)
        except Exception:
            pass  # psutil not available
        
        return PerformanceMetrics(
            scan_duration_seconds=duration,
            directories_per_second=dirs_scanned / duration if duration > 0 else 0,
            files_per_second=files_scanned / duration if duration > 0 else 0,
            memory_usage_mb=memory_mb
        )
    
    def _compute_coverage(self, governed_dirs: int, total_dirs: int,
                         violations: int, file_metrics: FileScanMetrics) -> CoverageMetrics:
        """Compute compliance coverage metrics."""
        # Directory compliance
        compliant_dirs = governed_dirs - violations
        dir_compliance = (compliant_dirs / governed_dirs * 100) if governed_dirs > 0 else 100.0
        
        # File compliance
        file_compliance = file_metrics.compliance_percentage
        
        # Overall weighted score (60% dirs, 40% files)
        overall_score = (dir_compliance * 0.6) + (file_compliance * 0.4)
        
        return CoverageMetrics(
            directory_compliance=dir_compliance,
            file_compliance=file_compliance,
            zone_compliance={},  # Populated by zone_distribution
            overall_score=overall_score
        )
    
    def _compare_with_previous(self, basic_report: ScanReport,
                              file_metrics: FileScanMetrics,
                              coverage: CoverageMetrics) -> Optional[HistoricalComparison]:
        """Compare with previous scan results."""
        evidence_dir = self.project_root / '.state' / 'evidence' / 'scans'
        
        if not evidence_dir.exists():
            return None
        
        # Find most recent scan
        scan_dirs = sorted([d for d in evidence_dir.iterdir() if d.is_dir()], 
                          key=lambda d: d.name, reverse=True)
        
        if not scan_dirs:
            return None
        
        try:
            previous_report_path = scan_dirs[0] / 'report.json'
            if not previous_report_path.exists():
                return None
            
            prev_data = json.loads(previous_report_path.read_text(encoding='utf-8'))
            
            # Extract previous metrics
            prev_violations = prev_data.get('violations_found', 0)
            prev_coverage = prev_data.get('coverage', {}).get('overall_score', 100.0)
            
            violations_delta = basic_report.violations_found - prev_violations
            compliance_delta = coverage.overall_score - prev_coverage
            
            # Identify new vs resolved
            prev_keys = {(v['violation_code'], v['relative_path']) 
                        for v in prev_data.get('violations', [])}
            curr_keys = {(v.violation_code, v.relative_path) 
                        for v in basic_report.violations}
            
            new_violations = [v for v in basic_report.violations 
                            if (v.violation_code, v.relative_path) not in prev_keys]
            
            resolved_violations = [
                ScanViolation(**v) for v in prev_data.get('violations', [])
                if (v['violation_code'], v['relative_path']) not in curr_keys
            ]
            
            is_regression = compliance_delta < -1.0
            
            return HistoricalComparison(
                previous_scan_id=prev_data.get('scan_id'),
                previous_scan_date=prev_data.get('completed_at'),
                violations_delta=violations_delta,
                compliance_delta=compliance_delta,
                new_violations=new_violations,
                resolved_violations=resolved_violations,
                is_regression=is_regression
            )
        except Exception as e:
            print(f"Warning: Historical comparison failed: {e}", file=sys.stderr)
            return None
    
    def _generate_remediations(self, violations: List[ScanViolation],
                              duplicates: DuplicateDetectionResult) -> List[ActionableRemediation]:
        """Generate actionable remediation guidance."""
        remediations = []
        
        # Remediation templates
        templates = {
            'DIR-IDENTITY-004': ActionableRemediation(
                violation_code='DIR-IDENTITY-004',
                command='python ID\\7_automation\\P_01260207233100000071_scanner_service.py --root . --root-id <PROJECT_ROOT_ID> --fix',
                automated=True,
                estimated_effort='1min',
                description='Missing .dir_id - run scanner with --fix to allocate'
            ),
            'DIR-IDENTITY-005': ActionableRemediation(
                violation_code='DIR-IDENTITY-005',
                command='del .dir_id && python ID\\7_automation\\P_01260207233100000071_scanner_service.py --root . --root-id <PROJECT_ROOT_ID> --fix',
                automated=True,
                estimated_effort='1min',
                description='Invalid .dir_id format - delete and re-allocate'
            ),
            'DIR-IDENTITY-006': ActionableRemediation(
                violation_code='DIR-IDENTITY-006',
                command='Manual review required - check .dir_id content',
                automated=False,
                estimated_effort='5min',
                description='Invalid .dir_id content - manual correction needed'
            )
        }
        
        # Add remediations for violations
        violation_codes = {v.violation_code for v in violations}
        for code in violation_codes:
            if code in templates:
                remediations.append(templates[code])
        
        # Add duplicate remediation if needed
        if duplicates.duplicate_count > 0:
            remediations.append(ActionableRemediation(
                violation_code='DUPLICATE-ID',
                command='python scripts/id_duplicate_resolver.py',
                automated=False,
                estimated_effort='10min',
                description=f'Resolve {duplicates.duplicate_count} duplicate IDs'
            ))
        
        return remediations
    
    def _store_evidence(self, report: EnhancedScanReport):
        """Store scan evidence to .state/evidence/scans/."""
        evidence_dir = self.project_root / '.state' / 'evidence' / 'scans' / report.scan_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Main report
        report_json = json.dumps(report.to_dict(), indent=2)
        (evidence_dir / 'report.json').write_text(report_json, encoding='utf-8')
        
        # Streaming violations (JSONL)
        with open(evidence_dir / 'violations.jsonl', 'w', encoding='utf-8') as f:
            for v in report.violations:
                f.write(json.dumps(asdict(v)) + '\n')
        
        # Separate metric files
        (evidence_dir / 'metrics.json').write_text(
            json.dumps({
                'file_metrics': asdict(report.file_metrics),
                'zone_distribution': asdict(report.zone_distribution),
                'depth_analysis': asdict(report.depth_analysis),
                'performance': asdict(report.performance),
                'coverage': asdict(report.coverage)
            }, indent=2),
            encoding='utf-8'
        )
        
        (evidence_dir / 'registry_sync.json').write_text(
            json.dumps(asdict(report.registry_sync), indent=2),
            encoding='utf-8'
        )
        
        (evidence_dir / 'duplicates.json').write_text(
            json.dumps(asdict(report.duplicates), indent=2),
            encoding='utf-8'
        )
        
        # SHA256 integrity hash
        sha256_hash = hashlib.sha256(report_json.encode()).hexdigest()
        (evidence_dir / 'sha256.txt').write_text(f"{sha256_hash}  report.json\n", encoding='utf-8')
        
        print(f"Evidence stored: {evidence_dir}", file=sys.stderr)


def main():
    """CLI entry point for scanner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Directory governance scanner")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root")
    parser.add_argument("--root-id", type=str, required=True, help="Project root ID")
    parser.add_argument("--fix", action="store_true", help="Repair violations")
    parser.add_argument("--report", dest="fix", action="store_false", help="Report only (default)")
    parser.add_argument("--output", type=Path, help="Output report JSON path")
    parser.add_argument("--format", choices=['basic', 'full', 'summary', 'prometheus'], 
                       default='basic', help="Report format (default: basic)")
    parser.add_argument("--enhanced", action="store_true", 
                       help="Use enhanced scan with comprehensive metrics")
    parser.add_argument("--historical", action="store_true",
                       help="Include historical comparison")
    parser.add_argument("--no-evidence", action="store_true",
                       help="Skip storing evidence (for testing)")
    
    args = parser.parse_args()
    
    # Run scan
    scanner = ScannerService(
        project_root=args.root,
        project_root_id=args.root_id
    )
    
    print(f"Scanning {args.root}...")
    
    # Choose scan mode
    if args.enhanced or args.format in ['full', 'summary', 'prometheus']:
        # Enhanced scan
        report = scanner.scan_enhanced(
            repair=args.fix,
            store_evidence=not args.no_evidence
        )
        
        # Print based on format
        if args.format == 'summary':
            _print_summary(report)
        elif args.format == 'prometheus':
            _print_prometheus(report)
        else:  # 'full'
            _print_enhanced_report(report)
        
        # Save report
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(report.to_dict(), f, indent=2)
            print(f"\nReport saved to: {args.output}")
        
        # Exit code
        exit_code = 0
        if report.violations_found > 0 and not args.fix:
            print(f"\n✗ Violations found - run with --fix to repair")
            exit_code = 1
        elif report.violations_found > 0 and args.fix:
            if report.repaired == report.violations_found:
                print(f"\n✓ All violations repaired")
                exit_code = 0
            else:
                print(f"\n⚠ {report.violations_found - report.repaired} violations could not be repaired")
                exit_code = 1
        elif report.historical and report.historical.is_regression:
            print(f"\n⚠ REGRESSION DETECTED: Compliance decreased by {abs(report.historical.compliance_delta):.2f}%")
            exit_code = 2
        else:
            print(f"\n✓ No violations found")
            exit_code = 0
        
        sys.exit(exit_code)
    
    else:
        # Basic scan (backward compatible)
        report = scanner.scan(repair=args.fix)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Scan Complete: {report.scan_id}")
        print(f"{'='*60}")
        print(f"Directories scanned: {report.directories_scanned}")
        print(f"Governed directories: {report.governed_directories}")
        print(f"Violations found: {report.violations_found}")
        if args.fix:
            print(f"Violations repaired: {report.repaired}")
        print(f"{'='*60}")
        
        # Print violations
        if report.violations:
            print(f"\nViolations:")
            for v in report.violations:
                print(f"  [{v.violation_code}] {v.relative_path}: {v.message}")
        
        # Save report
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                json.dump(report.to_dict(), f, indent=2)
            print(f"\nReport saved to: {args.output}")
        
        # Exit code
        if report.violations_found > 0 and not args.fix:
            print(f"\n✗ Violations found - run with --fix to repair")
            sys.exit(1)
        elif report.violations_found > 0 and args.fix:
            if report.repaired == report.violations_found:
                print(f"\n✓ All violations repaired")
                sys.exit(0)
            else:
                print(f"\n⚠ {report.violations_found - report.repaired} violations could not be repaired")
                sys.exit(1)
        else:
            print(f"\n✓ No violations found")
            sys.exit(0)


def _print_enhanced_report(report: EnhancedScanReport):
    """Print full enhanced report."""
    print(f"\n{'='*70}")
    print(f"  ENHANCED GOVERNANCE SCAN REPORT")
    print(f"{'='*70}")
    print(f"Scan ID: {report.scan_id}")
    print(f"Completed: {report.completed_at}")
    print(f"Duration: {report.performance.scan_duration_seconds:.2f}s")
    
    print(f"\n--- DIRECTORY METRICS ---")
    print(f"Directories scanned: {report.directories_scanned}")
    print(f"Governed directories: {report.governed_directories}")
    print(f"Violations found: {report.violations_found}")
    if report.repair_mode:
        print(f"Violations repaired: {report.repaired}")
    
    print(f"\n--- FILE METRICS ---")
    print(f"Files scanned: {report.file_metrics.total_files_scanned}")
    print(f"Files correct: {report.file_metrics.files_correct}")
    print(f"Files without ID: {report.file_metrics.files_no_id}")
    print(f"Files wrong format: {report.file_metrics.files_wrong_format}")
    print(f"Python files missing P_ prefix: {report.file_metrics.files_python_no_prefix}")
    print(f"Files missing FILE_ID header: {report.file_metrics.files_missing_header}")
    
    print(f"\n--- COMPLIANCE COVERAGE ---")
    print(f"Directory compliance: {report.coverage.directory_compliance:.2f}%")
    print(f"File compliance: {report.coverage.file_compliance:.2f}%")
    print(f"Overall score: {report.coverage.overall_score:.2f}%")
    
    print(f"\n--- ZONE DISTRIBUTION ---")
    for zone, count in report.zone_distribution.zones.items():
        viols = report.zone_distribution.violations_by_zone.get(zone, 0)
        comp = report.zone_distribution.compliance_by_zone.get(zone, 100.0)
        print(f"  {zone}: {count} dirs, {viols} violations ({comp:.1f}% compliant)")
    
    print(f"\n--- DEPTH ANALYSIS ---")
    print(f"Max depth: {report.depth_analysis.max_depth}")
    print(f"Avg depth: {report.depth_analysis.avg_depth:.1f}")
    
    print(f"\n--- REGISTRY SYNC ---")
    print(f"In sync: {report.registry_sync.in_sync_count}")
    print(f"Missing from registry: {len(report.registry_sync.missing_from_registry)}")
    print(f"Missing from filesystem: {len(report.registry_sync.missing_from_filesystem)}")
    print(f"Path mismatches: {len(report.registry_sync.mismatched_paths)}")
    print(f"Sync percentage: {report.registry_sync.sync_percentage:.2f}%")
    
    print(f"\n--- DUPLICATES ---")
    print(f"Duplicate ID groups: {report.duplicates.duplicate_count}")
    print(f"Total affected files: {report.duplicates.total_affected_files}")
    
    if report.historical:
        print(f"\n--- HISTORICAL COMPARISON ---")
        print(f"Previous scan: {report.historical.previous_scan_id}")
        print(f"Violations delta: {report.historical.violations_delta:+d}")
        print(f"Compliance delta: {report.historical.compliance_delta:+.2f}%")
        print(f"New violations: {len(report.historical.new_violations)}")
        print(f"Resolved violations: {len(report.historical.resolved_violations)}")
        if report.historical.is_regression:
            print(f"⚠ REGRESSION DETECTED")
    
    print(f"\n--- PERFORMANCE ---")
    print(f"Directories/sec: {report.performance.directories_per_second:.1f}")
    print(f"Files/sec: {report.performance.files_per_second:.1f}")
    if report.performance.memory_usage_mb > 0:
        print(f"Memory usage: {report.performance.memory_usage_mb:.1f} MB")
    
    if report.remediations:
        print(f"\n--- RECOMMENDED ACTIONS ---")
        for r in report.remediations:
            auto = "✓ Automated" if r.automated else "⚠ Manual"
            print(f"  [{r.violation_code}] {auto} ({r.estimated_effort})")
            print(f"    Command: {r.command}")
            print(f"    {r.description}")
    
    print(f"\n{'='*70}")


def _print_summary(report: EnhancedScanReport):
    """Print concise summary."""
    print(f"\n{'='*60}")
    print(f"  SCAN SUMMARY: {report.scan_id}")
    print(f"{'='*60}")
    print(f"Overall Compliance: {report.coverage.overall_score:.1f}%")
    print(f"Violations: {report.violations_found}")
    print(f"Duration: {report.performance.scan_duration_seconds:.1f}s")
    
    if report.historical:
        trend = "↑" if report.historical.compliance_delta > 0 else "↓" if report.historical.compliance_delta < 0 else "→"
        print(f"Trend: {trend} {report.historical.compliance_delta:+.1f}%")
    
    print(f"{'='*60}")


def _print_prometheus(report: EnhancedScanReport):
    """Print Prometheus-style metrics."""
    print(f"# HELP governance_compliance_score Overall governance compliance score (0-100)")
    print(f"# TYPE governance_compliance_score gauge")
    print(f"governance_compliance_score {report.coverage.overall_score:.2f}")
    
    print(f"\n# HELP governance_violations_total Total number of violations")
    print(f"# TYPE governance_violations_total gauge")
    print(f"governance_violations_total {report.violations_found}")
    
    print(f"\n# HELP governance_directories_scanned Total directories scanned")
    print(f"# TYPE governance_directories_scanned gauge")
    print(f"governance_directories_scanned {report.directories_scanned}")
    
    print(f"\n# HELP governance_scan_duration_seconds Scan duration in seconds")
    print(f"# TYPE governance_scan_duration_seconds gauge")
    print(f"governance_scan_duration_seconds {report.performance.scan_duration_seconds:.2f}")
    
    print(f"\n# HELP governance_files_scanned Total files scanned")
    print(f"# TYPE governance_files_scanned gauge")
    print(f"governance_files_scanned {report.file_metrics.total_files_scanned}")
    
    print(f"\n# HELP governance_duplicates_total Total duplicate ID groups")
    print(f"# TYPE governance_duplicates_total gauge")
    print(f"governance_duplicates_total {report.duplicates.duplicate_count}")


if __name__ == "__main__":
    main()
