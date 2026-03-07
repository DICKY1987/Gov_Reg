# DOC_LINK: DOC-CORE-DETECTION-INIT-009
"""ID System Detection Package

Change detection and entity classification.

DOC_ID: DOC-CORE-DETECTION-INIT-009
"""

from .change_detector import ChangeDetector, Change, ChangeType
from .entity_classifier import EntityClassifier, Entity, EntityType

__all__ = [
    'ChangeDetector',
    'Change',
    'ChangeType',
    'EntityClassifier',
    'Entity',
    'EntityType',
]

__version__ = '1.0.0'
__doc_id__ = 'DOC-CORE-DETECTION-INIT-009'
