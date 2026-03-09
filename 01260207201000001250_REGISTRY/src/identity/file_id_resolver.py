"""
file_id_resolver.py

Identity contract enforcement: Resolve SHA256 to official 20-digit file_id.

Issue: FCA-005 (Critical)
Symptom: file_id promotion blocked because sha256-based lookups cannot resolve
         to official 20-digit file_id required for registry mutation.
Root Cause: Identity promotion contract incomplete; mutation/executor paths must
            fail closed until official file_id resolution proven.
Fix: Implement deterministic file_id resolution with fallback policy.

Contract: identity_contract
Category: Mutation
Runner: Must query authoritative file_id source before allowing promotion
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class FileIDResolutionError(Exception):
    """Raised when file_id cannot be resolved from sha256."""
    pass


class FileIDResolver:
    """
    Resolve SHA256 hashes to official 20-digit file_id values.
    
    Implements identity_contract: SHA256 → file_id mapping must be deterministic
    and verifiable before any registry mutation occurs.
    
    Resolution Strategy:
    1. Check local cache (fast path)
    2. Query authoritative source (filesystem metadata, registry)
    3. Generate file_id if allowed (based on policy)
    4. Fail closed if unresolvable and strict mode enabled
    """
    
    def __init__(
        self,
        cache_path: Optional[Path] = None,
        strict_mode: bool = True,
        allow_generation: bool = False
    ):
        """
        Initialize file_id resolver.
        
        Args:
            cache_path: Path to file_id cache (JSON mapping sha256 → file_id)
            strict_mode: If True, fail on unresolvable file_id; if False, allow fallback
            allow_generation: If True, generate new file_id when not found (unsafe for production)
        """
        self.cache_path = cache_path or Path(".state/identity/file_id_cache.json")
        self.strict_mode = strict_mode
        self.allow_generation = allow_generation
        self.cache: Dict[str, str] = {}
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "generations": 0,
            "failures": 0
        }
        
        self._load_cache()
    
    def _load_cache(self):
        """Load file_id cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} file_id mappings from cache")
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
            logger.info(f"Saved {len(self.cache)} file_id mappings to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def resolve(self, sha256: str, context: Optional[Dict] = None) -> str:
        """
        Resolve SHA256 to official 20-digit file_id.
        
        Args:
            sha256: 64-character hex SHA256 hash
            context: Optional context (file_path, registry_id, etc.)
        
        Returns:
            20-digit file_id string
        
        Raises:
            FileIDResolutionError: If file_id cannot be resolved and strict_mode=True
        """
        # Validate SHA256 format
        if not self._is_valid_sha256(sha256):
            raise ValueError(f"Invalid SHA256 format: {sha256}")
        
        # Fast path: check cache
        if sha256 in self.cache:
            self.stats["cache_hits"] += 1
            logger.debug(f"Cache hit: {sha256} → {self.cache[sha256]}")
            return self.cache[sha256]
        
        self.stats["cache_misses"] += 1
        logger.debug(f"Cache miss: {sha256}")
        
        # Slow path: query authoritative sources
        file_id = self._query_authoritative_sources(sha256, context)
        
        if file_id:
            self._add_to_cache(sha256, file_id)
            return file_id
        
        # Fallback: generate file_id if allowed
        if self.allow_generation:
            file_id = self._generate_file_id(sha256, context)
            self.stats["generations"] += 1
            logger.warning(f"Generated file_id for {sha256}: {file_id}")
            self._add_to_cache(sha256, file_id)
            return file_id
        
        # Fail closed
        self.stats["failures"] += 1
        if self.strict_mode:
            raise FileIDResolutionError(
                f"Cannot resolve file_id for SHA256 {sha256} "
                f"(strict_mode=True, allow_generation=False)"
            )
        else:
            # Return placeholder in lenient mode
            placeholder = f"UNRESOLVED_{sha256[:16]}"
            logger.error(f"Unresolved file_id for {sha256}, returning placeholder: {placeholder}")
            return placeholder
    
    def _is_valid_sha256(self, sha256: str) -> bool:
        """Validate SHA256 hash format."""
        return isinstance(sha256, str) and len(sha256) == 64 and all(c in '0123456789abcdef' for c in sha256.lower())
    
    def _query_authoritative_sources(self, sha256: str, context: Optional[Dict]) -> Optional[str]:
        """
        Query authoritative sources for file_id.
        
        Priority order:
        1. Context hint (if file_id provided in context)
        2. Registry lookup (query existing registry by sha256)
        3. Filesystem metadata (if file_path provided)
        """
        # Check context for explicit file_id
        if context and "file_id" in context:
            file_id = context["file_id"]
            if self._is_valid_file_id(file_id):
                logger.info(f"Found file_id in context: {file_id}")
                return file_id
        
        # Check registry (would query actual registry here)
        # For now, this is a stub - real implementation would query registry DB
        file_id = self._query_registry(sha256)
        if file_id:
            return file_id
        
        # Check filesystem metadata
        if context and "file_path" in context:
            file_id = self._query_filesystem(context["file_path"], sha256)
            if file_id:
                return file_id
        
        return None
    
    def _query_registry(self, sha256: str) -> Optional[str]:
        """Query registry for existing file_id (stub for now)."""
        # TODO: Implement actual registry query
        # This would connect to the registry database and query by sha256
        return None
    
    def _query_filesystem(self, file_path: str, sha256: str) -> Optional[str]:
        """Query filesystem metadata for file_id."""
        path = Path(file_path)
        if not path.exists():
            return None
        
        # Check for sidecar metadata file
        metadata_path = path.with_suffix(path.suffix + '.meta.json')
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    if "file_id" in metadata and self._is_valid_file_id(metadata["file_id"]):
                        logger.info(f"Found file_id in metadata: {metadata['file_id']}")
                        return metadata["file_id"]
            except Exception as e:
                logger.warning(f"Failed to read metadata file: {e}")
        
        return None
    
    def _generate_file_id(self, sha256: str, context: Optional[Dict]) -> str:
        """
        Generate new file_id (only when allow_generation=True).
        
        WARNING: This should only be used in development/testing.
        Production should always use pre-existing authoritative file_id.
        """
        # Generate deterministic 20-digit file_id from sha256
        # Use first 20 chars of sha256 as seed for deterministic generation
        seed = int(sha256[:16], 16)
        file_id = str(seed)[:20].zfill(20)
        
        logger.warning(f"GENERATED file_id {file_id} from SHA256 {sha256}")
        return file_id
    
    def _is_valid_file_id(self, file_id: str) -> bool:
        """Validate file_id format (20-digit numeric string)."""
        return isinstance(file_id, str) and len(file_id) == 20 and file_id.isdigit()
    
    def _add_to_cache(self, sha256: str, file_id: str):
        """Add mapping to cache and persist."""
        self.cache[sha256] = file_id
        self._save_cache()
    
    def bulk_resolve(self, sha256_list: list) -> Dict[str, Tuple[str, bool]]:
        """
        Resolve multiple SHA256 hashes in batch.
        
        Args:
            sha256_list: List of SHA256 hashes
        
        Returns:
            Dict mapping sha256 → (file_id, success)
        """
        results = {}
        for sha256 in sha256_list:
            try:
                file_id = self.resolve(sha256)
                results[sha256] = (file_id, True)
            except FileIDResolutionError as e:
                logger.error(f"Failed to resolve {sha256}: {e}")
                results[sha256] = (None, False)
        
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
        """Generate evidence report for file_id resolution."""
        evidence = {
            "component": "file_id_resolver",
            "contract": "identity_contract",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "configuration": {
                "strict_mode": self.strict_mode,
                "allow_generation": self.allow_generation,
                "cache_path": str(self.cache_path)
            },
            "statistics": self.get_stats(),
            "cache_sample": dict(list(self.cache.items())[:10]) if self.cache else {}
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        logger.info(f"Evidence written to {output_path}")
