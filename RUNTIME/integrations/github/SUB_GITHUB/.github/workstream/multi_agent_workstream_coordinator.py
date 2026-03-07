#!/usr/bin/env python3
"""
Multi-Agent Workstream Coordinator with Result Consolidation
- Executes multiple workstreams across multiple agents
- Consolidates results from all agents
- Saves consolidated state to central database
- Generates unified reports
- NO STOP MODE - continues through all tasks
"""
# DOC_ID: DOC-SCRIPT-MULTI-AGENT-WORKSTREAM-COORDINATOR-001

import asyncio
import json
import sqlite3
import subprocess
import sys
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import networkx as nx

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
WORKSTREAMS_DIR = REPO_ROOT / "workstreams"
REPORTS_DIR = REPO_ROOT / "reports"
LOGS_DIR = REPO_ROOT / "logs"
STATE_DIR = REPO_ROOT / ".state"
CONSOLIDATED_DB = STATE_DIR / "multi_agent_consolidated.db"

# Ensure directories exist
for dir_path in [REPORTS_DIR, LOGS_DIR, STATE_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)


class ExecutionStatus(Enum):
    """Execution status codes"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result from single agent execution"""

    agent_id: str
    workstream_id: str
    status: ExecutionStatus
    start_time: str
    end_time: str
    duration_seconds: float
    files_modified: List[str]
    commits_created: List[str]
    errors: List[str]
    warnings: List[str]
    test_results: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class ConsolidatedResult:
    """Consolidated results from all agents"""

    run_id: str
    timestamp: str
    total_workstreams: int
    completed_count: int
    failed_count: int
    skipped_count: int
    total_files_modified: int
    total_commits: int
    total_errors: int
    total_warnings: int
    agents_used: List[str]
    execution_summary: Dict[str, Any]
    agent_results: List[AgentResult]
    consolidated_errors: List[Dict[str, Any]]
    recommendations: List[str]


class ConsolidationDatabase:
    """Manages consolidated results database"""

    def __init__(self, db_path: Path = CONSOLIDATED_DB):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consolidated_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    total_workstreams INTEGER,
                    completed_count INTEGER,
                    failed_count INTEGER,
                    skipped_count INTEGER,
                    total_files_modified INTEGER,
                    total_commits INTEGER,
                    total_errors INTEGER,
                    total_warnings INTEGER,
                    execution_summary TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    workstream_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    duration_seconds REAL,
                    files_modified TEXT,
                    commits_created TEXT,
                    errors TEXT,
                    warnings TEXT,
                    test_results TEXT,
                    metadata TEXT,
                    FOREIGN KEY (run_id) REFERENCES consolidated_runs(run_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consolidated_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    workstream_id TEXT,
                    agent_id TEXT,
                    timestamp TEXT,
                    stack_trace TEXT,
                    FOREIGN KEY (run_id) REFERENCES consolidated_runs(run_id)
                )
            """
            )

            conn.commit()

    def save_consolidated_run(self, result: ConsolidatedResult):
        """Save consolidated run results"""
        with sqlite3.connect(self.db_path) as conn:
            # Save main run
            conn.execute(
                """
                INSERT INTO consolidated_runs
                (run_id, timestamp, total_workstreams, completed_count, failed_count,
                 skipped_count, total_files_modified, total_commits, total_errors,
                 total_warnings, execution_summary, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    result.run_id,
                    result.timestamp,
                    result.total_workstreams,
                    result.completed_count,
                    result.failed_count,
                    result.skipped_count,
                    result.total_files_modified,
                    result.total_commits,
                    result.total_errors,
                    result.total_warnings,
                    json.dumps(result.execution_summary),
                    json.dumps(result.recommendations),
                ),
            )

            # Save agent results
            for agent_result in result.agent_results:
                conn.execute(
                    """
                    INSERT INTO agent_results
                    (run_id, agent_id, workstream_id, status, start_time, end_time,
                     duration_seconds, files_modified, commits_created, errors,
                     warnings, test_results, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.run_id,
                        agent_result.agent_id,
                        agent_result.workstream_id,
                        agent_result.status.value,
                        agent_result.start_time,
                        agent_result.end_time,
                        agent_result.duration_seconds,
                        json.dumps(agent_result.files_modified),
                        json.dumps(agent_result.commits_created),
                        json.dumps(agent_result.errors),
                        json.dumps(agent_result.warnings),
                        json.dumps(agent_result.test_results),
                        json.dumps(agent_result.metadata),
                    ),
                )

            # Save consolidated errors
            for error in result.consolidated_errors:
                conn.execute(
                    """
                    INSERT INTO consolidated_errors
                    (run_id, error_type, error_message, workstream_id, agent_id,
                     timestamp, stack_trace)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.run_id,
                        error.get("type", "unknown"),
                        error.get("message", ""),
                        error.get("workstream_id"),
                        error.get("agent_id"),
                        error.get("timestamp", datetime.now().isoformat()),
                        error.get("stack_trace", ""),
                    ),
                )

            conn.commit()

    def get_run_summary(self, run_id: str) -> Optional[Dict]:
        """Get summary of a specific run"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM consolidated_runs WHERE run_id = ?", (run_id,)
            ).fetchone()

            if not row:
                return None

            return dict(row)

    def get_all_runs(self, limit: int = 50) -> List[Dict]:
        """Get list of all runs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT run_id, timestamp, total_workstreams, completed_count,
                       failed_count, total_errors, created_at
                FROM consolidated_runs
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            ).fetchall()

            return [dict(row) for row in rows]


