# DOC_LINK: DOC-CORE-STATE-INIT-002
"""ID System State Management Package

State machine and rollback capabilities for orchestrator.

DOC_ID: DOC-CORE-STATE-INIT-002
"""

from .state_machine import State, StateTransition, StateMachine
from .rollback_manager import RollbackManager, Snapshot

__all__ = [
    'State',
    'StateTransition',
    'StateMachine',
    'RollbackManager',
    'Snapshot',
]

__version__ = '1.0.0'
__doc_id__ = 'DOC-CORE-STATE-INIT-002'
