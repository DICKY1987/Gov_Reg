# ACMS & MINI_PIPE Test Plan

This document outlines the comprehensive testing strategy for the ACMS and MINI_PIPE systems, based on the 50-step process defined in `process_spec.json`. The goal is to achieve full test coverage through a multi-layered approach, ensuring correctness, determinism, and robustness.

## 1. Testing Levels

The testing strategy is divided into three primary levels:

*   **Level 1: Unit / Contract Tests**: These are fine-grained tests that verify the functionality of individual modules and functions in isolation. They use mocks for external dependencies to ensure that each component behaves as expected according to its contract.
*   **Level 2: Phase Integration Tests**: These tests verify the interaction between a group of related modules that constitute a logical phase of the 50-step process (e.g., Gap Discovery, Planning, Execution). They use a combination of real modules and mocks for external systems (like AI adapters).
*   **Level 3: End-to-End (E2E) Tests**: These are high-level tests that run the entire `acms_controller.py` pipeline from start to finish on a controlled, fixture repository. They verify that all 50 steps are orchestrated correctly and produce the expected final artifacts.

## 2. Test Coverage Matrix

The following matrix maps each of the 50 process steps to the tests that will provide coverage.

| Step | Responsible Module        | Unit/Contract Test (`tests/unit/`)                   | Phase Integration Test (`tests/integration/`)          | E2E Test (`tests/e2e/`)             |
|------|---------------------------|------------------------------------------------------|--------------------------------------------------------|-------------------------------------|
| 1-5  | `acms_controller`         | `test_controller_init.py`                            | `test_phase_init.py`                                   | `test_full_run.py`                  |
| 6    | `acms_ai_adapter`         | `test_ai_adapter_factory.py`                         | `test_phase_gap_discovery.py`                          | `test_full_run.py`                  |
| 7-9  | `acms_controller`         | `test_controller_gap_analysis.py`                    | `test_phase_gap_discovery.py`                          | `test_full_run.py`                  |
| 10   | `acms_ai_adapter`         | `test_ai_adapter_mock.py`                            | (Mocked)                                               | (Mocked)                            |
| 11-12| `acms_controller`         | `test_controller_gap_analysis.py`                    | `test_phase_gap_discovery.py`                          | `test_full_run.py`                  |
| 13-15| `gap_registry`            | `test_gap_registry.py`                               | `test_phase_gap_discovery.py`                          | `test_full_run.py`                  |
| 16-20| `execution_planner`       | `test_execution_planner.py`                          | `test_phase_planning.py`                               | `test_full_run.py`                  |
| 21-24| `phase_plan_compiler`     | `test_phase_plan_compiler.py`                        | `test_phase_planning.py`                               | `test_full_run.py`                  |
| 25-27| `acms_minipipe_adapter`   | `test_acms_minipipe_adapter.py`                      | `test_phase_execution.py`                              | `test_full_run.py`                  |
| 28-31| `MINI_PIPE_orchestrator`  | `test_orchestrator.py`                               | `test_phase_execution.py`                              | `test_full_run.py`                  |
| 32-34| `MINI_PIPE_executor`      | `test_executor.py`                                   | `test_phase_execution.py`                              | `test_full_run.py`                  |
| 35-37| `MINI_PIPE_tools`         | `test_tools.py`                                      | `test_phase_execution.py`                              | `test_full_run.py`                  |
| 38-39| `MINI_PIPE_orchestrator`  | `test_orchestrator_lifecycle.py`                     | `test_phase_execution.py`                              | `test_full_run.py`                  |
| 40-41| `MINI_PIPE_patch_ledger`  | `test_patch_ledger.py`                               | `test_phase_execution_with_patching.py`                | `test_full_run_with_patching.py`    |
| 42   | `MINI_PIPE_orchestrator`  | `test_orchestrator.py`                               | `test_phase_execution.py`                              | `test_full_run.py`                  |
| 43-44| `acms_minipipe_adapter`   | `test_acms_minipipe_adapter.py`                      | `test_phase_summary.py`                                | `test_full_run.py`                  |
| 45-46| `acms_controller`         | `test_controller_summary.py`                         | `test_phase_summary.py`                                | `test_full_run.py`                  |
| 47-48| `acms_controller`         | `test_controller_summary.py`                         | `test_phase_summary.py`                                | `test_full_run.py`                  |
| 49-50| `acms_controller`         | `test_controller_exit.py`                            | `test_phase_summary.py`                                | `test_full_run.py`                  |

## 3. Implementation Plan

### 3.1. Level 1: Unit/Contract Tests

Unit tests will be created for each module listed in the `responsible_module` column of the coverage matrix. These tests will use `pytest` and `unittest.mock` to test functions in isolation.

**Example Tests:**
*   `test_gap_registry.py`: Test that `normalize()` creates stable IDs and `persist()` writes to the correct location.
*   `test_execution_planner.py`: Given a fixed set of gaps, assert that the output workstreams are deterministic and correctly structured.
*   `test_phase_plan_compiler.py`: Given a sample workstream, assert that the output MINI_PIPE plan is valid against its JSON schema.
*   `test_scheduler.py`: Test `get_ready_batches()` returns predictable results for a given task graph and detects cycles.

### 3.2. Level 2: Phase Integration Tests

Phase integration tests will combine modules to test logical segments of the pipeline.

*   **Phase A: Gap Discovery (Steps 7-15)**: Use a mock AI adapter to return a fixed gap analysis report. Run the controller's gap analysis path and assert that the `gap_registry.json` is created correctly.
*   **Phase B: Planning (Steps 16-24)**: Use a fixture `gap_registry.json`. Run the `execution_planner` and `phase_plan_compiler` and assert that a valid `mini_pipe_execution_plan.json` is created.
*   **Phase C: Execution (Steps 25-42)**: Use a small, fixed execution plan with mock tools. Run the `MINI_PIPE_orchestrator` and assert that all tasks are marked as completed and tool calls were correct.
*   **Phase D: Summary (Steps 43-50)**: Use fixture execution results. Run the `acms_controller` summary building logic and assert that `run_status.json` is created and its contents are correct.

### 3.3. Level 3: End-to-End Tests

E2E tests will execute the entire pipeline using `acms_controller.py`.

*   **`test_full_run.py`**:
    *   Set up a small, self-contained Git repository fixture.
    *   Run `python acms_controller.py /path/to/fixture --mode full --ai-adapter mock`.
    *   Use a mock AI adapter that returns a deterministic gap report.
    *   After the run, parse the `run.ledger.jsonl`, `run_status.json`, and other artifacts to verify that all steps executed correctly and the final state is as expected.
*   **`test_determinism.py`**:
    *   Run the E2E test twice with identical inputs.
    *   Compare the `gap_registry.json`, `mini_pipe_execution_plan.json`, and `run_status.json` (ignoring timestamps) from both runs. Assert that they are identical.
*   **`test_failure_paths.py`**:
    *   Inject controlled failures at key steps (e.g., malformed AI response, failing tool).
    *   Assert that the pipeline halts gracefully, the error is logged correctly in `run_status.json`, and no partial state is committed.

This test plan provides a clear roadmap for building a robust and comprehensive test suite that ensures the reliability of the ACMS and MINI_PIPE systems.
