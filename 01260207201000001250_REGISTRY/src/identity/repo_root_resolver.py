"""
repo_root_resolver.py

Repository root inference: Resolve missing repo_root_id for 46 records.

Issue: FCA-011 (Critical)
Symptom: 46 records missing repo_root_id field
Root Cause: Input schema contract not enforced; inference logic incomplete
Fix: Deterministic repo_root_id inference from file paths

Contract: input_contract
Category: Phase
Runner: Must infer repo_root_id before phase completion
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RepoRootResolutionError(Exception):
    """Raised when repo_root_id cannot be resolved."""
    pass


class RepoRootResolver:
    """
    Resolve repository root identifiers for files.
    
    Strategy:
    1. Walk up directory tree looking for .git directory
    2. Use cached mappings for performance
    3. Generate stable repo_root_id from repository path
    4. Validate uniqueness and consistency
    """
    
    def __init__(
        self,
        cache_path: Optional[Path] = None,
        strict_mode: bool = True
    ):
        """
        Initialize repo root resolver.
        
        Args:
            cache_path: Path to repo_root cache
            strict_mode: If True, fail on unresolvable repo_root
        """
        self.cache_path = cache_path or Path(".state/identity/repo_root_cache.json")
        self.strict_mode = strict_mode
        self.cache: Dict[str, str] = {}  # path → repo_root_id
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "inferences": 0,
            "failures": 0
        }
        
        self._load_cache()
    
    def _load_cache(self):
        """Load repo_root cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} repo_root mappings from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            logger.info("No cache found, starting with empty cache")
            self.cache = {}
    
    def _save_cache(self):
        """Persist cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} repo_root mappings to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def resolve(self, file_path: str) -> str:
        """
        Resolve repo_root_id for a file path.
        
        Args:
            file_path: Absolute or relative file path
        
        Returns:
            repo_root_id (20-digit identifier)
        
        Raises:
            RepoRootResolutionError: If repo_root cannot be resolved
        """
        # Normalize path
        path = Path(file_path).resolve()
        path_str = str(path)
        
        # Fast path: check cache
        if path_str in self.cache:
            self.stats["cache_hits"] += 1
            logger.debug(f"Cache hit: {path_str} → {self.cache[path_str]}")
            return self.cache[path_str]
        
        # Check if any parent path is cached
        for parent in path.parents:
            parent_str = str(parent)
            if parent_str in self.cache:
                self.stats["cache_hits"] += 1
                repo_root_id = self.cache[parent_str]
                # Cache this path too
                self.cache[path_str] = repo_root_id
                self._save_cache()
                return repo_root_id
        
        self.stats["cache_misses"] += 1
        
        # Slow path: infer repo_root
        repo_root_id = self._infer_repo_root(path)
        
        if repo_root_id:
            self.cache[path_str] = repo_root_id
            self._save_cache()
            return repo_root_id
        
        # Fail closed
        self.stats["failures"] += 1
        if self.strict_mode:
            raise RepoRootResolutionError(
                f"Cannot resolve repo_root_id for {file_path} (strict_mode=True)"
            )
        else:
            # Return placeholder
            placeholder = "00000000000000000000"  # 20 zeros
            logger.error(f"Unresolved repo_root for {file_path}, returning placeholder")
            return placeholder
    
    def _infer_repo_root(self, file_path: Path) -> Optional[str]:
        """
        Infer repository root by walking up directory tree.
        
        Looks for:
        1. .git directory (Git repository)
        2. .hg directory (Mercurial repository)
        3. .svn directory (Subversion repository)
        4. Repository marker files (.repo_root, REPO_ROOT.txt)
        """
        current = file_path if file_path.is_dir() else file_path.parent
        
        # Walk up directory tree
        for parent in [current] + list(current.parents):
            # Check for version control directories
            if (parent / ".git").exists():
                repo_root_id = self._generate_repo_root_id(parent, "git")
                self.stats["inferences"] += 1
                logger.info(f"Found git repo: {parent} → {repo_root_id}")
                return repo_root_id
            
            if (parent / ".hg").exists():
                repo_root_id = self._generate_repo_root_id(parent, "hg")
                self.stats["inferences"] += 1
                logger.info(f"Found hg repo: {parent} → {repo_root_id}")
                return repo_root_id
            
            if (parent / ".svn").exists():
                repo_root_id = self._generate_repo_root_id(parent, "svn")
                self.stats["inferences"] += 1
                logger.info(f"Found svn repo: {parent} → {repo_root_id}")
                return repo_root_id
            
            # Check for marker files
            if (parent / ".repo_root").exists():
                repo_root_id = self._generate_repo_root_id(parent, "marker")
                self.stats["inferences"] += 1
                logger.info(f"Found repo marker: {parent} → {repo_root_id}")
                return repo_root_id
        
        logger.warning(f"Cannot infer repo_root for {file_path}")
        return None
    
    def _generate_repo_root_id(self, repo_path: Path, repo_type: str) -> str:
        """
        Generate stable 20-digit repo_root_id from repository path.
        
        Uses hash of:
        - Absolute path
        - Repository type
        - Directory name (for uniqueness)
        """
        import hashlib
        
        # Create deterministic seed
        seed_str = f"{repo_path.resolve()}:{repo_type}:{repo_path.name}"
        hash_obj = hashlib.sha256(seed_str.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Convert first 16 chars of hash to decimal
        seed = int(hash_hex[:16], 16)
        repo_root_id = str(seed)[:20].zfill(20)
        
        return repo_root_id
    
    def bulk_resolve(self, file_paths: List[str]) -> Dict[str, Tuple[str, bool]]:
        """
        Resolve repo_root_id for multiple files.
        
        Args:
            file_paths: List of file paths
        
        Returns:
            Dict mapping file_path → (repo_root_id, success)
        """
        results = {}
        for file_path in file_paths:
            try:
                repo_root_id = self.resolve(file_path)
                results[file_path] = (repo_root_id, True)
            except RepoRootResolutionError as e:
                logger.error(f"Failed to resolve repo_root for {file_path}: {e}")
                results[file_path] = (None, False)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get resolution statistics."""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (self.stats["cache_hits"] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "cache_hit_rate": f"{hit_rate:.1f}%"
        }
    
    def create_evidence(self, output_path: Path):
        """Generate evidence report for repo_root resolution."""
        evidence = {
            "component": "repo_root_resolver",
            "contract": "input_contract",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "configuration": {
                "strict_mode": self.strict_mode,
                "cache_path": str(self.cache_path)
            },
            "statistics": self.get_stats(),
            "cache_sample": dict(list(self.cache.items())[:10]) if self.cache else {}
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        logger.info(f"Evidence written to {output_path}")
