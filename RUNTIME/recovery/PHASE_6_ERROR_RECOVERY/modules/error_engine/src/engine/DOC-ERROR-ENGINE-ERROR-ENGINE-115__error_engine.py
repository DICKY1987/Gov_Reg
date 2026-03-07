# DOC_LINK: DOC-ERROR-ENGINE-ERROR-ENGINE-115
"""Error engine - Re-exports from pipeline_engine for compatibility."""

# DOC_ID: DOC-ERROR-ENGINE-ERROR-ENGINE-115

from phase6_error_recovery.modules.error_engine.src.engine.pipeline_engine import (
    PipelineEngine,
)

__all__ = ["PipelineEngine"]
