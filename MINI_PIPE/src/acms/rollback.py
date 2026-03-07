"""
Automated Rollback System

Provides automatic rollback capabilities for failed executions.
Creates snapshots before execution and restores on failure.
"""

import json
import subprocess
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib


@dataclass
class Snapshot:
    """Represents a state snapshot"""
    snapshot_id: str
    created_at: datetime
    snapshot_type: str  # git, file, database
    metadata: Dict[str, Any]
    snapshot_path: Optional[Path] = None


class RollbackManager:
    """Manages rollback snapshots and restoration"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.snapshot_dir = self.repo_root / ".acms_runs" / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots: List[Snapshot] = []
    
    def create_snapshot(
        self,
        run_id: str,
        snapshot_type: str = "git"
    ) -> Snapshot:
        """
        Create a snapshot before execution
        
        Types:
        - git: Create git stash
        - file: Copy files to backup
        - database: Export database state
        """
        snapshot_id = self._generate_snapshot_id(run_id)
        
        if snapshot_type == "git":
            snapshot = self._create_git_snapshot(snapshot_id, run_id)
        elif snapshot_type == "file":
            snapshot = self._create_file_snapshot(snapshot_id, run_id)
        elif snapshot_type == "database":
            snapshot = self._create_database_snapshot(snapshot_id, run_id)
        else:
            raise ValueError(f"Unknown snapshot type: {snapshot_type}")
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def _create_git_snapshot(self, snapshot_id: str, run_id: str) -> Snapshot:
        """Create snapshot using git stash"""
        try:
            # Check if there are changes to stash
            result = subprocess.run(
                ["git", "diff", "--quiet"],
                cwd=self.repo_root,
                capture_output=True,
                timeout=10
            )
            
            has_changes = result.returncode != 0
            
            if has_changes:
                # Create stash with message
                stash_msg = f"ACMS snapshot {snapshot_id} for run {run_id}"
                result = subprocess.run(
                    ["git", "stash", "push", "-m", stash_msg],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"Git stash failed: {result.stderr}")
                
                return Snapshot(
                    snapshot_id=snapshot_id,
                    created_at=datetime.now(),
                    snapshot_type="git",
                    metadata={
                        "run_id": run_id,
                        "stash_message": stash_msg,
                        "has_changes": True
                    }
                )
            else:
                return Snapshot(
                    snapshot_id=snapshot_id,
                    created_at=datetime.now(),
                    snapshot_type="git",
                    metadata={
                        "run_id": run_id,
                        "has_changes": False
                    }
                )
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git snapshot timed out")
        except Exception as e:
            raise RuntimeError(f"Git snapshot failed: {e}")
    
    def _create_file_snapshot(self, snapshot_id: str, run_id: str) -> Snapshot:
        """Create snapshot by copying files"""
        snapshot_path = self.snapshot_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        # Copy important files
        files_to_backup = [
            ".acms_runs",
            "config",
            "schemas"
        ]
        
        backed_up = []
        for file_pattern in files_to_backup:
            source = self.repo_root / file_pattern
            if source.exists():
                dest = snapshot_path / file_pattern
                
                if source.is_dir():
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, dest)
                
                backed_up.append(file_pattern)
        
        return Snapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(),
            snapshot_type="file",
            metadata={
                "run_id": run_id,
                "backed_up_files": backed_up
            },
            snapshot_path=snapshot_path
        )
    
    def _create_database_snapshot(self, snapshot_id: str, run_id: str) -> Snapshot:
        """Create snapshot of database state"""
        snapshot_path = self.snapshot_dir / f"{snapshot_id}_db.json"
        
        # Export MINI_PIPE database if exists
        db_path = self.repo_root / ".minipipe" / "db" / "runs.db"
        
        if db_path.exists():
            # Simple backup: copy the database file
            backup_path = self.snapshot_dir / f"{snapshot_id}_runs.db"
            shutil.copy2(db_path, backup_path)
            
            return Snapshot(
                snapshot_id=snapshot_id,
                created_at=datetime.now(),
                snapshot_type="database",
                metadata={
                    "run_id": run_id,
                    "db_path": str(db_path),
                    "backup_path": str(backup_path)
                },
                snapshot_path=backup_path
            )
        
        return Snapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(),
            snapshot_type="database",
            metadata={
                "run_id": run_id,
                "no_database": True
            }
        )
    
    def rollback(self, snapshot: Snapshot) -> bool:
        """
        Rollback to a previous snapshot
        
        Returns:
            True if rollback successful, False otherwise
        """
        print(f"\n🔄 ROLLING BACK TO SNAPSHOT: {snapshot.snapshot_id}")
        print(f"   Type: {snapshot.snapshot_type}")
        print(f"   Created: {snapshot.created_at.isoformat()}\n")
        
        try:
            if snapshot.snapshot_type == "git":
                return self._rollback_git(snapshot)
            elif snapshot.snapshot_type == "file":
                return self._rollback_file(snapshot)
            elif snapshot.snapshot_type == "database":
                return self._rollback_database(snapshot)
            else:
                print(f"   ✗ Unknown snapshot type: {snapshot.snapshot_type}")
                return False
        
        except Exception as e:
            print(f"   ✗ Rollback failed: {e}")
            return False
    
    def _rollback_git(self, snapshot: Snapshot) -> bool:
        """Rollback using git stash pop"""
        if not snapshot.metadata.get("has_changes"):
            print("   → No changes to rollback (snapshot was clean)")
            return True
        
        try:
            # Find the stash
            stash_msg = snapshot.metadata.get("stash_message")
            
            # List stashes to find index
            result = subprocess.run(
                ["git", "stash", "list"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"   ✗ Could not list stashes: {result.stderr}")
                return False
            
            # Find stash index
            stash_index = None
            for line in result.stdout.splitlines():
                if stash_msg in line:
                    # Format: "stash@{0}: ..."
                    stash_index = line.split(":")[0]
                    break
            
            if not stash_index:
                print(f"   ✗ Stash not found: {stash_msg}")
                return False
            
            # Apply stash
            result = subprocess.run(
                ["git", "stash", "pop", stash_index],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"   ✗ Git stash pop failed: {result.stderr}")
                return False
            
            print(f"   ✓ Rolled back to git stash: {stash_index}")
            return True
        
        except subprocess.TimeoutExpired:
            print("   ✗ Git rollback timed out")
            return False
        except Exception as e:
            print(f"   ✗ Git rollback error: {e}")
            return False
    
    def _rollback_file(self, snapshot: Snapshot) -> bool:
        """Rollback by restoring files"""
        if not snapshot.snapshot_path or not snapshot.snapshot_path.exists():
            print("   ✗ Snapshot path not found")
            return False
        
        try:
            backed_up_files = snapshot.metadata.get("backed_up_files", [])
            
            for file_pattern in backed_up_files:
                source = snapshot.snapshot_path / file_pattern
                dest = self.repo_root / file_pattern
                
                if source.exists():
                    # Remove current version
                    if dest.exists():
                        if dest.is_dir():
                            shutil.rmtree(dest)
                        else:
                            dest.unlink()
                    
                    # Restore backup
                    if source.is_dir():
                        shutil.copytree(source, dest)
                    else:
                        shutil.copy2(source, dest)
                    
                    print(f"   ✓ Restored: {file_pattern}")
            
            return True
        
        except Exception as e:
            print(f"   ✗ File rollback error: {e}")
            return False
    
    def _rollback_database(self, snapshot: Snapshot) -> bool:
        """Rollback database state"""
        if snapshot.metadata.get("no_database"):
            print("   → No database to rollback")
            return True
        
        try:
            backup_path = Path(snapshot.metadata.get("backup_path"))
            db_path = Path(snapshot.metadata.get("db_path"))
            
            if not backup_path.exists():
                print(f"   ✗ Backup not found: {backup_path}")
                return False
            
            # Restore database
            if db_path.exists():
                db_path.unlink()
            
            shutil.copy2(backup_path, db_path)
            print(f"   ✓ Restored database: {db_path.name}")
            
            return True
        
        except Exception as e:
            print(f"   ✗ Database rollback error: {e}")
            return False
    
    def _generate_snapshot_id(self, run_id: str) -> str:
        """Generate unique snapshot ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{run_id}_{timestamp}".encode()
        hash_value = hashlib.md5(hash_input).hexdigest()[:8]
        return f"snapshot_{run_id}_{hash_value}"
    
    def cleanup_old_snapshots(self, keep_count: int = 10):
        """Remove old snapshots, keeping only the most recent"""
        if len(self.snapshots) <= keep_count:
            return
        
        # Sort by creation time
        sorted_snapshots = sorted(
            self.snapshots,
            key=lambda s: s.created_at,
            reverse=True
        )
        
        # Remove old snapshots
        to_remove = sorted_snapshots[keep_count:]
        
        for snapshot in to_remove:
            if snapshot.snapshot_path and snapshot.snapshot_path.exists():
                if snapshot.snapshot_path.is_dir():
                    shutil.rmtree(snapshot.snapshot_path)
                else:
                    snapshot.snapshot_path.unlink()
            
            self.snapshots.remove(snapshot)
        
        print(f"   Cleaned up {len(to_remove)} old snapshots")


def create_rollback_manager(repo_root: Path) -> RollbackManager:
    """Factory function to create rollback manager"""
    return RollbackManager(repo_root)
