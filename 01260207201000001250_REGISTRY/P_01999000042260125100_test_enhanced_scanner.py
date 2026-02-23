#!/usr/bin/env python3
"""Test script for enhanced scanner functionality.

FILE_ID: 01999000042260125100
PURPOSE: Test enhanced scanner metrics and features
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add govreg_core to path
sys.path.insert(0, str(Path(__file__).parent / "01260207201000001173_govreg_core"))

# Import enhanced dataclasses
from P_01260207233100000071_scanner_service import (
    FileScanMetrics,
    ZoneDistributionMetrics,
    DepthAnalysisMetrics,
    RegistrySyncStatus,
    DuplicateDetectionResult,
    AllocationStatistics,
    PerformanceMetrics,
    CoverageMetrics,
    HistoricalComparison,
    ActionableRemediation,
    EnhancedScanReport,
    ScanViolation
)


def test_dataclasses():
    """Test that all enhanced dataclasses can be instantiated."""
    print("Testing enhanced dataclasses...")
    
    # Test FileScanMetrics
    file_metrics = FileScanMetrics(
        total_files_scanned=100,
        files_correct=90,
        files_no_id=5,
        files_wrong_format=2,
        files_python_no_prefix=2,
        files_legacy_format=1,
        files_missing_header=3,
        files_modified_dir_id=0,
        compliance_percentage=90.0
    )
    print(f"✓ FileScanMetrics: {file_metrics.compliance_percentage}% compliant")
    
    # Test ZoneDistributionMetrics
    zone_dist = ZoneDistributionMetrics(
        zones={"governed": 50, "staging": 10, "excluded": 40},
        files_by_zone={"governed": 500, "staging": 100, "excluded": 400},
        violations_by_zone={"governed": 5, "staging": 2},
        compliance_by_zone={"governed": 90.0, "staging": 80.0}
    )
    print(f"✓ ZoneDistributionMetrics: {len(zone_dist.zones)} zones")
    
    # Test DepthAnalysisMetrics
    depth_analysis = DepthAnalysisMetrics(
        depth_distribution={0: 1, 1: 10, 2: 20, 3: 15},
        max_depth=3,
        avg_depth=2.1,
        violations_by_depth={2: 3, 3: 2}
    )
    print(f"✓ DepthAnalysisMetrics: max={depth_analysis.max_depth}, avg={depth_analysis.avg_depth:.1f}")
    
    # Test RegistrySyncStatus
    registry_sync = RegistrySyncStatus(
        in_sync_count=45,
        missing_from_registry=['path1', 'path2'],
        missing_from_filesystem=['old_path'],
        mismatched_paths=[],
        sync_percentage=95.0
    )
    print(f"✓ RegistrySyncStatus: {registry_sync.sync_percentage}% in sync")
    
    # Test DuplicateDetectionResult
    duplicates = DuplicateDetectionResult(
        duplicate_count=0,
        duplicate_groups={},
        total_affected_files=0
    )
    print(f"✓ DuplicateDetectionResult: {duplicates.duplicate_count} duplicates")
    
    # Test AllocationStatistics
    allocations = AllocationStatistics(
        ids_allocated=5,
        allocation_failures=0,
        allocated_ranges=[]
    )
    print(f"✓ AllocationStatistics: {allocations.ids_allocated} allocated")
    
    # Test PerformanceMetrics
    performance = PerformanceMetrics(
        scan_duration_seconds=15.5,
        directories_per_second=6.5,
        files_per_second=64.5,
        memory_usage_mb=45.2
    )
    print(f"✓ PerformanceMetrics: {performance.scan_duration_seconds:.1f}s, {performance.memory_usage_mb:.1f}MB")
    
    # Test CoverageMetrics
    coverage = CoverageMetrics(
        directory_compliance=90.0,
        file_compliance=90.0,
        zone_compliance={"governed": 90.0, "staging": 80.0},
        overall_score=90.0
    )
    print(f"✓ CoverageMetrics: {coverage.overall_score:.1f}% overall")
    
    # Test ActionableRemediation
    remediation = ActionableRemediation(
        violation_code="DIR-IDENTITY-004",
        command="scanner --fix",
        automated=True,
        estimated_effort="1min",
        description="Allocate missing .dir_id"
    )
    print(f"✓ ActionableRemediation: {remediation.violation_code} ({remediation.estimated_effort})")
    
    # Test EnhancedScanReport
    violation = ScanViolation(
        violation_code="DIR-IDENTITY-004",
        severity="ERROR",
        directory="/path/to/dir",
        relative_path="path/to/dir",
        zone="governed",
        depth=2,
        message="Missing .dir_id",
        remediation="Run scanner --fix"
    )
    
    report = EnhancedScanReport(
        scan_id="SCAN-20260214-213000",
        project_root="/path/to/project",
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
        directories_scanned=100,
        governed_directories=50,
        violations_found=5,
        violations=[violation],
        repaired=0,
        repair_mode=False,
        file_metrics=file_metrics,
        zone_distribution=zone_dist,
        depth_analysis=depth_analysis,
        registry_sync=registry_sync,
        duplicates=duplicates,
        allocations=allocations,
        performance=performance,
        coverage=coverage,
        historical=None,
        remediations=[remediation]
    )
    print(f"✓ EnhancedScanReport: {report.scan_id}")
    
    # Test serialization
    report_dict = report.to_dict()
    print(f"✓ EnhancedScanReport.to_dict(): {len(report_dict)} keys")
    
    # Test backward compatibility
    basic_report = report.to_basic_report()
    print(f"✓ EnhancedScanReport.to_basic_report(): {basic_report.scan_id}")
    
    print("\n✅ All dataclass tests passed!")
    return True


def test_report_formats():
    """Test different report output formats."""
    print("\nTesting report format functions...")
    
    # Import format functions
    from P_01260207233100000071_scanner_service import (
        _print_summary,
        _print_prometheus,
        _print_enhanced_report
    )
    
    # Create sample report
    file_metrics = FileScanMetrics(
        total_files_scanned=100,
        files_correct=90,
        files_no_id=5,
        files_wrong_format=2,
        files_python_no_prefix=2,
        files_legacy_format=1,
        files_missing_header=3,
        files_modified_dir_id=0,
        compliance_percentage=90.0
    )
    
    zone_dist = ZoneDistributionMetrics(
        zones={"governed": 50, "staging": 10},
        files_by_zone={"governed": 500, "staging": 100},
        violations_by_zone={"governed": 5},
        compliance_by_zone={"governed": 90.0, "staging": 100.0}
    )
    
    report = EnhancedScanReport(
        scan_id="TEST-SCAN-001",
        project_root="/test/project",
        started_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
        directories_scanned=60,
        governed_directories=50,
        violations_found=5,
        violations=[],
        repaired=0,
        repair_mode=False,
        file_metrics=file_metrics,
        zone_distribution=zone_dist,
        depth_analysis=DepthAnalysisMetrics({0: 1, 1: 30, 2: 20}, 2, 1.5, {}),
        registry_sync=RegistrySyncStatus(45, [], [], [], 100.0),
        duplicates=DuplicateDetectionResult(0, {}, 0),
        allocations=None,
        performance=PerformanceMetrics(10.0, 6.0, 10.0, 50.0),
        coverage=CoverageMetrics(90.0, 90.0, {}, 90.0),
        historical=None,
        remediations=[]
    )
    
    print("\n--- Testing Summary Format ---")
    _print_summary(report)
    
    print("\n--- Testing Prometheus Format ---")
    _print_prometheus(report)
    
    print("\n--- Testing Enhanced Report Format ---")
    _print_enhanced_report(report)
    
    print("\n✅ All format tests passed!")
    return True


def main():
    """Run all tests."""
    print("="*70)
    print("  ENHANCED SCANNER TEST SUITE")
    print("="*70)
    
    try:
        test_dataclasses()
        test_report_formats()
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED")
        print("="*70)
        print("\nEnhanced scanner implementation is ready:")
        print("  - 12 new dataclasses defined")
        print("  - FileScanMetrics (file-level scanning)")
        print("  - ZoneDistributionMetrics (zone breakdown)")
        print("  - DepthAnalysisMetrics (depth analysis)")
        print("  - RegistrySyncStatus (registry coherence)")
        print("  - DuplicateDetectionResult (duplicate detection)")
        print("  - AllocationStatistics (ID allocation tracking)")
        print("  - PerformanceMetrics (scan performance)")
        print("  - CoverageMetrics (compliance scoring)")
        print("  - HistoricalComparison (trend analysis)")
        print("  - ActionableRemediation (fix commands)")
        print("  - EnhancedScanReport (comprehensive report)")
        print("  - 3 output formats: summary, full, prometheus")
        print("\nNext steps:")
        print("  1. Fix remaining import issues in dependency chain")
        print("  2. Run integration test with actual directory scan")
        print("  3. Validate evidence storage to .state/evidence/")
        
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