class MultiAgentWorkstreamCoordinator:
    """Coordinates multi-agent workstream execution with consolidation"""

    def __init__(self, agents_count: int = 3):
        self.agents_count = agents_count
        self.run_id = f"ma-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.db = ConsolidationDatabase()
        self.agent_results: List[AgentResult] = []
        self.errors: List[Dict[str, Any]] = []
        self.start_time = datetime.now()

    def load_workstreams(self) -> List[Dict]:
        """Load all workstream files"""
        workstreams = []

        for ws_file in sorted(WORKSTREAMS_DIR.glob("ws-*.json")):
            try:
                with open(ws_file, "r", encoding="utf-8") as f:
                    ws = json.load(f)
                workstreams.append(ws)
            except Exception as e:
                self.log_error("Load workstream", str(e), ws_file.name)

        return workstreams

    def log_error(
        self, context: str, error: str, workstream_id: str = None, agent_id: str = None
    ):
        """Log error (NO STOP MODE)"""
        error_entry = {
            "type": context,
            "message": error,
            "workstream_id": workstream_id,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "stack_trace": traceback.format_exc(),
        }
        self.errors.append(error_entry)
        print(f"❌ ERROR [{context}]: {error}", file=sys.stderr)

    async def execute_workstream_with_agent(
        self, agent_id: str, workstream: Dict
    ) -> AgentResult:
        """Execute single workstream with specific agent"""
        ws_id = workstream.get("id", "unknown")
        start = datetime.now()

        print(f"\n🤖 Agent {agent_id} starting {ws_id}...")

        try:
            # Simulate execution (replace with real agent call)
            # This is where you'd call aider, codex, etc.
            await asyncio.sleep(0.5)  # Simulate work

            # Mock result for demonstration
            result = AgentResult(
                agent_id=agent_id,
                workstream_id=ws_id,
                status=ExecutionStatus.COMPLETED,
                start_time=start.isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=(datetime.now() - start).total_seconds(),
                files_modified=[],
                commits_created=[],
                errors=[],
                warnings=[],
                test_results={},
                metadata=workstream,
            )

            self.agent_results.append(result)
            print(f"✅ Agent {agent_id} completed {ws_id}")
            return result

        except Exception as e:
            self.log_error(f"Execute {ws_id}", str(e), ws_id, agent_id)

            result = AgentResult(
                agent_id=agent_id,
                workstream_id=ws_id,
                status=ExecutionStatus.FAILED,
                start_time=start.isoformat(),
                end_time=datetime.now().isoformat(),
                duration_seconds=(datetime.now() - start).total_seconds(),
                files_modified=[],
                commits_created=[],
                errors=[str(e)],
                warnings=[],
                test_results={},
                metadata=workstream,
            )

            self.agent_results.append(result)
            print(f"❌ Agent {agent_id} failed {ws_id}")
            return result

    async def execute_all_workstreams(self):
        """Execute all workstreams across all agents (NO STOP MODE)"""
        print(f"\n{'='*80}")
        print(f"🚀 MULTI-AGENT WORKSTREAM EXECUTION - NO STOP MODE")
        print(f"{'='*80}")
        print(f"Run ID: {self.run_id}")
        print(f"Agents: {self.agents_count}")

        # Load workstreams
        workstreams = self.load_workstreams()
        print(f"Workstreams: {len(workstreams)}")

        # Distribute workstreams across agents
        tasks = []
        for i, ws in enumerate(workstreams):
            agent_id = f"agent-{(i % self.agents_count) + 1}"
            task = self.execute_workstream_with_agent(agent_id, ws)
            tasks.append(task)

        # Execute all in parallel
        print(f"\n📦 Executing {len(tasks)} workstreams...")
        await asyncio.gather(*tasks, return_exceptions=True)

        print(f"\n{'='*80}")
        print(f"✅ Execution complete - {len(self.agent_results)} results collected")
        print(f"{'='*80}")

    def consolidate_results(self) -> ConsolidatedResult:
        """Consolidate all agent results"""
        print(f"\n📊 Consolidating results...")

        completed = [
            r for r in self.agent_results if r.status == ExecutionStatus.COMPLETED
        ]
        failed = [r for r in self.agent_results if r.status == ExecutionStatus.FAILED]

        # Aggregate files modified
        all_files = set()
        all_commits = []
        for result in self.agent_results:
            all_files.update(result.files_modified)
            all_commits.extend(result.commits_created)

        # Count errors and warnings
        total_errors = sum(len(r.errors) for r in self.agent_results)
        total_warnings = sum(len(r.warnings) for r in self.agent_results)

        # Generate recommendations
        recommendations = []
        if failed:
            recommendations.append(f"Review {len(failed)} failed workstreams")
        if total_errors > 10:
            recommendations.append("High error count - consider system review")
        if len(completed) == len(self.agent_results):
            recommendations.append("All workstreams completed - ready for merge")

        # Create execution summary
        execution_summary = {
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "agents_used": self.agents_count,
            "parallel_execution": True,
            "completed_workstreams": [r.workstream_id for r in completed],
            "failed_workstreams": [r.workstream_id for r in failed],
        }

        consolidated = ConsolidatedResult(
            run_id=self.run_id,
            timestamp=datetime.now().isoformat(),
            total_workstreams=len(self.agent_results),
            completed_count=len(completed),
            failed_count=len(failed),
            skipped_count=0,
            total_files_modified=len(all_files),
            total_commits=len(all_commits),
            total_errors=total_errors,
            total_warnings=total_warnings,
            agents_used=[f"agent-{i+1}" for i in range(self.agents_count)],
            execution_summary=execution_summary,
            agent_results=self.agent_results,
            consolidated_errors=self.errors,
            recommendations=recommendations,
        )

        print(f"✅ Results consolidated")
        return consolidated

    def save_consolidated_results(self, consolidated: ConsolidatedResult):
        """Save consolidated results to database"""
        print(f"\n💾 Saving consolidated results to database...")

        try:
            self.db.save_consolidated_run(consolidated)
            print(f"✅ Saved to: {CONSOLIDATED_DB}")
        except Exception as e:
            self.log_error("Save results", str(e))
            print(f"❌ Failed to save: {e}")

    def generate_report(self, consolidated: ConsolidatedResult) -> Path:
        """Generate consolidated report"""
        print(f"\n📄 Generating consolidated report...")

        report_path = REPORTS_DIR / f"multi_agent_consolidated_{self.run_id}.md"

        content = f"""# Multi-Agent Workstream Execution Report

**Run ID**: {consolidated.run_id}
**Timestamp**: {consolidated.timestamp}
**Agents Used**: {len(consolidated.agents_used)}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Workstreams | {consolidated.total_workstreams} |
| Completed | {consolidated.completed_count} |
| Failed | {consolidated.failed_count} |
| Skipped | {consolidated.skipped_count} |
| Files Modified | {consolidated.total_files_modified} |
| Commits Created | {consolidated.total_commits} |
| Errors | {consolidated.total_errors} |
| Warnings | {consolidated.total_warnings} |

## Agent Results

### By Agent

"""

        # Group by agent
        by_agent: Dict[str, List[AgentResult]] = {}
        for result in consolidated.agent_results:
            if result.agent_id not in by_agent:
                by_agent[result.agent_id] = []
            by_agent[result.agent_id].append(result)

        for agent_id, results in sorted(by_agent.items()):
            completed_ws = [r for r in results if r.status == ExecutionStatus.COMPLETED]
            failed_ws = [r for r in results if r.status == ExecutionStatus.FAILED]

            content += f"\n#### {agent_id}\n\n"
            content += f"- Workstreams: {len(results)}\n"
            content += f"- Completed: {len(completed_ws)}\n"
            content += f"- Failed: {len(failed_ws)}\n\n"

        # Add errors section
        if consolidated.consolidated_errors:
            content += "\n## Errors\n\n"
            for error in consolidated.consolidated_errors[:10]:  # First 10
                content += f"### {error['type']}\n"
                content += f"- Message: {error['message']}\n"
                content += f"- Workstream: {error.get('workstream_id', 'N/A')}\n"
                content += f"- Agent: {error.get('agent_id', 'N/A')}\n\n"

        # Add recommendations
        if consolidated.recommendations:
            content += "\n## Recommendations\n\n"
            for rec in consolidated.recommendations:
                content += f"- {rec}\n"

        # Write report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ Report generated: {report_path}")
        return report_path

    async def run(self):
        """Main execution flow - NO STOP MODE"""
        try:
            # Execute all workstreams
            await self.execute_all_workstreams()

            # Consolidate results
            consolidated = self.consolidate_results()

            # Save to database
            self.save_consolidated_results(consolidated)

            # Generate report
            report_path = self.generate_report(consolidated)

            # Print summary
            print(f"\n{'='*80}")
            print(f"🏁 MULTI-AGENT EXECUTION COMPLETE")
            print(f"{'='*80}")
            print(f"Run ID: {consolidated.run_id}")
            print(
                f"Completed: {consolidated.completed_count}/{consolidated.total_workstreams}"
            )
            print(f"Failed: {consolidated.failed_count}")
            print(f"Errors: {consolidated.total_errors}")
            print(f"Database: {CONSOLIDATED_DB}")
            print(f"Report: {report_path}")
            print(f"{'='*80}\n")

            return 0 if consolidated.failed_count == 0 else 1

        except Exception as e:
            self.log_error("Fatal error in coordinator", str(e))
            print(f"\n❌ Fatal error: {e}")
            traceback.print_exc()
            return 2


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Agent Workstream Coordinator")
    parser.add_argument("--agents", type=int, default=3, help="Number of agents to use")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY RUN MODE")
        return 0

    coordinator = MultiAgentWorkstreamCoordinator(agents_count=args.agents)
    return asyncio.run(coordinator.run())


if __name__ == "__main__":
    sys.exit(main())
