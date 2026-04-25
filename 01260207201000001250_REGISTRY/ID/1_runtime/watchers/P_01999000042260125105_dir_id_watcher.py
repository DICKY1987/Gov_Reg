"""Continuous enforcement via filesystem watcher (GAP-002).

FILE_ID: 01999000042260125105
PURPOSE: Monitor governed zones for directory changes and enforce .dir_id allocation
PHASE: Phase 2 - Continuous Enforcement
BACKLOG: 01999000042260125103 GAP-002
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, asdict
import sys
import os

# Add parent to path for imports
repo_root = Path(__file__).parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

sys.path.insert(0, str(Path(__file__).parent))
from P_01260207233100000070_dir_identity_resolver import DirectoryIdentityResolver
from P_01260207233100000068_zone_classifier import ZoneClassifier

# Check if watchdog is available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, DirCreatedEvent, DirDeletedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Fallback: define dummy classes
    class Observer:
        pass
    class FileSystemEventHandler:
        pass
    class DirCreatedEvent:
        pass
    class DirDeletedEvent:
        pass
    class FileModifiedEvent:
        pass


@dataclass
class WatcherHandle:
    """Handle for a running watcher."""
    watcher_id: str
    pid: int
    started_at: str
    stop: Callable[[], None]


class DirIdWatcher(FileSystemEventHandler):
    """Filesystem watcher for .dir_id enforcement."""
    
    def __init__(
        self,
        project_root: Path,
        project_root_id: str,
        zone_classifier: ZoneClassifier,
        resolver: DirectoryIdentityResolver,
        on_directory_created: Optional[Callable[[Path], None]] = None,
        on_directory_deleted: Optional[Callable[[Path], None]] = None,
        evidence_dir: Optional[Path] = None
    ):
        """Initialize watcher.
        
        Args:
            project_root: Project root directory
            project_root_id: Project root dir_id
            zone_classifier: Zone classifier instance
            resolver: Directory identity resolver
            on_directory_created: Callback for directory creation
            on_directory_deleted: Callback for directory deletion
            evidence_dir: Directory for evidence artifacts
        """
        self.project_root = project_root
        self.project_root_id = project_root_id
        self.zone_classifier = zone_classifier
        self.resolver = resolver
        self.on_directory_created = on_directory_created
        self.on_directory_deleted = on_directory_deleted
        
        if evidence_dir is None:
            evidence_dir = project_root / ".state" / "evidence" / "watcher_events"
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def on_created(self, event):
        """Handle directory creation events."""
        if not isinstance(event, DirCreatedEvent):
            return
        
        directory = Path(event.src_path)
        
        # Check if in governed zone
        zone = self.zone_classifier.compute_zone(directory)
        if zone != 'governed':
            return
        
        # Auto-allocate .dir_id
        try:
            result = self.resolver.resolve_identity(directory, allocate_if_missing=True)
            
            if result.status == 'allocated':
                self._emit_evidence(
                    "directory_created",
                    directory,
                    {"dir_id": result.dir_id, "zone": zone},
                    "DIR-IDENTITY-010"
                )
                
                # Call user callback
                if self.on_directory_created:
                    self.on_directory_created(directory)
        
        except Exception as e:
            self._emit_evidence(
                "directory_created_error",
                directory,
                {"error": str(e), "zone": zone},
                "DIR-IDENTITY-010"
            )
    
    def on_deleted(self, event):
        """Handle directory deletion events."""
        if not isinstance(event, DirDeletedEvent):
            return
        
        directory = Path(event.src_path)
        
        # Check if had .dir_id
        dir_id_path = directory / ".dir_id"
        if dir_id_path.exists():
            self._emit_evidence(
                "directory_deleted",
                directory,
                {"had_dir_id": True},
                "DIR-IDENTITY-012"
            )
            
            # Call user callback
            if self.on_directory_deleted:
                self.on_directory_deleted(directory)
    
    def on_modified(self, event):
        """Handle .dir_id modification events."""
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith(".dir_id"):
            file_path = Path(event.src_path)
            directory = file_path.parent
            
            # Check if not committed to git
            # (simplified check - full implementation would use git status)
            self._emit_evidence(
                "dir_id_modified",
                directory,
                {"dir_id_path": str(file_path)},
                "DIR-IDENTITY-011"
            )
    
    def _emit_evidence(
        self,
        event_type: str,
        directory: Path,
        details: Dict[str, Any],
        defect_code: str
    ):
        """Emit evidence for watcher event."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S%f")
        evidence_file = self.evidence_dir / f"{timestamp}_event_{event_type}.json"
        
        evidence = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "directory": str(directory),
            "relative_path": str(directory.relative_to(self.project_root)),
            "details": details,
            "defect_code": defect_code
        }
        
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2)


def watch_governed_zones(
    config_path: Path,
    on_directory_created: Optional[Callable[[Path], None]] = None,
    on_directory_deleted: Optional[Callable[[Path], None]] = None,
    daemon: bool = False
) -> WatcherHandle:
    """Start filesystem watcher for governed zones.
    
    Args:
        config_path: Path to IDPKG config
        on_directory_created: Callback when new directory created in governed zone
        on_directory_deleted: Callback when directory deleted
        daemon: If True, run as background daemon
        
    Returns:
        WatcherHandle: Handle to control watcher
        
    Raises:
        ImportError: If watchdog library not available
    """
    if not WATCHDOG_AVAILABLE:
        raise ImportError(
            "watchdog library required for filesystem watching. "
            "Install with: pip install watchdog"
        )
    
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    project_root_value = config.get("project_root_path") or config.get("project_root") or Path.cwd()
    project_root = Path(project_root_value)
    project_root_id = config.get('project_root_id', '01260207201000000000')

    # Initialize components
    zone_classifier = ZoneClassifier(project_root=project_root)
    resolver = DirectoryIdentityResolver(project_root, project_root_id, zone_classifier)
    
    # Create event handler
    event_handler = DirIdWatcher(
        project_root,
        project_root_id,
        zone_classifier,
        resolver,
        on_directory_created,
        on_directory_deleted
    )
    
    # Create observer
    observer = Observer()
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()
    
    watcher_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    pid = os.getpid()
    started_at = datetime.now(timezone.utc).isoformat()
    
    def stop():
        """Stop the watcher."""
        observer.stop()
        observer.join()
    
    handle = WatcherHandle(
        watcher_id=watcher_id,
        pid=pid,
        started_at=started_at,
        stop=stop
    )
    
    if daemon:
        # Run in background
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop()
    
    return handle


if __name__ == "__main__":
    # CLI entry point
    import argparse
    
    parser = argparse.ArgumentParser(description="Watch governed zones for .dir_id enforcement")
    parser.add_argument("--config", type=Path, required=True, help="Path to IDPKG config")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    print(f"Starting watcher for {args.config}")
    handle = watch_governed_zones(args.config, daemon=args.daemon)
    
    if not args.daemon:
        print(f"Watcher started (PID: {handle.pid})")
        print("Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping watcher...")
            handle.stop()
            print("Watcher stopped")
