# DOC_LINK: DOC-CORE-FILE-WATCHER-005
"""File watcher utility for monitoring state file changes.

Provides cross-platform file system monitoring with callbacks for real-time updates.
Uses watchdog library for efficient file system event handling.
"""

# DOC_ID: DOC-CORE-FILE-WATCHER-005

import logging
import DOC-ERROR-UTILS-TIME-145__time
from pathlib import Path
from threading import Thread, Lock
from typing import Callable, Dict, List, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

logger = logging.getLogger(__name__)


class StateFileWatcher(FileSystemEventHandler):
    """File system event handler for state files.
    
    Monitors specified directories and triggers callbacks when files are modified.
    Includes debouncing to avoid excessive callbacks on rapid file changes.
    """
    
    def __init__(
        self,
        callback: Callable[[str], None],
        debounce_seconds: float = 1.0,
        file_patterns: Optional[List[str]] = None
    ):
        """Initialize state file watcher.
        
        Args:
            callback: Function to call when file changes (receives file path)
            debounce_seconds: Minimum time between callbacks for same file
            file_patterns: List of file patterns to watch (e.g., ['*.json'])
                          If None, watches all files
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.file_patterns = file_patterns or []
        
        # Debouncing: track last callback time per file
        self._last_callback_time: Dict[str, float] = {}
        self._lock = Lock()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check file pattern match if patterns specified
        if self.file_patterns:
            if not any(Path(file_path).match(pattern) for pattern in self.file_patterns):
                return
        
        # Debouncing: check if enough time has passed since last callback
        with self._lock:
            current_time = time.time()
            last_time = self._last_callback_time.get(file_path, 0)
            
            if current_time - last_time < self.debounce_seconds:
                # Too soon, skip this event
                return
            
            # Update last callback time
            self._last_callback_time[file_path] = current_time
        
        # Trigger callback
        try:
            logger.info(f"File changed: {file_path}")
            self.callback(file_path)
        except Exception as e:
            logger.error(f"Error in file change callback: {e}")


class FileWatcherManager:
    """Manager for file watching across multiple directories.
    
    Provides high-level interface for watching state files and event logs.
    Handles observer lifecycle and provides clean shutdown.
    """
    
    def __init__(self):
        """Initialize file watcher manager."""
        self.observers: List[Observer] = []
        self._running = False
    
    def watch_directory(
        self,
        directory: str | Path,
        callback: Callable[[str], None],
        recursive: bool = False,
        file_patterns: Optional[List[str]] = None,
        debounce_seconds: float = 1.0
    ) -> Observer:
        """Start watching a directory for file changes.
        
        Args:
            directory: Directory path to watch
            callback: Function to call on file changes
            recursive: Watch subdirectories recursively
            file_patterns: List of file patterns to watch (e.g., ['*.json'])
            debounce_seconds: Debounce interval for callbacks
        
        Returns:
            Observer instance (already started)
        """
        directory = Path(directory)
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return None
        
        # Create event handler
        event_handler = StateFileWatcher(
            callback=callback,
            debounce_seconds=debounce_seconds,
            file_patterns=file_patterns
        )
        
        # Create and start observer
        observer = Observer()
        observer.schedule(event_handler, str(directory), recursive=recursive)
        observer.start()
        
        self.observers.append(observer)
        self._running = True
        
        logger.info(f"Started watching: {directory} (recursive={recursive})")
        return observer
    
    def stop_all(self):
        """Stop all observers and clean up."""
        if not self._running:
            return
        
        logger.info("Stopping all file watchers...")
        
        for observer in self.observers:
            observer.stop()
        
        # Wait for all observers to finish
        for observer in self.observers:
            observer.join(timeout=2.0)
        
        self.observers.clear()
        self._running = False
        
        logger.info("All file watchers stopped")
    
    def is_running(self) -> bool:
        """Check if any watchers are running."""
        return self._running and any(obs.is_alive() for obs in self.observers)


class StateFileWatcherService:
    """High-level service for watching state files in GUI context.
    
    Provides convenient methods for watching PHASE_5 state files and event logs.
    Integrates with GUI refresh mechanisms.
    """
    
    def __init__(
        self,
        state_dir: str | Path,
        event_log_file: Optional[str | Path] = None,
        on_state_change: Optional[Callable[[], None]] = None,
        on_event_change: Optional[Callable[[], None]] = None,
        debounce_seconds: float = 1.5
    ):
        """Initialize state file watcher service.
        
        Args:
            state_dir: Directory containing state JSON files
            event_log_file: Path to events.jsonl file
            on_state_change: Callback when state files change
            on_event_change: Callback when event log changes
            debounce_seconds: Debounce interval
        """
        self.state_dir = Path(state_dir)
        self.event_log_file = Path(event_log_file) if event_log_file else None
        self.on_state_change = on_state_change
        self.on_event_change = on_event_change
        self.debounce_seconds = debounce_seconds
        
        self.manager = FileWatcherManager()
    
    def start(self):
        """Start watching all configured files/directories."""
        # Watch state directory for JSON files
        if self.state_dir.exists() and self.on_state_change:
            self.manager.watch_directory(
                directory=self.state_dir,
                callback=lambda path: self.on_state_change(),
                recursive=False,
                file_patterns=['*.json'],
                debounce_seconds=self.debounce_seconds
            )
            logger.info(f"Watching state dir: {self.state_dir}")
        
        # Watch event log file
        if self.event_log_file and self.event_log_file.exists() and self.on_event_change:
            # Watch parent directory for the specific file
            self.manager.watch_directory(
                directory=self.event_log_file.parent,
                callback=lambda path: self._on_event_file_changed(path),
                recursive=False,
                file_patterns=['events.jsonl'],
                debounce_seconds=self.debounce_seconds
            )
            logger.info(f"Watching event log: {self.event_log_file}")
    
    def _on_event_file_changed(self, changed_path: str):
        """Internal callback for event file changes."""
        if Path(changed_path).name == self.event_log_file.name:
            if self.on_event_change:
                self.on_event_change()
    
    def stop(self):
        """Stop all watchers."""
        self.manager.stop_all()
    
    def is_active(self) -> bool:
        """Check if watcher service is active."""
        return self.manager.is_running()


# Convenience functions
def create_state_watcher(
    state_dir: str,
    on_change: Callable[[], None],
    debounce_seconds: float = 1.5
) -> StateFileWatcherService:
    """Factory function to create a simple state file watcher.
    
    Args:
        state_dir: Directory containing state files
        on_change: Callback when any state file changes
        debounce_seconds: Debounce interval
    
    Returns:
        StateFileWatcherService instance (not started)
    """
    return StateFileWatcherService(
        state_dir=state_dir,
        on_state_change=on_change,
        debounce_seconds=debounce_seconds
    )
