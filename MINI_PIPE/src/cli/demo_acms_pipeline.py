#!/usr/bin/env python3
"""
ACMS Pipeline Demonstration Script

Demonstrates the complete ACMS pipeline using the example gap report.
Shows gap discovery, clustering, planning, and execution plan generation.
"""

import json
from pathlib import Path
from src.acms.gap_registry import GapRegistry, GapStatus
from src.acms.execution_planner import ExecutionPlanner
from src.acms.phase_plan_compiler import PhasePlanCompiler


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demonstrate_gap_registry():
    """Demonstrate gap registry capabilities"""
    print_section("PHASE 1: Gap Discovery & Registry")

    # Load example gap report
    registry = GapRegistry()
    count = registry.load_from_report(
        Path(__file__).parent.parent.parent
        / "docs"
        / "analysis_frameworks"
        / "example_gap_report.json"
    )
    print(f"✓ Loaded {count} gaps from example_gap_report.json\n")

    # Show statistics
    stats = registry.get_stats()
    print(f"Gap Statistics:")
    print(f"  Total gaps: {stats['total']}")
    print(f"  By severity:")
    for severity, count in stats["by_severity"].items():
        if count > 0:
            print(f"    - {severity}: {count}")

    print(f"\n  Unresolved: {stats['unresolved']}")

    # Show sample gaps
    print(f"\nSample Gaps:")
    for gap in list(registry.gaps.values())[:3]:
        print(f"  • {gap.gap_id}: {gap.title}")
        print(f"    Severity: {gap.severity.value}, Category: {gap.category}")
        print(f"    Files: {len(gap.file_paths)}")

    return registry


def demonstrate_clustering(registry: GapRegistry):
    """Demonstrate workstream clustering"""
    print_section("PHASE 2: Gap Clustering into Workstreams")

    planner = ExecutionPlanner(registry)
    workstreams = planner.cluster_gaps(max_files_per_workstream=5, category_based=True)

    print(f"✓ Created {len(workstreams)} workstreams\n")

    # Show prioritized workstreams
    print("Workstreams (by priority):")
    for ws in planner.get_prioritized_workstreams():
        print(f"\n  {ws.workstream_id}: {ws.name}")
        print(f"    Priority score: {ws.priority_score:.1f}")
        print(f"    Gaps: {len(ws.gap_ids)}")
        print(f"    Files in scope: {len(ws.file_scope)}")
        print(f"    Estimated effort: {ws.estimated_effort}")
        if ws.dependencies:
            print(f"    Dependencies: {', '.join(ws.dependencies)}")

    return planner


def demonstrate_plan_compilation(planner: ExecutionPlanner):
    """Demonstrate execution plan compilation"""
    print_section("PHASE 3: Execution Plan Generation")

    workstreams = planner.get_prioritized_workstreams()
    compiler = PhasePlanCompiler()

    plan = compiler.compile_from_workstreams(workstreams, repo_root=Path("."))

    print(f"✓ Generated execution plan: {plan.plan_id}")
    print(f"✓ Total tasks: {len(plan.tasks)}\n")

    # Task breakdown
    task_kinds = {}
    for task in plan.tasks:
        task_kinds[task.task_kind] = task_kinds.get(task.task_kind, 0) + 1

    print("Task Breakdown:")
    for kind, count in sorted(task_kinds.items()):
        print(f"  - {kind}: {count}")

    # Show sample task chain
    print("\nSample Task Chain (first workstream):")
    for i, task in enumerate(plan.tasks[:3]):
        deps = f" (depends on {', '.join(task.depends_on)})" if task.depends_on else ""
        print(f"  {i+1}. {task.task_id}: {task.task_kind}{deps}")
        print(f"     {task.description}")

    # Save plan
    output_path = Path(__file__).parent / "demo_execution_plan.json"
    compiler.save_plan(plan, output_path)
    print(f"\n✓ Saved plan to {output_path}")

    return plan


def demonstrate_gap_queries(registry: GapRegistry):
    """Demonstrate gap query capabilities"""
    print_section("Gap Query Examples")

    from src.acms.gap_registry import GapSeverity

    critical_gaps = registry.get_by_severity(GapSeverity.CRITICAL)
    print(f"Critical Gaps ({len(critical_gaps)}):")
    for gap in critical_gaps:
        print(f"  • {gap.gap_id}: {gap.title}")

    # Integration gaps
    integration_gaps = registry.get_by_category("integration")
    print(f"\nIntegration Gaps ({len(integration_gaps)}):")
    for gap in integration_gaps:
        print(f"  • {gap.gap_id}: {gap.title}")

    # Unresolved gaps
    unresolved = registry.get_unresolved()
    print(f"\nTotal Unresolved: {len(unresolved)}")


def show_recommendations(registry: GapRegistry):
    """Show priority recommendations"""
    print_section("Recommended Actions")

    from gap_registry import GapSeverity

    # Load original report for recommendations
    with open(
        Path(__file__).parent.parent.parent
        / "docs"
        / "analysis_frameworks"
        / "example_gap_report.json",
        "r",
    ) as f:
        report = json.load(f)

    print("Priority Recommendations (from gap analysis):")
    for i, rec in enumerate(report["summary"]["priority_recommendations"], 1):
        print(f"  {i}. {rec}")

    print(
        f"\nEstimated Total Effort: {report['summary']['estimated_total_effort_hours']}"
    )


def main():
    """Run complete demonstration"""
    print("\n" + "=" * 70)
    print("  ACMS Pipeline Demonstration")
    print("  Using example_gap_report.json with 12 realistic gaps")
    print("=" * 70)

    # Phase 1: Gap Registry
    registry = demonstrate_gap_registry()

    # Query examples
    demonstrate_gap_queries(registry)

    # Phase 2: Clustering
    planner = demonstrate_clustering(registry)

    # Phase 3: Plan Generation
    plan = demonstrate_plan_compilation(planner)

    # Recommendations
    show_recommendations(registry)

    # Summary
    print_section("Demonstration Complete")
    print("Artifacts created:")
    print("  • demo_execution_plan.json - 22 tasks ready for MINI_PIPE")
    print("\nNext steps:")
    print("  1. Review demo_execution_plan.json")
    print("  2. Integrate AI for real gap analysis (Phase 1)")
    print("  3. Wire MINI_PIPE orchestrator (Phase 4)")
    print("  4. Run full pipeline: python acms_controller.py . --mode full")
    print()


if __name__ == "__main__":
    main()
