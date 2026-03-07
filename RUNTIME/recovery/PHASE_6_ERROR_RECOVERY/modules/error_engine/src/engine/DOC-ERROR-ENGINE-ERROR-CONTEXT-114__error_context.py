# DOC_LINK: DOC-ERROR-ENGINE-ERROR-CONTEXT-114
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ErrorPipelineContext:
    # Identity
    run_id: str
    workstream_id: str

    # Target files
    python_files: List[str] = field(default_factory=list)
    powershell_files: List[str] = field(default_factory=list)

    # Config
    enable_mechanical_autofix: bool = True
    enable_aider: bool = True
    enable_codex: bool = True
    enable_claude: bool = True
    strict_mode: bool = True
    max_attempts_per_agent: int = 1

    # Attempt tracking
    attempt_number: int = 0  # 0=baseline,1=aider,2=codex,3=claude
    current_agent: str = "none"  # "none"|"aider"|"codex"|"claude"
    mechanical_fix_applied: bool = False

    # Error reports
    last_error_report: Optional[Dict[str, Any]] = None
    previous_error_report: Optional[Dict[str, Any]] = None

    # AI attempts audit
    ai_attempts: List[Dict[str, Any]] = field(default_factory=list)

    # Finalization
    final_status: Optional[str] = None  # "success"|"quarantined"|"infra_failure"
    quarantine_path: Optional[str] = None

    # State machine
    current_state: str = "S_INIT"

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ErrorPipelineContext":
        return cls(**data)

    def record_ai_attempt(self, attempt: Dict[str, Any]) -> None:
        self.ai_attempts.append(attempt)

    def update_error_reports(self, new_report: Dict[str, Any]) -> None:
        self.previous_error_report = self.last_error_report
        self.last_error_report = new_report

