# DOC_LINK: DOC-CORE-WORKSPACE-DIAGRAM-BASED-RULES-1092
"""
Diagram-based classification rules extracted from UTI_VISUAL_DIAGRAMS
These rules provide architectural context for file classification
"""
DOC_ID: DOC-CORE-WORKSPACE-DIAGRAM-BASED-RULES-1092

# From directory-structure.mmd
DIRECTORY_MAPPINGS = {
    'core/state/': 'PHASE_5_EXECUTION',
    'core/engine/': 'PHASE_5_EXECUTION',
    'core/planning/': 'PHASE_1_PLANNING',
    'core/bootstrap/': 'PHASE_0_BOOTSTRAP',
    'error/engine/': 'PHASE_6_ERROR_RECOVERY',
    'error/plugins/': 'PHASE_6_ERROR_RECOVERY',
    'error/shared/': 'PHASE_6_ERROR_RECOVERY',
    'aim/': 'SUB_AIM',
    'pm/': 'SUB_PM',
    'spec/': 'SUB_IO_CONTRACT_PIPELINE',
    'aider/': 'SUB_AIM',  # Aider integration
    'config/': 'CONFIG',
    'schema/': 'SUB_IO_CONTRACT_PIPELINE',
    'workstreams/': 'PHASE_1_PLANNING',
    'scripts/': 'UTI_TOOLS',
    'tools/': 'UTI_TOOLS',
    'tests/': 'tests',
    'docs/': 'DOCUMENTS',
    'meta/': 'DOCUMENTS',
}

# Legacy/deprecated paths (should be archived)
LEGACY_PATHS = [
    'src/pipeline/',
    'MOD_ERROR_PIPELINE/',
    'src/shim/',
    'src/legacy/',
]

# From module-dependencies.mmd - Core module groupings
MODULE_GROUPS = {
    'ORCHESTRATOR_GROUP': {
        'files': ['orchestrator.py', 'scheduler.py', 'executor.py', 'tools.py', 'circuit_breakers.py', 'recovery.py'],
        'destination': 'PHASE_5_EXECUTION/engine'
    },
    'STATE_GROUP': {
        'files': ['db.py', 'db_sqlite.py', 'crud.py', 'bundles.py', 'worktree.py'],
        'destination': 'PHASE_5_EXECUTION/state'
    },
    'PLANNING_GROUP': {
        'files': ['planner.py', 'archive.py', 'workstream_gen.py'],
        'destination': 'PHASE_1_PLANNING'
    },
    'ERROR_ENGINE_GROUP': {
        'files': ['error_engine.py', 'error_state_machine.py', 'plugin_manager.py'],
        'destination': 'PHASE_6_ERROR_RECOVERY/engine'
    },
    'ERROR_PLUGINS_GROUP': {
        'files': ['python_ruff.py', 'python_mypy.py', 'js_eslint.py', 'md_markdownlint.py', 'yaml_yamllint.py'],
        'destination': 'PHASE_6_ERROR_RECOVERY/plugins'
    },
    'AIM_GROUP': {
        'files': ['bridge.py', 'aim_client.py', 'registry.py', 'capability_index.py'],
        'destination': 'SUB_AIM'
    }
}

# From integration-overview.mmd - Architectural layers
ARCHITECTURAL_LAYERS = {
    'entry_layer': {
        'keywords': ['cli', 'user', 'main', 'entry'],
        'destination': 'PHASE_0_BOOTSTRAP'
    },
    'core_pipeline': {
        'keywords': ['orchestrator', 'planner', 'scheduler', 'executor'],
        'destination': 'PHASE_5_EXECUTION'
    },
    'error_detection': {
        'keywords': ['error_engine', 'plugin_manager', 'error_state', 'error_detection'],
        'destination': 'PHASE_6_ERROR_RECOVERY'
    },
    'external_integration': {
        'keywords': ['aim', 'aider', 'pm', 'spec', 'github', 'integration'],
        'destination': 'SUB_*'  # Varies by keyword
    },
    'configuration': {
        'keywords': ['config', 'schema', 'workstreams', 'settings'],
        'destination': 'CONFIG'
    }
}

