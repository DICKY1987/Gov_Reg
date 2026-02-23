"""Base command class with shared utilities"""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from datetime import datetime, timezone
import uuid


class BaseCommand:
    """Base class for all Phase B commands"""
    
    def __init__(self, args):
        self.args = args
        self.repo_root = Path(args.repo_root).resolve()
        self.runs_dir = Path(args.runs_dir)
        self.run_id = args.run_id
        self.phase_b_run_id = args.phase_b_run_id or self._get_or_create_phase_b_run_id()
        self.strict = args.strict
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s [%(levelname)s] %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Phase A run paths
        self.phase_a_dir = self.runs_dir / self.run_id
        self.phase_a_artifacts = self.phase_a_dir / "artifacts" / "phase" / "PHASE_A"
        
        # Phase B run paths
        self.phase_b_dir = self.phase_a_dir / "artifacts" / "phase" / "PHASE_B"
        
    def _get_or_create_phase_b_run_id(self) -> str:
        """Get existing or create new Phase B run ID"""
        linkage_file = self.runs_dir / self.args.run_id / "phase_b_linkage.json"
        
        if linkage_file.exists():
            with open(linkage_file) as f:
                linkage = json.load(f)
                return linkage["phase_b_run_id"]
        
        # Generate new Phase B run ID
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_uuid = str(uuid.uuid4())
        phase_b_run_id = f"phaseB_{timestamp}_{run_uuid}"
        
        # Write linkage file
        linkage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(linkage_file, "w") as f:
            json.dump({
                "phase_a_run_id": self.args.run_id,
                "phase_b_run_id": phase_b_run_id,
                "linked_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
        
        return phase_b_run_id
    
    def load_json(self, path: Path) -> Dict[str, Any]:
        """Load and parse JSON file"""
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")
        with open(path) as f:
            return json.load(f)
    
    def write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON file with proper formatting"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self.logger.debug(f"Wrote {path}")
    
    def execute(self) -> int:
        """Execute command - must be implemented by subclasses"""
        raise NotImplementedError("Subclass must implement execute()")
