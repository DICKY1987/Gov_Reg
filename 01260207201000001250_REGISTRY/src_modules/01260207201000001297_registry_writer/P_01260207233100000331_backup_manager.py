"""
Canonical Backup Manager for Registry.

Handles:
- create_backup() -> timestamped file in REGISTRY/backups/
- rollback(path) restores registry; rollback(None) uses latest
- list_backups(limit) returns sorted newest-first
- cleanup_old_backups() respects retention_days
- All backups verified as valid JSON after creation
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any


class BackupManager:
    """
    Canonical backup/rollback manager in src/registry_writer/.
    """

    def __init__(self, registry_path: Optional[Path] = None, backup_dir: Optional[Path] = None):
        """
        Initialize backup manager.

        Args:
            registry_path: Path to registry file (default from config)
            backup_dir: Path to backup directory (default from config)
        """
        if registry_path is None:
            # Import here to avoid circular dependency
            from config.registry_paths import REGISTRY_PATH, BACKUP_DIR
            registry_path = REGISTRY_PATH
            backup_dir = BACKUP_DIR

        self.registry_path = Path(registry_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, suffix: str = "") -> Path:
        """
        Create timestamped backup of registry.

        Args:
            suffix: Optional suffix for backup filename

        Returns:
            Path to created backup file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"registry_backup_{timestamp}"
        if suffix:
            backup_name += f"_{suffix}"
        backup_name += ".json"

        backup_path = self.backup_dir / backup_name

        # Copy registry to backup
        shutil.copy2(self.registry_path, backup_path)

        # Verify backup is valid JSON
        with open(backup_path) as f:
            json.load(f)  # Will raise if invalid

        return backup_path

    def verify_backup(self, backup_path: Path) -> bool:
        """
        Verify backup is valid JSON.

        Args:
            backup_path: Path to backup file

        Returns:
            True if valid, False otherwise
        """
        try:
            with open(backup_path) as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False

    def rollback(self, backup_path: Optional[Path] = None) -> Path:
        """
        Restore registry from backup.

        Args:
            backup_path: Path to backup file (None = use latest)

        Returns:
            Path to backup used for rollback
        """
        if backup_path is None:
            backup_path = self.get_latest_backup()
            if backup_path is None:
                raise FileNotFoundError("No backups available for rollback")

        backup_path = Path(backup_path)

        # Verify backup before rollback
        if not self.verify_backup(backup_path):
            raise ValueError(f"Backup at {backup_path} is not valid JSON")

        # Create a backup of current state before rollback
        pre_rollback_backup = self.create_backup(suffix="pre_rollback")

        # Restore from backup
        shutil.copy2(backup_path, self.registry_path)

        return backup_path

    def get_latest_backup(self) -> Optional[Path]:
        """
        Get path to most recent backup.

        Returns:
            Path to latest backup, or None if no backups exist
        """
        backups = self.list_backups(limit=1)
        return backups[0] if backups else None

    def list_backups(self, limit: Optional[int] = None) -> List[Path]:
        """
        List backup files sorted newest-first.

        Args:
            limit: Maximum number of backups to return (None = all)

        Returns:
            List of backup file paths sorted by modification time (newest first)
        """
        backups = list(self.backup_dir.glob("*.json"))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        if limit is not None:
            backups = backups[:limit]

        return backups

    def cleanup_old_backups(self, retention_days: int = 30) -> List[Path]:
        """
        Remove backups older than retention period.

        Args:
            retention_days: Number of days to keep backups

        Returns:
            List of deleted backup paths
        """
        cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
        cutoff_timestamp = cutoff_time.timestamp()

        deleted = []
        for backup_path in self.list_backups():
            if backup_path.stat().st_mtime < cutoff_timestamp:
                backup_path.unlink()
                deleted.append(backup_path)

        return deleted
