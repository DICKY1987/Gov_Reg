# DOC_LINK: DOC-CORE-RESOLUTION-INIT-017
"""ID System Resolution Package

Identity resolution and remediation engine.

DOC_ID: DOC-CORE-RESOLUTION-INIT-017
"""

from .identity_resolver import IdentityResolver, Resolution, ResolutionAction
from .remediation_engine import RemediationEngine, Remediation, RemediationMode
from .id_generator import IDGenerator

__all__ = [
    'IdentityResolver',
    'Resolution',
    'ResolutionAction',
    'RemediationEngine',
    'Remediation',
    'RemediationMode',
    'IDGenerator',
]

__version__ = '1.0.0'
__doc_id__ = 'DOC-CORE-RESOLUTION-INIT-017'
