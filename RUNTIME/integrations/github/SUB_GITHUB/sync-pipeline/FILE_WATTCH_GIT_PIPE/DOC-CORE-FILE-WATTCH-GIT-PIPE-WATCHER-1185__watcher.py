# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-WATCHER-1185
from __future__ import annotations

import os
import DOC-ERROR-UTILS-TIME-145__time
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from fwgp.events import ChangeType, FileDetectedEvent


def _iter_files(root: str) -> Iterable[Tuple[str, float]]:
    for base, dirs, files in os.walk(root):
        # Skip .git directory
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            p = Path(base) / f
            try:
                stat = p.stat()
            except OSError:
                continue
            yield str(p), stat.st_mtime


class PollingWatcher:
    def __init__(self, root: str, debounce_sec: float = 0.5):
        self.root = root
        self.debounce_sec = debounce_sec
        self.snapshot: Dict[str, float] = {}

    def initial_scan(self):
        self.snapshot = {p: m for p, m in _iter_files(self.root)}

    def poll_changes(self) -> List[FileDetectedEvent]:
        now = time.time()
        current = {p: m for p, m in _iter_files(self.root)}
        events: List[FileDetectedEvent] = []
        # detect created/modified
        for p, m in current.items():
            old = self.snapshot.get(p)
            if old is None:
                events.append(FileDetectedEvent(path=p, change_type=ChangeType.CREATED, ts=now, repo=self.root))
            elif m - old >= self.debounce_sec:
                events.append(FileDetectedEvent(path=p, change_type=ChangeType.MODIFIED, ts=now, repo=self.root))
        # detect deleted
        for p in set(self.snapshot.keys()) - set(current.keys()):
            events.append(FileDetectedEvent(path=p, change_type=ChangeType.DELETED, ts=now, repo=self.root))
        self.snapshot = current
        return events


class WatchdogWatcher:
    def __init__(self, root: str):
        try:
            from watchdog.observers import Observer  # type: ignore
            from watchdog.events import FileSystemEventHandler  # type: ignore
        except Exception as e:
            raise ImportError("watchdog not installed") from e

        self.root = root
        self._observer = Observer()
        self._events: List[FileDetectedEvent] = []
        self._handler = self._make_handler()
        self._observer.schedule(self._handler, root, recursive=True)
        self._observer.start()

    def _make_handler(self):
        from watchdog.events import FileSystemEventHandler  # type: ignore

        class Handler(FileSystemEventHandler):
            def __init__(self, outer):
                self.outer = outer

            def on_created(self, event):
                if event.is_directory or ".git" in event.src_path:
                    return
                self.outer._events.append(
                    FileDetectedEvent(event.src_path, ChangeType.CREATED, time.time(), self.outer.root)
                )

            def on_modified(self, event):
                if event.is_directory or ".git" in event.src_path:
                    return
                self.outer._events.append(
                    FileDetectedEvent(event.src_path, ChangeType.MODIFIED, time.time(), self.outer.root)
                )

            def on_deleted(self, event):
                if event.is_directory or ".git" in event.src_path:
                    return
                self.outer._events.append(
                    FileDetectedEvent(event.src_path, ChangeType.DELETED, time.time(), self.outer.root)
                )

        return Handler(self)

    def poll_changes(self) -> List[FileDetectedEvent]:
        evts = list(self._events)
        self._events.clear()
        return evts


def get_watcher(root: str, prefer_os_events: bool = True):
    if prefer_os_events:
        try:
            return WatchdogWatcher(root)
        except Exception:
            pass
    w = PollingWatcher(root)
    w.initial_scan()
    return w
