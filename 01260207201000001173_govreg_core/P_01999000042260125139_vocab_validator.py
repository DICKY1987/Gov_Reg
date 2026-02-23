"""
VocabularyValidator - Closed-World Vocabulary Enforcement

Validates capability tags and component IDs against frozen vocabularies.
Prevents uncontrolled tag sprawl by enforcing bounded vocabularies.

FILE_ID: 01999000042260125139
"""

import json
from pathlib import Path
from typing import List, Tuple, Optional
from difflib import get_close_matches


class VocabularyValidator:
    """
    Validates values against a closed-world vocabulary.
    
    Supports validation, batch validation, and near-miss suggestions.
    """
    
    def __init__(self, vocab_path: Path):
        """
        Initialize validator with vocabulary file.
        
        Args:
            vocab_path: Path to vocabulary JSON file
        """
        self.vocab_path = Path(vocab_path)
        self.vocab_data = self._load_vocab()
        self.allowed_ids = {entry["id"] for entry in self.vocab_data["entries"]}
    
    def validate(self, value: str) -> bool:
        """
        Validate a single value against the vocabulary.
        
        Args:
            value: Value to validate (e.g., "CAP-REGISTRY-VALIDATE")
            
        Returns:
            True if value is in vocabulary, False otherwise
        """
        return value in self.allowed_ids
    
    def validate_batch(self, values: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a batch of values.
        
        Args:
            values: List of values to validate
            
        Returns:
            Tuple of (valid_values, invalid_values)
        """
        valid = []
        invalid = []
        
        for value in values:
            if self.validate(value):
                valid.append(value)
            else:
                invalid.append(value)
        
        return valid, invalid
    
    def suggest(self, value: str, max_results: int = 3) -> List[str]:
        """
        Suggest near-miss matches for an invalid value.
        
        Args:
            value: Invalid value to find suggestions for
            max_results: Maximum number of suggestions to return
            
        Returns:
            List of suggested matches (empty if none found)
        """
        # Use difflib to find close matches
        suggestions = get_close_matches(
            value,
            self.allowed_ids,
            n=max_results,
            cutoff=0.6  # 60% similarity threshold
        )
        return suggestions
    
    def get_entries_by_component(self, component: str) -> List[dict]:
        """
        Get all vocabulary entries for a specific component.
        
        Args:
            component: Component ID (e.g., "REGISTRY", "IDS")
            
        Returns:
            List of vocabulary entries for that component
        """
        return [
            entry for entry in self.vocab_data["entries"]
            if entry.get("component") == component
        ]
    
    def get_entries_by_domain(self, domain: str) -> List[dict]:
        """
        Get all vocabulary entries for a specific domain.
        
        Args:
            domain: Domain name (e.g., "registry", "governance")
            
        Returns:
            List of vocabulary entries for that domain
        """
        return [
            entry for entry in self.vocab_data["entries"]
            if entry.get("domain") == domain
        ]
    
    def _load_vocab(self) -> dict:
        """Load and parse vocabulary JSON file."""
        if not self.vocab_path.exists():
            raise FileNotFoundError(f"Vocabulary file not found: {self.vocab_path}")
        
        with open(self.vocab_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @property
    def version(self) -> str:
        """Get vocabulary version."""
        return self.vocab_data.get("version", "unknown")
    
    @property
    def frozen_at(self) -> str:
        """Get vocabulary freeze timestamp."""
        return self.vocab_data.get("frozen_at", "unknown")
    
    @property
    def entry_count(self) -> int:
        """Get count of vocabulary entries."""
        return len(self.vocab_data["entries"])
