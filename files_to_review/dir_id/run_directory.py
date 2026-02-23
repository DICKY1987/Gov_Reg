"""
Run Directory Manager
Handles creation and management of planning run state directories.
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4


class RunDirectoryManager:
    """Manages planning run directory structure and artifacts"""
    
    def __init__(self, state_root: Path):
        self.state_root = Path(state_root)
        self.runs_dir = self.state_root / "runs"
        self.evidence_dir = self.state_root / "evidence"
        self.metrics_dir = self.state_root / "metrics"
    
    def create_run_directory(self, run_id: Optional[str] = None) -> str:
        """Create new planning run directory structure
        
        Args:
            run_id: Optional custom run ID, auto-generated if None
            
        Returns:
            run_id: The run identifier
        """
        if not run_id:
            timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            short_uuid = str(uuid4()).replace('-', '')[:8]
            run_id = f"planning_{timestamp}_{short_uuid}"
        
        run_dir = self.runs_dir / run_id
        
        # Create directory structure
        (run_dir / "iterations").mkdir(parents=True, exist_ok=True)
        (run_dir / "patches").mkdir(parents=True, exist_ok=True)
        (run_dir / "critic_reports").mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        
        # Create evidence directory
        evidence_dir = self.evidence_dir / run_id
        evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Create run manifest placeholder
        manifest = {
            "planning_run_id": run_id,
            "repo_root": str(Path.cwd()),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "state_directory": str(run_dir)
        }
        
        manifest_path = run_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return run_id
    
    def get_run_directory(self, run_id: str) -> Path:
        """Get path to existing run directory"""
        return self.runs_dir / run_id
    
    def get_iteration_path(self, run_id: str, iteration: int) -> Path:
        """Get path for iteration artifacts"""
        return self.runs_dir / run_id / "iterations" / f"iter_{iteration:03d}"
    
    def get_evidence_path(self, run_id: str, phase_id: str, step_id: str) -> Path:
        """Get path for evidence artifacts"""
        evidence_path = self.evidence_dir / run_id / phase_id / step_id
        evidence_path.mkdir(parents=True, exist_ok=True)
        return evidence_path
    
    def list_runs(self) -> list:
        """List all planning runs"""
        if not self.runs_dir.exists():
            return []
        return [d.name for d in self.runs_dir.iterdir() if d.is_dir()]
    
    def get_manifest(self, run_id: str) -> Dict:
        """Load run manifest"""
        manifest_path = self.runs_dir / run_id / "manifest.json"
        with open(manifest_path, 'r') as f:
            return json.load(f)
    
    def save_artifact(self, run_id: str, artifact_name: str, content: Dict) -> Path:
        """Save artifact to run directory
        
        Args:
            run_id: Planning run identifier
            artifact_name: Name of artifact file
            content: JSON-serializable content
            
        Returns:
            Path to saved artifact
        """
        artifact_path = self.runs_dir / run_id / "artifacts" / artifact_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(artifact_path, 'w') as f:
            json.dump(content, f, indent=2)
        
        return artifact_path
