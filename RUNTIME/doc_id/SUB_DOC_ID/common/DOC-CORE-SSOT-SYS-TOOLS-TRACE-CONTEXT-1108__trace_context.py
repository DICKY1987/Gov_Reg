#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108
"""
Trace Context - Observability Layer

Provides trace ID and run ID propagation across all SSOT tools.
Implements Governance Layer 4: Trace ID + Run ID propagation required.

Alignment:
- Uses UET_* prefix per SYSTEM_DETERMINISM_CONTRACT.json:27
- Context-based for async compatibility
- Supports explicit injection for testing
"""
# DOC_ID: DOC-CORE-SSOT-SYS-TOOLS-TRACE-CONTEXT-1108

import uuid
import os
from contextvars import ContextVar
from typing import Optional

# Context variables for trace/run IDs
_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
_run_id: ContextVar[Optional[str]] = ContextVar('run_id', default=None)


def get_or_create_trace_id() -> str:
    """
    Get current trace ID or create new one.
    
    Trace ID tracks a single logical operation across tool boundaries.
    Persists for entire execution chain (e.g., ci_gate → validator → relationship_gen).
    
    Returns:
        str: UUID-format trace ID
    
    Examples:
        >>> import os
        >>> os.environ['UET_TRACE_ID'] = 'test-trace-123'
        >>> get_or_create_trace_id()
        'test-trace-123'
    """
    tid = _trace_id.get()
    if tid is None:
        # Check environment first (allows external orchestration)
        tid = os.environ.get('UET_TRACE_ID')
        if tid is None:
            # Generate new trace ID
            tid = str(uuid.uuid4())
        _trace_id.set(tid)
    return tid


def get_or_create_run_id() -> str:
    """
    Get current run ID or create new one.
    
    Run ID identifies a single execution instance (one process).
    Used for output directory naming per SYSTEM_DETERMINISM_CONTRACT.
    
    Returns:
        str: UUID-format run ID
    
    Examples:
        >>> import os
        >>> os.environ['UET_RUN_ID'] = 'run-456'
        >>> get_or_create_run_id()
        'run-456'
    """
    rid = _run_id.get()
    if rid is None:
        # Check environment first
        rid = os.environ.get('UET_RUN_ID')
        if rid is None:
            # Generate new run ID
            rid = str(uuid.uuid4())
        _run_id.set(rid)
    return rid


def set_trace_id(trace_id: str) -> None:
    """
    Explicitly set trace ID (for testing or external orchestration).
    
    Args:
        trace_id: Trace ID to set
    """
    _trace_id.set(trace_id)


def set_run_id(run_id: str) -> None:
    """
    Explicitly set run ID (for testing or external orchestration).
    
    Args:
        run_id: Run ID to set
    """
    _run_id.set(run_id)


def get_trace_context() -> dict:
    """
    Get both trace and run IDs in single call.
    
    Returns:
        dict: {"trace_id": str, "run_id": str}
    
    Examples:
        >>> ctx = get_trace_context()
        >>> 'trace_id' in ctx and 'run_id' in ctx
        True
    """
    return {
        "trace_id": get_or_create_trace_id(),
        "run_id": get_or_create_run_id()
    }


def clear_context() -> None:
    """
    Clear trace context (for testing).
    
    Use in test teardown to ensure clean state.
    """
    _trace_id.set(None)
    _run_id.set(None)


if __name__ == "__main__":
    # Demo usage
    print("Trace Context Demo")
    print("=" * 50)
    
    # First call creates new IDs
    ctx1 = get_trace_context()
    print(f"Initial context: {ctx1}")
    
    # Subsequent calls return same IDs
    ctx2 = get_trace_context()
    print(f"Same context: {ctx2}")
    assert ctx1 == ctx2
    
    # Environment variables take precedence
    os.environ['UET_TRACE_ID'] = 'external-trace-123'
    clear_context()  # Reset to pick up env var
    ctx3 = get_trace_context()
    print(f"From env: {ctx3}")
    assert ctx3['trace_id'] == 'external-trace-123'
    
    print("\n✓ Trace context working correctly")

