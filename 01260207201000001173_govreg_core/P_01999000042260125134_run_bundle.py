"""
RunBundle - Canonical Run Root Factory

Provides unified run directory structure for the Gov_Reg pipeline.
Implements evidence_path_policy.json formulas with sanitization and sealing.

FILE_ID: 01999000042260125134
"""

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from P_01260207233100000010_canonical_hash import hash_canonical_data, hash_file_content


class RunBundle:
    """
    Factory for creating canonical run root directories.
    
    Structure:
        evidence/{plan_id}/{run_id}/
            ├── manifest.json
            ├── gates/
            ├── controls/
            ├── phases/
            ├── stages/
            ├── telemetry/
            └── seal.json (after seal())
    """
    
    def __init__(self, repo_root: Path, plan_id: str, run_id: Optional[str] = None):
        """
        Initialize RunBundle.
        
        Args:
            repo_root: Repository root directory
            plan_id: Plan identifier (will be sanitized)
            run_id: Optional run ID (defaults to YYYYMMDD_HHMMSS timestamp)
        """
        self.repo_root = Path(repo_root)
        self.plan_id = self._sanitize_plan_id(plan_id)
        self.run_id = run_id or self._generate_run_id()
        self._root = self.repo_root / "evidence" / self.plan_id / self.run_id
    
    @property
    def root(self) -> Path:
        """Return the run root directory path."""
        return self._root
    
    def create(self) -> Path:
        """
        Create the run directory structure.
        
        Returns:
            Path to the created run root
        """
        subdirs = ["gates", "controls", "phases", "stages", "telemetry"]
        self._root.mkdir(parents=True, exist_ok=True)
        
        for subdir in subdirs:
            (self._root / subdir).mkdir(exist_ok=True)
        
        return self._root
    
    def write_manifest(self, extra: Optional[Dict[str, Any]] = None) -> Path:
        """
        Write manifest.json with run metadata.
        
        Args:
            extra: Optional additional metadata to include
            
        Returns:
            Path to manifest.json
        """
        manifest = {
            "plan_id": self.plan_id,
            "run_id": self.run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(self.repo_root),
            "schema_version": "1.0.0"
        }
        
        if extra:
            manifest.update(extra)
        
        manifest_path = self._root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        
        return manifest_path
    
    def stage_path(self, stage: str) -> Path:
        """
        Get path for a specific stage.
        
        Args:
            stage: Stage identifier (e.g., "stage0_ssot", "stage3_facts")
            
        Returns:
            Path to stage directory
        """
        stage_dir = self._root / "stages" / stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir
    
    def gate_evidence_path(self, gate_id: str) -> Path:
        """
        Get evidence path for a specific gate.
        
        Args:
            gate_id: Gate identifier (e.g., "DIR-G1", "FILE-G3")
            
        Returns:
            Path to gate evidence directory
        """
        gate_dir = self._root / "gates" / gate_id
        gate_dir.mkdir(parents=True, exist_ok=True)
        return gate_dir
    
    def seal(self) -> Path:
        """
        Seal the run bundle by creating an index of all artifacts.
        
        Generates seal.json with SHA256 hash of each file in the bundle.
        
        Returns:
            Path to seal.json
        """
        artifacts = {}
        
        for file_path in self._root.rglob("*"):
            if file_path.is_file() and file_path.name != "seal.json":
                relative_path = file_path.relative_to(self._root)
                try:
                    artifacts[str(relative_path)] = hash_file_content(file_path)
                except Exception as e:
                    artifacts[str(relative_path)] = f"ERROR: {str(e)}"
        
        seal = {
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "plan_id": self.plan_id,
            "run_id": self.run_id,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "seal_hash": hash_canonical_data({"artifacts": artifacts})
        }
        
        seal_path = self._root / "seal.json"
        seal_path.write_text(json.dumps(seal, indent=2), encoding="utf-8")
        
        return seal_path
    
    @staticmethod
    def _sanitize_plan_id(plan_id: str) -> str:
        """
        Sanitize plan_id per evidence_path_policy.json rules.
        
        Rules:
        - Lowercase
        - Replace spaces with hyphens
        - Only allow a-z0-9-_
        - Max 64 chars
        """
        sanitized = plan_id.lower()
        sanitized = re.sub(r'\s+', '-', sanitized)
        sanitized = re.sub(r'[^a-z0-9\-_]', '', sanitized)
        return sanitized[:64]
    
    @staticmethod
    def _generate_run_id() -> str:
        """Generate run_id as YYYYMMDD_HHMMSS timestamp."""
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
