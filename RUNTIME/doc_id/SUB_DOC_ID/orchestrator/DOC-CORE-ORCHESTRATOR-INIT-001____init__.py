# DOC_LINK: DOC-CORE-ORCHESTRATOR-INIT-001
"""ID System Orchestrator Package

Master orchestration engine for ID system automation.
Handles change detection, entity classification, identity resolution,
remediation, validation, and gate enforcement.

DOC_ID: DOC-CORE-ORCHESTRATOR-INIT-001
"""

from .orchestrator import Orchestrator
from .state.state_machine import State, StateTransition
from .state.rollback_manager import RollbackManager

__all__ = [
    'Orchestrator',
    'State',
    'StateTransition',
    'RollbackManager',
]

__version__ = '1.0.0'
__doc_id__ = 'DOC-CORE-ORCHESTRATOR-INIT-001'
