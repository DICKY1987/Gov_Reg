#!/usr/bin/env python3
# DOC_LINK: DOC-CORE-ID-SHARED-LIBRARY-001
"""
DOC-CORE-ID-SHARED-LIBRARY-001
Shared ID validation/parsing/formatting logic for all ID types.

This is the taxonomy-driven unified ID library that replaces
duplicated logic across DOC_ID, PATTERN_ID, and TRIGGER_ID subsystems.

Design:
- Single implementation for all ID operations
- Driven by id_taxonomy.json configuration
- Type-safe operations with clear error messages
- Non-breaking: can coexist with legacy implementations
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union


class IDType(Enum):
    """Supported ID types."""
    DOC_ID = "DOC_ID"
    PATTERN_ID = "PATTERN_ID"
    TRIGGER_ID = "TRIGGER_ID"
    ARTIFACT_ID = "ARTIFACT_ID"
    REQUIREMENT_ID = "REQUIREMENT_ID"
    SECTION_ID = "SECTION_ID"


class IDScope(Enum):
    """ID scope levels."""
    GLOBAL = "global"
    LOCAL = "local"
    SUBSYSTEM = "subsystem"


@dataclass
class IDFormat:
    """ID format specification from taxonomy."""
    id_type: IDType
    prefix: str
    pattern: str
    scope: IDScope
    description: str
    example: str

    def __post_init__(self):
        """Compile regex pattern."""
        self._compiled_pattern = re.compile(self.pattern)

    def matches(self, id_str: str) -> bool:
        """Check if ID string matches this format."""
        return bool(self._compiled_pattern.fullmatch(id_str))


class IDValidationError(Exception):
    """Raised when ID validation fails."""
    pass


class IDCore:
    """
    Core ID operations library.

    Provides unified operations for all ID types:
    - Validation
    - Parsing
    - Formatting
    - Normalization
    """

    # Default formats (can be overridden by taxonomy)
    DEFAULT_FORMATS = {
        IDType.DOC_ID: IDFormat(
            id_type=IDType.DOC_ID,
            prefix="DOC",
            pattern=r"DOC-[A-Z][A-Z0-9_-]+-\d{3,4}",
            scope=IDScope.GLOBAL,
            description="Document ID",
            example="DOC-CORE-REGISTRY-1171"
        ),
        IDType.PATTERN_ID: IDFormat(
            id_type=IDType.PATTERN_ID,
            prefix="PAT",
            pattern=r"PAT-[A-Z][A-Z0-9_-]+-\d{3}",
            scope=IDScope.GLOBAL,
            description="Pattern ID",
            example="PAT-E2E-VALIDATION-001"
        ),
        IDType.TRIGGER_ID: IDFormat(
            id_type=IDType.TRIGGER_ID,
            prefix="TRIG",
            pattern=r"TRIG-[A-Z][A-Z0-9_-]+-\d{3}",
            scope=IDScope.SUBSYSTEM,
            description="Trigger ID",
            example="TRIG-DOC-SCAN-001"
        ),
        IDType.ARTIFACT_ID: IDFormat(
            id_type=IDType.ARTIFACT_ID,
            prefix="A",
            pattern=r"A-[A-Z][A-Z0-9_-]+-\d{3}",
            scope=IDScope.GLOBAL,
            description="Artifact ID",
            example="A-SCHEMA-001"
        ),
        IDType.REQUIREMENT_ID: IDFormat(
            id_type=IDType.REQUIREMENT_ID,
            prefix="R",
            pattern=r"R-[A-Z][A-Z0-9_-]+-\d{3}",
            scope=IDScope.GLOBAL,
            description="Requirement ID",
            example="R-DETERM-001"
        ),
        IDType.SECTION_ID: IDFormat(
            id_type=IDType.SECTION_ID,
            prefix="S",
            pattern=r"S-[A-Z][A-Z0-9_-]+",
            scope=IDScope.GLOBAL,
            description="Section ID",
            example="S-ENFORCEMENT"
        )
    }

    def __init__(self, formats: Optional[Dict[IDType, IDFormat]] = None):
        """
        Initialize ID core.

        Args:
            formats: Optional ID format overrides (uses defaults if None)
        """
        self.formats = formats or self.DEFAULT_FORMATS

    @classmethod
    def from_taxonomy(cls, taxonomy_path: Path) -> 'IDCore':
        """
        Create ID core from taxonomy file.

        Args:
            taxonomy_path: Path to id_taxonomy.json

        Returns:
            Configured IDCore instance
        """
        import json

        with open(taxonomy_path, 'r') as f:
            taxonomy = json.load(f)

        formats = {}
        for type_name, type_config in taxonomy.get('id_types', {}).items():
            try:
                id_type = IDType[type_name]
                formats[id_type] = IDFormat(
                    id_type=id_type,
                    prefix=type_config['prefix'],
                    pattern=type_config['pattern'],
                    scope=IDScope[type_config.get('scope', 'GLOBAL').upper()],
                    description=type_config.get('description', ''),
                    example=type_config.get('example', '')
                )
            except (KeyError, ValueError):
                # Skip unknown ID types
                pass

        return cls(formats=formats)

    def validate(self, id_str: str, id_type: Optional[IDType] = None) -> bool:
        """
        Validate an ID string.

        Args:
            id_str: ID string to validate
            id_type: Expected ID type (auto-detect if None)

        Returns:
            True if valid

        Raises:
            IDValidationError: If validation fails
        """
        if not id_str:
            raise IDValidationError("ID string is empty")

        # Auto-detect type if not specified
        if id_type is None:
            id_type = self.detect_type(id_str)
            if id_type is None:
                raise IDValidationError(f"Unknown ID format: {id_str}")

        # Get format
        if id_type not in self.formats:
            raise IDValidationError(f"Unsupported ID type: {id_type}")

        fmt = self.formats[id_type]

        # Validate format
        if not fmt.matches(id_str):
            raise IDValidationError(
                f"Invalid {id_type.value} format: {id_str}\n"
                f"Expected pattern: {fmt.pattern}\n"
                f"Example: {fmt.example}"
            )

        return True

    def detect_type(self, id_str: str) -> Optional[IDType]:
        """
        Auto-detect ID type from string.

        Args:
            id_str: ID string

        Returns:
            Detected IDType or None
        """
        for id_type, fmt in self.formats.items():
            if fmt.matches(id_str):
                return id_type

        return None

    def parse(self, id_str: str, id_type: Optional[IDType] = None) -> Dict[str, str]:
        """
        Parse ID into components.

        Args:
            id_str: ID string to parse
            id_type: Expected ID type (auto-detect if None)

        Returns:
            Dictionary of components (prefix, category, number, etc.)

        Raises:
            IDValidationError: If parsing fails
        """
        # Validate first
        self.validate(id_str, id_type)

        # Auto-detect if needed
        if id_type is None:
            id_type = self.detect_type(id_str)

        # Parse based on common pattern: PREFIX-CATEGORY-NUMBER
        parts = id_str.split('-')

        result = {
            "full_id": id_str,
            "prefix": parts[0] if parts else "",
            "type": id_type.value if id_type else "UNKNOWN"
        }

        if len(parts) >= 2:
            # Extract category (everything between prefix and number)
            result["category"] = '-'.join(parts[1:-1])
            result["number"] = parts[-1]

        return result

    def format(
        self,
        id_type: IDType,
        category: str,
        number: Union[int, str],
        width: int = 3
    ) -> str:
        """
        Format an ID from components.

        Args:
            id_type: Type of ID to create
            category: Category/subsystem name
            number: ID number
            width: Minimum width for number (with zero-padding)

        Returns:
            Formatted ID string

        Raises:
            IDValidationError: If components are invalid
        """
        if id_type not in self.formats:
            raise IDValidationError(f"Unsupported ID type: {id_type}")

        fmt = self.formats[id_type]

        # Normalize category (uppercase, replace spaces/underscores with hyphens)
        category = category.upper().replace('_', '-').replace(' ', '-')

        # Format number with padding
        if isinstance(number, int):
            number_str = str(number).zfill(width)
        else:
            number_str = str(number)

        # Build ID
        id_str = f"{fmt.prefix}-{category}-{number_str}"

        # Validate result
        try:
            self.validate(id_str, id_type)
        except IDValidationError as e:
            raise IDValidationError(f"Generated invalid ID: {e}")

        return id_str

    def normalize(self, id_str: str, id_type: Optional[IDType] = None) -> str:
        """
        Normalize an ID to canonical format.

        Args:
            id_str: ID string to normalize
            id_type: Expected ID type (auto-detect if None)

        Returns:
            Normalized ID string

        Raises:
            IDValidationError: If ID is invalid
        """
        # Parse and re-format
        components = self.parse(id_str, id_type)

        if not components.get("category") or not components.get("number"):
            # Can't normalize if missing components
            return id_str

        detected_type = IDType[components["type"]]

        return self.format(
            id_type=detected_type,
            category=components["category"],
            number=components["number"]
        )


# Convenience functions for backward compatibility

_default_core = IDCore()


def validate_id(id_str: str, id_type: Optional[str] = None) -> bool:
    """Validate an ID using default core."""
    type_enum = IDType[id_type] if id_type else None
    return _default_core.validate(id_str, type_enum)


def parse_id(id_str: str, id_type: Optional[str] = None) -> Dict[str, str]:
    """Parse an ID using default core."""
    type_enum = IDType[id_type] if id_type else None
    return _default_core.parse(id_str, type_enum)


def format_id(id_type: str, category: str, number: Union[int, str]) -> str:
    """Format an ID using default core."""
    return _default_core.format(IDType[id_type], category, number)


if __name__ == "__main__":
    # Demo usage
    core = IDCore()

    print("=== ID Core Library Demo ===\n")

    # Validate
    test_ids = [
        "DOC-CORE-REGISTRY-1171",
        "PAT-E2E-VALIDATION-001",
        "TRIG-DOC-SCAN-001"
    ]

    for test_id in test_ids:
        try:
            core.validate(test_id)
            print(f"✓ Valid: {test_id}")

            # Parse
            components = core.parse(test_id)
            print(f"  Components: {components}")
        except IDValidationError as e:
            print(f"✗ Invalid: {test_id} - {e}")

        print()
