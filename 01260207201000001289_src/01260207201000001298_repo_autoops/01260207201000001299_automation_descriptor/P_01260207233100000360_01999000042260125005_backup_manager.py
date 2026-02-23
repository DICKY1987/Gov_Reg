"""
FILE_ID: 01999000042260125005
Facade: delegates to src/registry_writer/backup_manager.py
"""

import sys
from pathlib import Path
from typing import Optional, List

_repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_repo_root))

from src.registry_writer.backup_manager import BackupManager as CanonicalBackupManager


class BackupManager:
    """Facade: delegates to src/registry_writer/backup_manager.py"""

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        backup_dir: Optional[Path] = None,
        retention_days: int = 30
    ):
        self._canonical = CanonicalBackupManager(registry_path, backup_dir)
        self.retention_days = retention_days

    def create_backup(self, suffix: str = "") -> Path:
        return self._canonical.create_backup(suffix)

    def rollback(self, backup_path: Optional[Path] = None) -> Path:
        return self._canonical.rollback(backup_path)

    def get_latest_backup(self) -> Optional[Path]:
        return self._canonical.get_latest_backup()

    def list_backups(self, limit: Optional[int] = None) -> List[Path]:
        return self._canonical.list_backups(limit)

    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> List[Path]:
        days = retention_days if retention_days is not None else self.retention_days
        return self._canonical.cleanup_old_backups(days)

    def verify_backup(self, backup_path: Path) -> bool:
        return self._canonical.verify_backup(backup_path)
