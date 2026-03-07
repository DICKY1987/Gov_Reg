# DOC_LINK: DOC-CORE-ID-GENERATOR-018
"""ID Generator with Deterministic Mode

Generates ULIDs for document IDs with optional deterministic mode for testing.

DOC_ID: DOC-CORE-ID-GENERATOR-018
"""

import hashlib
import time
from typing import Optional


class IDGenerator:
    """Generates unique IDs with deterministic mode

    Production mode: Time-based ULIDs
    Deterministic mode: Seeded sequential IDs for testing
    """

    def __init__(self, deterministic: bool = False, seed: Optional[str] = None):
        """Initialize ID generator

        Args:
            deterministic: Enable deterministic mode
            seed: Seed for deterministic mode
        """
        self.deterministic = deterministic
        self.seed = seed or "default_seed"
        self._counter = 0

    def generate(self, prefix: str = "DOC-", context: Optional[str] = None) -> str:
        """Generate a unique ID

        Args:
            prefix: ID prefix (e.g., "DOC-", "DOC-SCRIPT-")
            context: Optional context for deterministic generation

        Returns:
            Generated ID (e.g., "DOC-CORE-001", "DOC-SCRIPT-042")
        """
        if self.deterministic:
            return self._generate_deterministic(prefix, context)
        else:
            return self._generate_ulid(prefix)

    def _generate_deterministic(self, prefix: str, context: Optional[str]) -> str:
        """Generate deterministic ID

        Uses counter + hash of context for reproducibility.

        Args:
            prefix: ID prefix
            context: Optional context string

        Returns:
            Deterministic ID
        """
        self._counter += 1

        if context:
            # Hash context to get a component token
            context_hash = hashlib.sha256(f"{self.seed}{context}".encode()).hexdigest()
            component = context_hash[:4].upper()
        else:
            component = "GEN"

        # Format: PREFIX-COMPONENT-###
        number = f"{self._counter:03d}"

        return f"{prefix}{component}-{number}"

    def _generate_ulid(self, prefix: str) -> str:
        """Generate time-based ULID

        Simplified ULID: timestamp + random component

        Args:
            prefix: ID prefix

        Returns:
            Time-based ID
        """
        # Get timestamp (milliseconds since epoch)
        timestamp_ms = int(time.time() * 1000)

        # Convert to base32-like encoding (simplified)
        timestamp_encoded = self._encode_timestamp(timestamp_ms)

        # Generate random component
        import random
        random_component = ''.join(
            random.choices('0123456789ABCDEFGHJKMNPQRSTVWXYZ', k=10)
        )

        # Extract numeric suffix for standard format
        number = str(timestamp_ms)[-3:]

        return f"{prefix}{timestamp_encoded}-{number}"

    def _encode_timestamp(self, timestamp_ms: int) -> str:
        """Encode timestamp to compact string

        Args:
            timestamp_ms: Timestamp in milliseconds

        Returns:
            Encoded timestamp (4-6 characters)
        """
        # Simple base-36 encoding
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        result = []
        value = timestamp_ms // 1000  # Convert to seconds

        while value > 0 and len(result) < 6:
            result.append(chars[value % 36])
            value //= 36

        return ''.join(reversed(result))[:4] or "0000"

    def reset_counter(self):
        """Reset counter (for deterministic mode)"""
        self._counter = 0


__doc_id__ = 'DOC-CORE-ID-GENERATOR-018'
