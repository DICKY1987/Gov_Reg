# DOC_LINK: DOC-ERROR-ENGINE-ERROR-STATE-MACHINE-116
from __future__ import annotations

from typing import Literal

from .error_context import ErrorPipelineContext


# States from the Operating Contract / spec
S_INIT = "S_INIT"
S0_BASELINE_CHECK = "S0_BASELINE_CHECK"
S0_MECHANICAL_AUTOFIX = "S0_MECHANICAL_AUTOFIX"
S0_MECHANICAL_RECHECK = "S0_MECHANICAL_RECHECK"
S1_AIDER_FIX = "S1_AIDER_FIX"
S1_AIDER_RECHECK = "S1_AIDER_RECHECK"
S2_CODEX_FIX = "S2_CODEX_FIX"
S2_CODEX_RECHECK = "S2_CODEX_RECHECK"
S3_CLAUDE_FIX = "S3_CLAUDE_FIX"
S3_CLAUDE_RECHECK = "S3_CLAUDE_RECHECK"
S4_QUARANTINE = "S4_QUARANTINE"
S_SUCCESS = "S_SUCCESS"
S_ERROR_INFRA = "S_ERROR_INFRA"


def advance_state(ctx: ErrorPipelineContext) -> None:
    """Advance the state machine by one deterministic step.

    This function mutates ctx.current_state and related counters only.
    Side-effects (running tools, writing files) live in the service layer.
    """
    st = ctx.current_state

    if st == S_INIT:
        ctx.attempt_number = 0
        ctx.current_agent = "none"
        ctx.mechanical_fix_applied = False
        ctx.current_state = S0_BASELINE_CHECK
        return

    # The following states expect the service to have run an action and
    # updated ctx.last_error_report beforehand when appropriate.
    if st in {S0_BASELINE_CHECK, S0_MECHANICAL_RECHECK, S1_AIDER_RECHECK, S2_CODEX_RECHECK, S3_CLAUDE_RECHECK}:
        rep = ctx.last_error_report or {"summary": {}}
        summary = rep.get("summary", {})
        total = int(summary.get("total_issues", 0))
        has_hard = bool(summary.get("has_hard_fail", False))

        if total == 0:
            ctx.final_status = "success"
            ctx.current_state = S_SUCCESS
            return

        if not has_hard and not ctx.strict_mode:
            ctx.final_status = "success"
            ctx.current_state = S_SUCCESS
            return

        # escalate path
        # If we just did a recheck after some tier and still failing, advance to next tier
        if st == S0_MECHANICAL_RECHECK:
            if ctx.enable_aider:
                ctx.attempt_number = 1
                ctx.current_agent = "aider"
                ctx.current_state = S1_AIDER_FIX
            elif ctx.enable_codex:
                ctx.attempt_number = 2
                ctx.current_agent = "codex"
                ctx.current_state = S2_CODEX_FIX
            elif ctx.enable_claude:
                ctx.attempt_number = 3
                ctx.current_agent = "claude"
                ctx.current_state = S3_CLAUDE_FIX
            else:
                ctx.current_state = S4_QUARANTINE
            return

        if st == S1_AIDER_RECHECK:
            if ctx.enable_codex:
                ctx.attempt_number = 2
                ctx.current_agent = "codex"
                ctx.current_state = S2_CODEX_FIX
            elif ctx.enable_claude:
                ctx.attempt_number = 3
                ctx.current_agent = "claude"
                ctx.current_state = S3_CLAUDE_FIX
            else:
                ctx.current_state = S4_QUARANTINE
            return

        if st == S2_CODEX_RECHECK:
            if ctx.enable_claude:
                ctx.attempt_number = 3
                ctx.current_agent = "claude"
                ctx.current_state = S3_CLAUDE_FIX
            else:
                ctx.current_state = S4_QUARANTINE
            return

        if st == S3_CLAUDE_RECHECK:
            ctx.current_state = S4_QUARANTINE
            return

        # st == S0_BASELINE_CHECK and failing
        if ctx.enable_mechanical_autofix:
            ctx.current_state = S0_MECHANICAL_AUTOFIX
        elif ctx.enable_aider:
            ctx.attempt_number = 1
            ctx.current_agent = "aider"
            ctx.current_state = S1_AIDER_FIX
        elif ctx.enable_codex:
            ctx.attempt_number = 2
            ctx.current_agent = "codex"
            ctx.current_state = S2_CODEX_FIX
        elif ctx.enable_claude:
            ctx.attempt_number = 3
            ctx.current_agent = "claude"
            ctx.current_state = S3_CLAUDE_FIX
        else:
            ctx.current_state = S4_QUARANTINE
        return

    # Fix states: the service is expected to apply changes (mechanical or AI)
    # then transition to the corresponding RECHECK state.
    if st == S0_MECHANICAL_AUTOFIX:
        ctx.mechanical_fix_applied = True
        ctx.current_state = S0_MECHANICAL_RECHECK
        return

    if st == S1_AIDER_FIX:
        ctx.current_state = S1_AIDER_RECHECK
        return

    if st == S2_CODEX_FIX:
        ctx.current_state = S2_CODEX_RECHECK
        return

    if st == S3_CLAUDE_FIX:
        ctx.current_state = S3_CLAUDE_RECHECK
        return

    # Terminal states remain unchanged
    if st in {S_SUCCESS, S4_QUARANTINE, S_ERROR_INFRA}:
        return

