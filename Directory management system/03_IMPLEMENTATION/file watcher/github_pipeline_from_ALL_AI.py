# DOC_LINK: DOC-CORE-FILE-WATTCH-GIT-PIPE-PIPELINE-1183
from __future__ import annotations

import DOC-ERROR-UTILS-TIME-145__time
from typing import Dict, List, Optional

from fwgp import events
from fwgp.dispatcher import Dispatcher
from fwgp.git_adapter import (
    GitError,
    add,
    commit,
    push,
    staged_summary,
)
from fwgp.watcher import PollingWatcher
from fwgp import git_adapter


class Pipeline:
    def __init__(self, repo_path: str, dispatcher: Dispatcher, logger, interval_sec: float = 2.0, watcher=None):
        self.repo_path = repo_path
        self.dispatcher = dispatcher
        self.logger = logger
        self.interval_sec = interval_sec
        self.watcher = watcher or PollingWatcher(repo_path)
        self._running = False

    def start(self):
        self._running = True
        self.logger.info("Watcher initialized for %s", self.repo_path)
        while self._running:
            try:
                self._tick()
            except KeyboardInterrupt:
                self.logger.info("Stopping pipeline (KeyboardInterrupt)")
                self._running = False
            except Exception as e:
                self.logger.error("Pipeline error: %s", e)
            time.sleep(self.interval_sec)

    def stop(self):
        self._running = False

    def _tick(self):
        # Optional: pre-sync with remote to reduce push failures
        ctx = self._ctx()
        remote = ctx.get("remote")
        branch = ctx.get("branch")
        if remote and branch:
            allow_pull, strategy = self.dispatcher.before_pull(events.PullRequest(remote=remote, branch=branch), ctx)
            if allow_pull:
                try:
                    git_adapter.pull(self.repo_path, remote, branch)
                except git_adapter.GitError as ge:
                    self.logger.warning("git pull failed: %s", ge)
                # Detect conflicts and notify
                conflicts = git_adapter.list_conflicts(self.repo_path)
                if conflicts:
                    self.logger.warning("Merge conflicts detected: %s", ", ".join(conflicts))
                    self.dispatcher.on_conflict(events.ConflictInfo(files=conflicts), ctx)
            # Always emit afterPull with whether updates or conflicts were seen
            conflicts = git_adapter.list_conflicts(self.repo_path)
            self.dispatcher.after_pull(events.PullResult(updated=True, conflicts=conflicts or None), ctx)

        changes = self.watcher.poll_changes()
        if not changes:
            return
        # Notify plugins about file detections
        for evt in changes:
            self.dispatcher.on_file_detected(evt, ctx)

        # Stage phase
        paths = [c.path.replace(self.repo_path+"/", "").replace(self.repo_path+"\\", "") for c in changes if c.change_type != events.ChangeType.DELETED]
        stage_req = events.StageRequest(paths=paths, repo=self.repo_path, ctx={})
        allow, reasons = self.dispatcher.before_stage(stage_req, ctx)
        if not allow:
            self.logger.warning("Stage blocked by plugins: %s", "; ".join(reasons) or "no reason")
            return
        try:
            add(self.repo_path, paths)
        except GitError as ge:
            self.logger.error("git add failed: %s", ge)
            return
        self.dispatcher.after_stage(stage_req, ctx)

        # Commit phase
        try:
            summary = staged_summary(self.repo_path)
        except GitError as ge:
            self.logger.error("git staged summary failed: %s", ge)
            return
        commit_req = events.CommitRequest(staged_summary=summary, repo=self.repo_path)
        allow, msg_override, sign = self.dispatcher.before_commit(commit_req, ctx)
        if not allow:
            self.logger.warning("Commit blocked by plugins")
            return
        message = msg_override or "chore(auto): update files"
        sha = None
        try:
            sha = commit(self.repo_path, message, sign=bool(sign))
            if sha:
                self.logger.info("Committed %s", sha)
            else:
                self.logger.info("No changes to commit")
        except GitError as ge:
            self.logger.error("git commit failed: %s", ge)
            return
        self.dispatcher.after_commit(sha, ctx)

        # Push phase (best-effort; requires remote tracking set up by TUI)
        remote = ctx.get("remote")
        branch = ctx.get("branch")
        if remote and branch:
            allow_push, force = self.dispatcher.before_push(
                events.PushRequest(remote=remote, branch=branch), ctx
            )
            if allow_push:
                try:
                    push(self.repo_path, remote, branch, force=bool(force))
                    self.logger.info("Pushed to %s/%s", remote, branch)
                except GitError as ge:
                    self.logger.warning("git push failed: %s", ge)
            self.dispatcher.after_push(events.PushRequest(remote=remote, branch=branch), ctx)

    def _ctx(self) -> Dict[str, object]:
        # Execution context shared with plugins
        return {
            "logger": self.logger,
            "repo_path": self.repo_path,
            "remote": None,  # filled by caller via wrapper if needed
            "branch": None,  # filled by caller via wrapper if needed
        }
