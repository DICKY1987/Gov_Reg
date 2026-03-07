#!/usr/bin/env python3
"""
Simple Sequential Workstream Executor
Executes workstreams one at a time with clear progress reporting
"""
# DOC_ID: DOC-SCRIPT-SCRIPTS-SIMPLE-WORKSTREAM-EXECUTOR-232
# DOC_ID: DOC-SCRIPT-SCRIPTS-SIMPLE-WORKSTREAM-EXECUTOR-169

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/simple_executor.log"), logging.StreamHandler()],
)

logger = logging.getLogger("simple_executor")


class SimpleWorkstreamExecutor:
    """Simple sequential executor for workstreams"""

    def __init__(self, workstreams_dir: Path):
        self.workstreams_dir = workstreams_dir
        self.results = []

    def load_workstreams(self) -> List[Dict]:
        """Load all workstream JSON files"""
        workstreams = []

        for ws_file in sorted(self.workstreams_dir.glob("ws-*.json")):
            try:
                with open(ws_file) as f:
                    ws = json.load(f)
                workstreams.append(ws)
                logger.info(f"Loaded: {ws['id']}")
            except Exception as e:
                logger.error(f"Failed to load {ws_file}: {e}")

        return workstreams

    def check_dependencies(self, workstream: Dict, completed: set) -> bool:
        """Check if all dependencies are met"""
        depends_on = workstream.get("depends_on", [])

        if not depends_on:
            return True

        missing = [dep for dep in depends_on if dep not in completed]
        if missing:
            logger.debug(f"{workstream['id']} waiting for: {missing}")
            return False

        return True

    def execute_workstream(self, workstream: Dict) -> bool:
        """Execute a single workstream"""
        ws_id = workstream["id"]
        title = workstream.get("title", ws_id)

        print("\n" + "=" * 70)
        print(f"📋 Workstream: {ws_id}")
        print(f"📝 Title: {title}")
        print("=" * 70)

        # Get execution details
        tool = workstream.get("tool", "manual")
        tasks = workstream.get("tasks", [])
        files_scope = workstream.get("files_scope", [])

        print(f"\n🔧 Tool: {tool}")
        print(f"📁 Files: {len(files_scope)} file patterns")
        print(f"✓ Tasks: {len(tasks)}")

        # Show tasks
        if tasks:
            print("\n📝 Tasks to complete:")
            for i, task in enumerate(tasks, 1):
                print(f"   {i}. {task}")

        # Show files
        if files_scope:
            print("\n📁 File scope:")
            for pattern in files_scope[:5]:  # Show first 5
                print(f"   - {pattern}")
            if len(files_scope) > 5:
                print(f"   ... and {len(files_scope) - 5} more")

        # Execution options
        print("\n" + "-" * 70)
        print("Choose execution method:")
        print("  1. Execute with Aider (automated)")
        print("  2. Open files in editor (manual)")
        print("  3. Skip this workstream")
        print("  4. Mark as completed (already done)")
        print("  q. Quit executor")
        print("-" * 70)

        while True:
            choice = input("\nYour choice [1/2/3/4/q]: ").strip().lower()

            if choice == "1":
                return self._execute_with_aider(workstream)
            elif choice == "2":
                return self._execute_manual(workstream)
            elif choice == "3":
                logger.info(f"Skipped: {ws_id}")
                return False
            elif choice == "4":
                logger.info(f"Marked complete: {ws_id}")
                return True
            elif choice == "q":
                print("\n👋 Exiting executor...")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, 4, or q")

    def _execute_with_aider(self, workstream: Dict) -> bool:
        """Execute using Aider"""
        ws_id = workstream["id"]
        tasks = workstream.get("tasks", [])
        files_scope = workstream.get("files_scope", [])

        # Build Aider command
        cmd = ["aider"]

        # Add files (expand patterns to actual files)
        files = self._expand_file_patterns(files_scope)
        if files:
            cmd.extend(files[:10])  # Limit to 10 files to avoid huge command

        # Add message with tasks
        if tasks:
            message = f"Workstream {ws_id}:\n" + "\n".join(
                f"{i+1}. {t}" for i, t in enumerate(tasks)
            )
            cmd.extend(["--message", message])
            cmd.append("--yes")  # Auto-approve

        print(f"\n🤖 Running Aider...")
        print(f"Command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(
                cmd, cwd=Path.cwd(), timeout=1800  # 30 minute timeout
            )

            success = result.returncode == 0

            if success:
                print("\n✅ Aider completed successfully")
            else:
                print(f"\n❌ Aider failed with exit code {result.returncode}")

            return success

        except subprocess.TimeoutExpired:
            print("\n⏱️ Aider timed out after 30 minutes")
            return False
        except FileNotFoundError:
            print("\n❌ Aider not found. Install with: pip install aider-chat")
            return False
        except Exception as e:
            print(f"\n❌ Error running Aider: {e}")
            return False

    def _execute_manual(self, workstream: Dict) -> bool:
        """Open files for manual editing"""
        files_scope = workstream.get("files_scope", [])

        # Expand patterns
        files = self._expand_file_patterns(files_scope)

        if not files:
            print("\n⚠️ No files matched the patterns")
            return False

        print(f"\n📂 Found {len(files)} files")
        print("Opening in default editor...\n")

        # Open first few files
        for f in files[:5]:
            print(f"  - {f}")
            try:
                if sys.platform == "win32":
                    subprocess.run(["notepad", str(f)])
                else:
                    subprocess.run(["$EDITOR", str(f)])
            except Exception as e:
                logger.error(f"Failed to open {f}: {e}")

        if len(files) > 5:
            print(f"\n⚠️ {len(files) - 5} more files not opened")

        print("\n" + "-" * 70)
        input("Press Enter when you've completed the manual edits...")

        # Ask if completed
        done = input("Did you complete all tasks? [y/n]: ").strip().lower()
        return done == "y"

    def _expand_file_patterns(self, patterns: List[str]) -> List[Path]:
        """Expand glob patterns to actual files"""
        files = []

        for pattern in patterns:
            # Convert to Path and use glob
            try:
                matches = list(Path.cwd().glob(pattern))
                files.extend([f for f in matches if f.is_file()])
            except Exception as e:
                logger.warning(f"Pattern {pattern} failed: {e}")

        return sorted(set(files))  # Unique, sorted

    def run(self):
        """Main execution loop"""
        print("\n" + "=" * 70)
        print("🚀 Simple Workstream Executor")
        print("=" * 70)

        # Load workstreams
        print("\n📂 Loading workstreams...")
        workstreams = self.load_workstreams()

        if not workstreams:
            print("❌ No workstreams found in workstreams/")
            return

        print(f"✅ Loaded {len(workstreams)} workstreams\n")

        # Track progress
        completed = set()
        skipped = set()
        total = len(workstreams)

        # Execution loop
        iteration = 0
        max_iterations = total * 2  # Prevent infinite loops

        while len(completed) + len(skipped) < total and iteration < max_iterations:
            iteration += 1

            print(f"\n{'='*70}")
            print(
                f"🔄 Iteration {iteration} | Completed: {len(completed)}/{total} | Skipped: {len(skipped)}"
            )
            print(f"{'='*70}\n")

            # Find ready workstreams
            executed_this_round = False

            for ws in workstreams:
                ws_id = ws["id"]

                # Skip if already done
                if ws_id in completed or ws_id in skipped:
                    continue

                # Check dependencies
                if not self.check_dependencies(ws, completed):
                    continue

                # Execute
                success = self.execute_workstream(ws)
                executed_this_round = True

                if success:
                    completed.add(ws_id)
                    self.results.append(
                        {
                            "workstream_id": ws_id,
                            "status": "completed",
                            "iteration": iteration,
                        }
                    )
                else:
                    skipped.add(ws_id)
                    self.results.append(
                        {
                            "workstream_id": ws_id,
                            "status": "skipped",
                            "iteration": iteration,
                        }
                    )

                break  # One at a time

            if not executed_this_round:
                print("\n⚠️ No workstreams ready to execute")
                print(
                    "This might indicate circular dependencies or missing workstreams"
                )
                break

        # Final report
        self.print_summary(completed, skipped, total)

    def print_summary(self, completed: set, skipped: set, total: int):
        """Print execution summary"""
        print("\n" + "=" * 70)
        print("📊 EXECUTION SUMMARY")
        print("=" * 70)
        print(f"\n✅ Completed: {len(completed)}/{total}")
        print(f"⏭️  Skipped: {len(skipped)}/{total}")
        print(f"⏸️  Remaining: {total - len(completed) - len(skipped)}/{total}")

        if completed:
            print("\n✅ Completed workstreams:")
            for ws_id in sorted(completed):
                print(f"   - {ws_id}")

        if skipped:
            print("\n⏭️ Skipped workstreams:")
            for ws_id in sorted(skipped):
                print(f"   - {ws_id}")

        # Save results
        results_file = Path("reports/simple_executor_results.json")
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, "w") as f:
            json.dump(
                {
                    "completed": list(completed),
                    "skipped": list(skipped),
                    "total": total,
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Results saved to: {results_file}")
        print("\n" + "=" * 70)


def main():
    """Main entry point"""
    workstreams_dir = Path("workstreams")

    if not workstreams_dir.exists():
        print(f"❌ Workstreams directory not found: {workstreams_dir}")
        print("\nExpected structure:")
        print("  workstreams/")
        print("    ws-*.json")
        return 1

    executor = SimpleWorkstreamExecutor(workstreams_dir)
    executor.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