# From DOC_TASK_LIFECYCLE_DIAGRAM.md - State machine components
TASK_LIFECYCLE_COMPONENTS = {
    'state_machine': {
        'states': ['PENDING', 'IN_PROGRESS', 'VALIDATING', 'COMPLETED', 'FAILED', 'RETRYING', 'CIRCUIT_OPEN'],
        'files': ['state_machine.py', 'task_state.py', 'lifecycle.py'],
        'destination': 'PHASE_5_EXECUTION'
    },
    'retry_circuit_breaker': {
        'keywords': ['retry', 'circuit_breaker', 'backoff', 'circuit_open'],
        'files': ['circuit_breakers.py', 'retry.py', 'backoff.py'],
        'destination': 'PHASE_6_ERROR_RECOVERY'
    }
}

# From data-flow-aim-integration.mmd - AIM subsystem structure
AIM_SUBSYSTEM_STRUCTURE = {
    'aim_bridge': {
        'files': ['bridge.py', 'aim_bridge.py'],
        'destination': 'SUB_AIM'
    },
    'aim_registry': {
        'subdirs': ['registry', '.AIM_ai-tools-registry'],
        'files': ['tool_catalog.py', 'tool_configs.py', 'capability_index.py'],
        'destination': 'SUB_AIM/registry'
    },
    'aim_tools': {
        'keywords': ['aider', 'claude', 'gpt', 'openai', 'anthropic', 'ollama'],
        'destination': 'SUB_AIM/tools'
    }
}

# From DOC_ERROR_ESCALATION_DIAGRAM.md - Error plugin architecture
ERROR_PLUGIN_TYPES = {
    'python_plugins': {
        'names': ['python_ruff', 'python_mypy', 'python_black_fix', 'python_pylint'],
        'destination': 'PHASE_6_ERROR_RECOVERY/plugins'
    },
    'javascript_plugins': {
        'names': ['js_eslint', 'js_prettier_fix', 'js_tslint'],
        'destination': 'PHASE_6_ERROR_RECOVERY/plugins'
    },
    'linting_plugins': {
        'names': ['md_markdownlint', 'yaml_yamllint', 'json_validator'],
        'destination': 'PHASE_6_ERROR_RECOVERY/plugins'
    },
    'security_plugins': {
        'names': ['semgrep', 'bandit', 'security_scanner'],
        'destination': 'PHASE_6_ERROR_RECOVERY/plugins'
    }
}

# From FOLDER_LIFECYCLE_FLOW.md - Processing flow layers
PROCESSING_FLOW_LAYERS = {
    'input_layer': ['workstreams', 'pm', 'aim'],
    'configuration_layer': ['schema', 'config', 'templates', 'docs', 'registry'],
    'core_domain_layer': ['core', 'error', 'specifications'],
    'execution_layer': ['engine'],
    'infrastructure_layer': ['scripts', 'infra', 'state', 'logs', 'tools'],
}

def classify_by_path(file_path: str) -> tuple[str, str, int]:
    """
    Classify file based on diagram-defined path mappings
    Returns: (destination, reason, confidence)
    """
    path_lower = file_path.lower().replace('\\', '/')

    # Check legacy paths first (highest priority to mark as deprecated)
    for legacy_path in LEGACY_PATHS:
        if legacy_path in path_lower:
            return ('UTI_ARCHIVES', f'Legacy path: {legacy_path}', 95)

    # Check directory mappings
    for dir_path, destination in DIRECTORY_MAPPINGS.items():
        if dir_path in path_lower:
            return (destination, f'Directory mapping: {dir_path}', 90)

    return (None, 'No diagram-based path match', 0)

def classify_by_module_group(file_name: str) -> tuple[str, str, int]:
    """
    Classify file based on module group membership
    Returns: (destination, reason, confidence)
    """
    for group_name, group_data in MODULE_GROUPS.items():
        if file_name in group_data['files']:
            return (group_data['destination'], f'Module group: {group_name}', 85)

    return (None, 'No module group match', 0)

def classify_by_error_plugin_type(file_name: str) -> tuple[str, str, int]:
    """
    Classify error plugin files
    Returns: (destination, reason, confidence)
    """
    for plugin_type, plugin_data in ERROR_PLUGIN_TYPES.items():
        for plugin_name in plugin_data['names']:
            if plugin_name in file_name.lower():
                return (plugin_data['destination'], f'Error plugin: {plugin_type}', 90)

    return (None, 'Not an error plugin', 0)
