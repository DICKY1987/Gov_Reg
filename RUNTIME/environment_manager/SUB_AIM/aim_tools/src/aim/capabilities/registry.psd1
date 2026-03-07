# Capability Registry
# PowerShell Data File (.psd1) defining worker capabilities

@(
    @{
        CapabilityId = 'cap-orchestration-001'
        Version      = '1.0.0'
        Name         = 'WorkstreamOrchestration'
        Description  = 'Coordinate multi-phase workstream execution'
        Provider     = 'core.engine.orchestrator'
        DeprecatedBy = $null
        Stability    = 'stable'
        SinceVersion = '1.0.0'

        Requirements = @{
            MinPythonVersion = '3.10'
            Dependencies     = @('git', 'pytest', 'ruff')
            MinMemoryMB      = 512
            MinDiskSpaceMB   = 1024
        }

        Operations = @(
            @{
                Name        = 'StartWorkstream'
                Inputs      = @('workstream_id', 'config')
                Output      = 'workstream_handle'
                Description = 'Initialize and start workstream execution'
            },
            @{
                Name        = 'StopWorkstream'
                Inputs      = @('workstream_id')
                Output      = 'status'
                Description = 'Gracefully stop workstream execution'
            },
            @{
                Name        = 'GetWorkstreamStatus'
                Inputs      = @('workstream_id')
                Output      = 'status_object'
                Description = 'Query current workstream status'
            }
        )
    },

    @{
        CapabilityId = 'cap-aider-001'
        Version      = '1.0.0'
        Name         = 'AiderCodeEditing'
        Description  = 'AI-assisted code editing using Aider'
        Provider     = 'core.engine.tools.AiderAdapter'
        DeprecatedBy = $null
        Stability    = 'stable'
        SinceVersion = '1.0.0'

        Requirements = @{
            MinPythonVersion = '3.10'
            Dependencies     = @('aider-chat>=0.50.0', 'git')
            MinMemoryMB      = 1024
            MinDiskSpaceMB   = 512
            NetworkRequired  = $true  # Aider may need OpenAI API
        }

        Operations = @(
            @{
                Name        = 'EditCode'
                Inputs      = @('files', 'prompt', 'context_requirements')
                Output      = 'edit_result'
                Description = 'Edit code files using AI assistance'
            },
            @{
                Name        = 'ValidateContext'
                Inputs      = @('files', 'max_tokens')
                Output      = 'validation_result'
                Description = 'Validate that files fit within context window'
            }
        )
    },

    @{
        CapabilityId = 'cap-pytest-001'
        Version      = '1.0.0'
        Name         = 'PytestExecution'
        Description  = 'Execute Python tests using pytest'
        Provider     = 'core.engine.workers.PytestWorker'
        DeprecatedBy = $null
        Stability    = 'stable'
        SinceVersion = '1.0.0'

        Requirements = @{
            MinPythonVersion = '3.10'
            Dependencies     = @('pytest>=7.0')
            MinMemoryMB      = 512
            MinDiskSpaceMB   = 256
        }

        Operations = @(
            @{
                Name        = 'RunTests'
                Inputs      = @('test_paths', 'pytest_args')
                Output      = 'test_results'
                Description = 'Run pytest with specified paths and arguments'
            },
            @{
                Name        = 'CollectTests'
                Inputs      = @('test_paths')
                Output      = 'test_list'
                Description = 'Collect tests without executing them'
            }
        )
    },

    @{
        CapabilityId = 'cap-ruff-001'
        Version      = '1.0.0'
        Name         = 'RuffLinting'
        Description  = 'Python linting and formatting using Ruff'
        Provider     = 'core.engine.workers.RuffWorker'
        DeprecatedBy = $null
        Stability    = 'stable'
        SinceVersion = '1.0.0'

        Requirements = @{
            MinPythonVersion = '3.10'
            Dependencies     = @('ruff>=0.1.0')
            MinMemoryMB      = 256
            MinDiskSpaceMB   = 128
        }

        Operations = @(
            @{
                Name        = 'CheckCode'
                Inputs      = @('file_paths', 'ruff_config')
                Output      = 'lint_results'
                Description = 'Check Python files for linting errors'
            },
            @{
                Name        = 'FormatCode'
                Inputs      = @('file_paths')
                Output      = 'format_results'
                Description = 'Format Python files using Ruff'
            },
            @{
                Name        = 'FixCode'
                Inputs      = @('file_paths', 'fix_rules')
                Output      = 'fix_results'
                Description = 'Automatically fix linting errors'
            }
        )
    },

    @{
        CapabilityId = 'cap-git-001'
        Version      = '1.0.0'
        Name         = 'GitOperations'
        Description  = 'Git repository operations and worktree management'
        Provider     = 'core.state.worktree'
        DeprecatedBy = $null
        Stability    = 'stable'
        SinceVersion = '1.0.0'

        Requirements = @{
            Dependencies     = @('git>=2.30')
            MinMemoryMB      = 256
            MinDiskSpaceMB   = 512
        }

        Operations = @(
            @{
                Name        = 'CreateWorktree'
                Inputs      = @('workstream_id', 'base_branch')
                Output      = 'worktree_path'
                Description = 'Create isolated git worktree for workstream'
            },
            @{
                Name        = 'DeleteWorktree'
                Inputs      = @('workstream_id')
                Output      = 'status'
                Description = 'Delete worktree after workstream completion'
            },
            @{
                Name        = 'MergeWorktree'
                Inputs      = @('workstream_id', 'target_branch')
                Output      = 'merge_result'
                Description = 'Merge workstream changes to target branch'
            }
        )
    },

    @{
        CapabilityId = 'cap-dag-001'
        Version      = '1.0.0'
        Name         = 'DAGScheduling'
        Description  = 'DAG-based task scheduling and execution planning'
        Provider     = 'core.engine.scheduler'
        DeprecatedBy = $null
        Stability    = 'stable'
        SinceVersion = '1.0.0'

        Requirements = @{
            MinPythonVersion = '3.10'
            Dependencies     = @()
            MinMemoryMB      = 256
            MinDiskSpaceMB   = 128
        }

        Operations = @(
            @{
                Name        = 'BuildDAG'
                Inputs      = @('tasks', 'dependencies')
                Output      = 'dag_structure'
                Description = 'Build DAG from task dependencies'
            },
            @{
                Name        = 'CreateExecutionPlan'
                Inputs      = @('dag_structure')
                Output      = 'execution_plan'
                Description = 'Create staged execution plan from DAG'
            },
            @{
                Name        = 'CalculateCriticalPath'
                Inputs      = @('dag_structure', 'task_durations')
                Output      = 'critical_path'
                Description = 'Identify critical path in DAG'
            }
        )
    },

    @{
        CapabilityId = 'cap-validation-001'
        Version      = '1.0.0'
        Name         = 'ValidationRules'
        Description  = 'Pre and post-execution validation'
        Provider     = 'core.engine.validators'
        DeprecatedBy = $null
        Stability    = 'experimental'
        SinceVersion = '1.0.0'

        Requirements = @{
            MinPythonVersion = '3.10'
            Dependencies     = @('git', 'pytest', 'ruff')
            MinMemoryMB      = 512
            MinDiskSpaceMB   = 256
        }

        Operations = @(
            @{
                Name        = 'ValidatePreExecution'
                Inputs      = @('task_id', 'validation_rules')
                Output      = 'validation_result'
                Description = 'Run pre-execution validation checks'
            },
            @{
                Name        = 'ValidatePostExecution'
                Inputs      = @('task_id', 'validation_rules')
                Output      = 'validation_result'
                Description = 'Run post-execution validation checks'
            }
        )
    }
)
