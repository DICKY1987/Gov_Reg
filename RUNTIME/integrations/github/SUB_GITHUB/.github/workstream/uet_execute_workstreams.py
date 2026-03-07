"""
UET Workstream Executor
Main script to execute workstreams using UET framework
"""

# DOC_ID: DOC-SCRIPT-SCRIPTS-UET-EXECUTE-WORKSTREAMS-238
# DOC_ID: DOC-SCRIPT-SCRIPTS-UET-EXECUTE-WORKSTREAMS-175

import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Add project root to path
.parent.parent))

# Import UET components
from modules.core_engine import Orchestrator
from modules.core_engine.m010001_uet_scheduler import ExecutionScheduler, Task

from scripts.uet_tool_adapter import ToolAdapter
from scripts.uet_workstream_loader import WorkstreamLoader
from UNIVERSAL_EXECUTION_TEMPLATES_FRAMEWORK.core.engine.dag_builder import DAGBuilder


def load_config(config_path: str = ".uet/config.yaml") -> dict:
    """Load UET configuration."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def setup_logging(config: dict):
    """Setup logging based on config."""
    log_dir = Path(config.get("execution", {}).get("log_dir", "logs/uet"))
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = config.get("execution", {}).get("log_level", "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "executor.log"),
            logging.StreamHandler(),
        ],
    )


def main():
    """Main execution function."""
    print("=" * 70)
    print("🚀 UET Workstream Executor")
    print("=" * 70)

    # Load configuration
    print("\n📋 Loading configuration...")
    try:
        config = load_config()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info("=== UET Execution Started ===")

    # Initialize orchestrator
    print("\n🎯 Initializing orchestrator...")
    try:
        orchestrator = Orchestrator()
        run_id = orchestrator.create_run(
            project_id=config["project"]["name"],
            phase_id="workstream-execution",
            metadata={
                "start_time": datetime.utcnow().isoformat(),
                "config": config["project"],
            },
        )
        orchestrator.start_run(run_id)
        print(f"✅ Run created: {run_id}")
        logger.info(f"Run created: {run_id}")
    except Exception as e:
        print(f"❌ Failed to initialize orchestrator: {e}")
        logger.error(f"Orchestrator init failed: {e}")
        return 1

    # Load workstreams
    print("\n📂 Loading workstreams...")
    try:
        loader = WorkstreamLoader(
            workstream_dir=config["execution"]["workstream_dir"],
            pattern=config["execution"]["workstream_pattern"],
        )
        workstreams = loader.load_all()
        summary = loader.get_summary()
        print(f"✅ Loaded {summary['successfully_loaded']} workstreams")
        if summary["failed"]:
            print(f"⚠️  Failed to load {summary['failed']} workstreams")
        logger.info(f"Loaded {len(workstreams)} workstreams")
    except Exception as e:
        print(f"❌ Failed to load workstreams: {e}")
        logger.error(f"Workstream loading failed: {e}")
        orchestrator.complete_run(run_id, status="failed", error_message=str(e))
        return 1

    if not workstreams:
        print("❌ No workstreams to execute")
        orchestrator.complete_run(run_id, status="succeeded")
        return 0

    # Build DAG
    print("\n🔗 Building execution DAG...")
    try:
        dag_builder = DAGBuilder()
        dag_plan = dag_builder.build_from_workstreams(workstreams)

        print(f"✅ DAG built successfully")
        print(f"   Total waves: {dag_plan['total_waves']}")
        print(f"   Total workstreams: {dag_plan['total_workstreams']}")

        # Show wave structure
        for wave_idx, wave in enumerate(dag_plan["waves"], 1):
            print(f"\n   Wave {wave_idx}: {len(wave)} workstreams")
            for ws_id in wave[:3]:  # Show first 3
                print(f"      - {ws_id}")
            if len(wave) > 3:
                print(f"      ... and {len(wave) - 3} more")

        logger.info(
            f"DAG: {dag_plan['total_waves']} waves, {dag_plan['total_workstreams']} workstreams"
        )

    except Exception as e:
        print(f"❌ Failed to build DAG: {e}")
        logger.error(f"DAG build failed: {e}")
        orchestrator.complete_run(run_id, status="failed", error_message=str(e))
        return 1

    # Initialize tool adapter
    print("\n🔧 Initializing tool adapter...")
    try:
        tool_adapter = ToolAdapter(config)
        print("✅ Tool adapter ready")
    except Exception as e:
        print(f"❌ Failed to initialize tool adapter: {e}")
        logger.error(f"Tool adapter init failed: {e}")
        orchestrator.complete_run(run_id, status="failed", error_message=str(e))
        return 1

    # Create scheduler and add tasks
    print("\n📅 Creating execution scheduler...")
    try:
        scheduler = ExecutionScheduler()
        task_objects = []

        for ws in workstreams:
            task = Task(
                task_id=ws.get("id"),
                task_kind="workstream",
                depends_on=ws.get("depends_on", []),
                metadata={
                    "workstream": ws,
                    "tool": ws.get("tool", "aider"),
                    "files": ws.get("files_scope", []),
                    "tasks": ws.get("tasks", []),
                },
            )
            task_objects.append(task)
            scheduler.add_task(task)

        print(f"✅ Scheduler created with {len(task_objects)} tasks")
        logger.info(f"Scheduler ready: {len(task_objects)} tasks")

    except Exception as e:
        print(f"❌ Failed to create scheduler: {e}")
        logger.error(f"Scheduler creation failed: {e}")
        orchestrator.complete_run(run_id, status="failed", error_message=str(e))
        return 1

    # Execute waves
    print("\n" + "=" * 70)
    print("🎬 Starting Execution")
    print("=" * 70)

    completed_count = 0
    failed_count = 0
    total_tasks = len(workstreams)

    wave_num = 0
    while True:
        # Get ready tasks
        ready_tasks = scheduler.get_ready_tasks()

        if not ready_tasks:
            break

        wave_num += 1
        print(f"\n{'='*70}")
        print(f"🌊 Wave {wave_num}: {len(ready_tasks)} tasks")
        print(f"{'='*70}")

        # Execute tasks in wave (sequential for now)
        for task in ready_tasks:
            task_id = task.task_id
            print(f"\n▶️  Executing: {task_id}")
            logger.info(f"Starting task: {task_id}")

            # Create step
            step_id = orchestrator.create_step_attempt(
                run_id=run_id,
                tool_id=task.metadata.get("tool", "aider"),
                sequence=completed_count + failed_count + 1,
                metadata=task.metadata,
            )

            # Execute task
            try:
                task.status = "running"
                result = tool_adapter.execute_task(task.__dict__)

                if result["success"]:
                    task.status = "completed"
                    completed_count += 1
                    print(f"   ✅ Completed ({result.get('duration', 0):.1f}s)")

                    orchestrator.complete_step_attempt(
                        step_attempt_id=step_id,
                        status="succeeded",
                        exit_code=result.get("exit_code", 0),
                        output_patch_id=result.get("patch_file"),
                    )
                else:
                    task.status = "failed"
                    failed_count += 1
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

                    orchestrator.complete_step_attempt(
                        step_attempt_id=step_id,
                        status="failed",
                        exit_code=result.get("exit_code", -1),
                        error_log=result.get("error"),
                    )

            except Exception as e:
                task.status = "failed"
                failed_count += 1
                print(f"   ❌ Exception: {e}")
                logger.error(f"Task {task_id} exception: {e}")

                orchestrator.complete_step_attempt(
                    step_attempt_id=step_id,
                    status="failed",
                    exit_code=-1,
                    error_log=str(e),
                )

            # Show progress
            progress = ((completed_count + failed_count) / total_tasks) * 100
            print(
                f"   Progress: {completed_count + failed_count}/{total_tasks} ({progress:.1f}%)"
            )

    # Complete run
    print("\n" + "=" * 70)
    print("📊 Execution Complete")
    print("=" * 70)
    print(f"\n✅ Completed: {completed_count}/{total_tasks}")
    print(f"❌ Failed: {failed_count}/{total_tasks}")
    print(f"📈 Success Rate: {(completed_count/total_tasks*100):.1f}%")

    if failed_count == 0:
        orchestrator.complete_run(run_id, status="succeeded")
        logger.info("Run completed successfully")
        return 0
    else:
        orchestrator.complete_run(
            run_id, status="failed", error_message=f"{failed_count} tasks failed"
        )
        logger.warning(f"Run completed with {failed_count} failures")
        return 1


if __name__ == "__main__":
    sys.exit(main())
