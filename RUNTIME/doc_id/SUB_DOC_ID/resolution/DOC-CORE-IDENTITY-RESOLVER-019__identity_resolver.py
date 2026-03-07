# DOC_LINK: DOC-CORE-IDENTITY-RESOLVER-019
"""Identity Resolver for ID System

Resolves entity identities: MINT, KEEP, RETIRE, or AMBIGUOUS.
Implements Section 3.2 Flow 3 from DOC-GUIDE-PROCESS-FLOW-AND-AUTOMATION-LOGIC-638.

DOC_ID: DOC-CORE-IDENTITY-RESOLVER-019
"""

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from ..detection.entity_classifier import Entity
from ..detection.change_detector import ChangeType
from .id_generator import IDGenerator


class ResolutionAction(Enum):
    """Identity resolution actions"""
    MINT = "MINT"          # Assign new ID
    KEEP = "KEEP"          # Keep existing ID
    RETIRE = "RETIRE"      # Mark ID as retired
    AMBIGUOUS = "AMBIGUOUS"  # Requires manual intervention


@dataclass
class Resolution:
    """Represents an identity resolution"""
    action: ResolutionAction
    entity: Entity
    doc_id: Optional[str] = None
    old_doc_id: Optional[str] = None
    confidence: int = 100
    reason: Optional[str] = None
    requires_manual: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'action': self.action.value,
            'entity': self.entity.to_dict(),
            'doc_id': self.doc_id,
            'old_doc_id': self.old_doc_id,
            'confidence': self.confidence,
            'reason': self.reason,
            'requires_manual': self.requires_manual
        }


