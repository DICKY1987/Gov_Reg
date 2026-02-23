"""
Staleness Checker
Detects when context or plan has become stale and needs refresh.
"""
import json
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime, timedelta

from .hash_utils import compute_file_hash, compute_json_hash


class StalenessChecker:
    """Checks staleness of context bundles and plans"""
    
    def __init__(self, staleness_threshold_hours: int = 24):
        self.staleness_threshold = timedelta(hours=staleness_threshold_hours)
    
    def check_context_staleness(self, context_bundle: Dict, 
                                context_bundle_path: Path) -> Tuple[str, Dict]:
        """Check if context bundle is stale
        
        Args:
            context_bundle: Context bundle dictionary
            context_bundle_path: Path to context bundle file
            
        Returns:
            Tuple of (status, details)
            status: "FRESH" | "STALE" | "UNKNOWN"
        """
        details = {
            "check_timestamp": datetime.utcnow().isoformat() + "Z",
            "context_bundle_path": str(context_bundle_path),
            "reasons": []
        }
        
        # Check file modification time
        if context_bundle_path.exists():
            file_mtime = datetime.fromtimestamp(context_bundle_path.stat().st_mtime)
            age = datetime.now() - file_mtime
            
            if age > self.staleness_threshold:
                details["reasons"].append(
                    f"Context bundle age ({age.total_seconds()/3600:.1f}h) exceeds threshold"
                )
                details["age_hours"] = age.total_seconds() / 3600
                return "STALE", details
        
        # Check recent_changes timestamp
        if "recent_changes" in context_bundle and context_bundle["recent_changes"]:
            latest_commit = context_bundle["recent_changes"][0]
            commit_time = datetime.fromisoformat(latest_commit["timestamp"].replace('Z', '+00:00'))
            
            # If there are commits newer than threshold, context might be stale
            age_since_commit = datetime.now(commit_time.tzinfo) - commit_time
            if age_since_commit > self.staleness_threshold:
                details["reasons"].append("No recent commits in context")
                details["latest_commit_age_hours"] = age_since_commit.total_seconds() / 3600
        
        # If no staleness indicators found, mark as FRESH
        if not details["reasons"]:
            details["status"] = "All checks passed"
            return "FRESH", details
        
        return "STALE", details
    
    def check_plan_staleness(self, plan: Dict, context_bundle: Dict) -> Tuple[str, Dict]:
        """Check if plan references stale context
        
        Args:
            plan: Plan dictionary
            context_bundle: Current context bundle
            
        Returns:
            Tuple of (status, details)
        """
        details = {
            "check_timestamp": datetime.utcnow().isoformat() + "Z",
            "reasons": []
        }
        
        # Check if plan references context bundle hash
        if "metadata" in plan and "context_bundle_hash" in plan["metadata"]:
            expected_hash = plan["metadata"]["context_bundle_hash"]
            actual_hash = compute_json_hash(context_bundle)
            
            if expected_hash != actual_hash:
                details["reasons"].append("Context bundle hash mismatch")
                details["expected_hash"] = expected_hash
                details["actual_hash"] = actual_hash
                return "STALE", details
        
        # Check plan creation time
        if "metadata" in plan and "created_at" in plan["metadata"]:
            plan_created = datetime.fromisoformat(
                plan["metadata"]["created_at"].replace('Z', '+00:00')
            )
            age = datetime.now(plan_created.tzinfo) - plan_created
            
            if age > self.staleness_threshold:
                details["reasons"].append(f"Plan age ({age.total_seconds()/3600:.1f}h) exceeds threshold")
                details["plan_age_hours"] = age.total_seconds() / 3600
                return "STALE", details
        
        if not details["reasons"]:
            details["status"] = "All checks passed"
            return "FRESH", details
        
        return "UNKNOWN", details
    
    def should_stop_due_to_staleness(self, status: str, strict_mode: bool = False) -> bool:
        """Determine if staleness should halt processing
        
        Args:
            status: Staleness status from check
            strict_mode: If True, STALE triggers stop
            
        Returns:
            True if processing should stop
        """
        if status == "STALE" and strict_mode:
            return True
        return False