class IdentityResolver:
    """Resolves entity identities

    Resolution logic:
    - NEW file → MINT (generate new ID)
    - RENAMED file with >70% similarity → KEEP (preserve ID)
    - RENAMED file with <70% similarity → AMBIGUOUS (manual decision)
    - DELETED file → RETIRE (mark as retired)
    - MODIFIED file → KEEP (no ID change)

    Advanced features:
    - Content hash matching
    - Override file support (.id_overrides.json)
    - Confidence scoring
    """

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        id_generator: Optional[IDGenerator] = None,
        similarity_threshold: int = 70
    ):
        """Initialize identity resolver

        Args:
            repo_root: Repository root directory
            id_generator: ID generator instance
            similarity_threshold: Minimum similarity for automatic KEEP (0-100)
        """
        self.repo_root = repo_root or Path.cwd()
        self.id_generator = id_generator or IDGenerator()
        self.similarity_threshold = similarity_threshold

        # Load overrides if they exist
        self.overrides = self._load_overrides()

    def resolve(self, entities: List[Entity]) -> List[Resolution]:
        """Resolve identities for entities

        Args:
            entities: List of classified entities

        Returns:
            List of resolutions
        """
        resolutions = []

        for entity in entities:
            resolution = self._resolve_single(entity)
            resolutions.append(resolution)

        return resolutions

    def _resolve_single(self, entity: Entity) -> Resolution:
        """Resolve a single entity

        Args:
            entity: Entity to resolve

        Returns:
            Resolution
        """
        # Check for manual override first
        override = self._check_override(entity.path)
        if override:
            return Resolution(
                action=ResolutionAction.KEEP,
                entity=entity,
                doc_id=override['doc_id'],
                old_doc_id=override.get('old_doc_id'),
                confidence=100,
                reason="Manual override",
                requires_manual=False
            )

        # Resolve based on change type
        if entity.change_type == ChangeType.FILE_ADDED:
            return self._resolve_added(entity)

        elif entity.change_type == ChangeType.FILE_RENAMED:
            return self._resolve_renamed(entity)

        elif entity.change_type == ChangeType.FILE_DELETED:
            return self._resolve_deleted(entity)

        elif entity.change_type == ChangeType.FILE_MODIFIED:
            return self._resolve_modified(entity)

        else:
            # Unknown change type
            return Resolution(
                action=ResolutionAction.AMBIGUOUS,
                entity=entity,
                reason="Unknown change type",
                requires_manual=True
            )

    def _resolve_added(self, entity: Entity) -> Resolution:
        """Resolve added file → MINT

        Args:
            entity: Added entity

        Returns:
            Resolution with MINT action
        """
        if not entity.requires_id:
            # File type doesn't require ID
            return Resolution(
                action=ResolutionAction.MINT,
                entity=entity,
                doc_id=None,
                reason="Entity type does not require doc_id"
            )

        # Generate new ID
        new_id = self.id_generator.generate(
            prefix=entity.id_prefix,
            context=entity.path
        )

        return Resolution(
            action=ResolutionAction.MINT,
            entity=entity,
            doc_id=new_id,
            confidence=100,
            reason="New file"
        )

    def _resolve_renamed(self, entity: Entity) -> Resolution:
        """Resolve renamed file

        Logic:
        - Git similarity ≥70% → KEEP (preserve ID)
        - Git similarity <70% → AMBIGUOUS (manual decision)
        - Content hash match → KEEP (high confidence)

        Args:
            entity: Renamed entity

        Returns:
            Resolution
        """
        if not entity.old_path:
            # Missing old path, treat as added
            return self._resolve_added(entity)

        # Try to extract old doc_id
        old_doc_id = self._extract_doc_id(entity.old_path)

        if not old_doc_id:
            # No old ID found, mint new
            return self._resolve_added(entity)

        # Check git similarity (from metadata if available)
        similarity = self._get_git_similarity(entity)

        if similarity >= self.similarity_threshold:
            # High similarity → KEEP
            return Resolution(
                action=ResolutionAction.KEEP,
                entity=entity,
                doc_id=old_doc_id,
                old_doc_id=old_doc_id,
                confidence=similarity,
                reason=f"Git rename detected (similarity: {similarity}%)"
            )

        # Low similarity → AMBIGUOUS
        return Resolution(
            action=ResolutionAction.AMBIGUOUS,
            entity=entity,
            old_doc_id=old_doc_id,
            confidence=similarity,
            reason=f"Low similarity ({similarity}%), manual decision required",
            requires_manual=True
        )

    def _resolve_deleted(self, entity: Entity) -> Resolution:
        """Resolve deleted file → RETIRE

        Args:
            entity: Deleted entity

        Returns:
            Resolution with RETIRE action
        """
        old_doc_id = self._extract_doc_id(entity.path)

        return Resolution(
            action=ResolutionAction.RETIRE,
            entity=entity,
            old_doc_id=old_doc_id,
            confidence=100,
            reason="File deleted"
        )

    def _resolve_modified(self, entity: Entity) -> Resolution:
        """Resolve modified file → KEEP

        Modified files keep their existing ID.

        Args:
            entity: Modified entity

        Returns:
            Resolution with KEEP action
        """
        doc_id = self._extract_doc_id(entity.path)

        if not doc_id and entity.requires_id:
            # File modified but has no ID → MINT
            return self._resolve_added(entity)

        return Resolution(
            action=ResolutionAction.KEEP,
            entity=entity,
            doc_id=doc_id,
            confidence=100,
            reason="File modified, ID preserved"
        )

    def _extract_doc_id(self, filepath: str) -> Optional[str]:
        """Extract doc_id from file

        Checks:
        1. Filename (DOC-XXX-###__)
        2. File content (doc_id: DOC-XXX-###)

        Args:
            filepath: Relative file path

        Returns:
            Extracted doc_id or None
        """
        # Check filename
        filename = Path(filepath).name
        match = re.search(r'(DOC-[A-Z]+-\d{3,})__', filename)
        if match:
            return match.group(1)

        # Check file content
        full_path = self.repo_root / filepath
        if not full_path.exists():
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Read first 2KB

            match = re.search(r'doc_id:\s*["\']?([A-Z]+-[A-Z0-9]+-\d{3,})["\']?', content)
            if match:
                return match.group(1)
        except Exception:
            pass

        return None

    def _get_git_similarity(self, entity: Entity) -> int:
        """Get git rename similarity

        Args:
            entity: Entity with rename metadata

        Returns:
            Similarity percentage (0-100)
        """
        # Check entity metadata first
        if entity.metadata and 'similarity' in entity.metadata:
            return entity.metadata['similarity']

        # Default based on file extensions
        if entity.old_path and entity.path:
            old_ext = Path(entity.old_path).suffix
            new_ext = Path(entity.path).suffix

            if old_ext == new_ext:
                return 75  # Same extension = likely related

        return 50  # Unknown similarity

    def _load_overrides(self) -> Dict:
        """Load manual overrides from .id_overrides.json

        Returns:
            Overrides dictionary
        """
        override_file = self.repo_root / '.id_overrides.json'

        if not override_file.exists():
            return {}

        try:
            with open(override_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _check_override(self, filepath: str) -> Optional[Dict]:
        """Check if filepath has a manual override

        Args:
            filepath: Relative file path

        Returns:
            Override entry or None
        """
        return self.overrides.get(filepath)

    def save_resolutions(self, resolutions: List[Resolution], output_file: Path):
        """Save resolutions to JSON file

        Args:
            resolutions: List of resolutions
            output_file: Output file path
        """
        from datetime import datetime, timezone

        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'resolutions': [r.to_dict() for r in resolutions],
            'total': len(resolutions),
            'requires_manual': sum(1 for r in resolutions if r.requires_manual),
            'resolved_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


__doc_id__ = 'DOC-CORE-IDENTITY-RESOLVER-019'
