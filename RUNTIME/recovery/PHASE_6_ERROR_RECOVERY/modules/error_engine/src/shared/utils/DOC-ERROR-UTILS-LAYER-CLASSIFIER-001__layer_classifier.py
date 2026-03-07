# DOC_LINK: DOC-ERROR-UTILS-LAYER-CLASSIFIER-001
"""5-Layer Error Classification Utility

Maps error categories to code quality layers for error detection.
Layer 0 (Syntax) is highest priority, Layer 4 (Security) is lowest.
"""

# DOC_ID: DOC-ERROR-UTILS-LAYER-CLASSIFIER-001

from typing import Dict

# Category to layer mapping (0-4, where 0 = highest priority)
CATEGORY_TO_LAYER: Dict[str, int] = {
    # Layer 0 - Syntax errors (blocks everything)
    "syntax": 0,
    "parse_error": 0,
    "indentation": 0,
    # Layer 1 - Type errors (breaks type safety)
    "type": 1,
    "type_error": 1,
    "incompatible_types": 1,
    # Layer 2 - Linting/Convention errors (code quality)
    "convention": 2,
    "lint": 2,
    "complexity": 2,
    "naming": 2,
    "unused": 2,
    # Layer 3 - Style/Formatting errors (cosmetic)
    "style": 3,
    "formatting": 3,
    "whitespace": 3,
    # Layer 4 - Security errors (critical but contextual)
    "security": 4,
    "vulnerability": 4,
    "secret": 4,
}

# Layer priority (lower number = higher priority)
LAYER_PRIORITY: Dict[int, int] = {
    0: 1,  # Syntax - blocks everything
    1: 2,  # Type - breaks contracts
    2: 3,  # Linting - code quality
    3: 4,  # Style - cosmetic
    4: 5,  # Security - critical but contextual
}


def classify_error_layer(category: str) -> int:
    """
    Classify error category into code quality layer.

    Args:
        category: Error category (e.g., "syntax", "type")

    Returns:
        Layer number (0-4), defaults to Layer 2 (linting) if unknown
    """
    return CATEGORY_TO_LAYER.get(category, 2)


def get_layer_priority(layer: int) -> int:
    """
    Get priority for a layer (lower = higher priority).

    Args:
        layer: Layer number (0-4)

    Returns:
        Priority value (1-5)
    """
    return LAYER_PRIORITY.get(layer, 3)


def is_auto_repairable(category: str, has_fix_method: bool = False) -> bool:
    """
    Determine if an error category is typically auto-repairable.

    Args:
        category: Error category
        has_fix_method: Whether plugin has a fix() method

    Returns:
        True if auto-repairable
    """
    layer = classify_error_layer(category)

    # Layer 3 (style/formatting) is usually auto-repairable if plugin supports it
    if layer == 3 and has_fix_method:
        return True

    # Layer 2 (linting) sometimes auto-repairable
    if layer == 2 and has_fix_method:
        return True

    # Layer 0 (syntax) and Layer 1 (type) typically require human intervention
    # Layer 4 (security) requires careful review
    return False


def classify_issue(issue) -> int:
    """
    Classify a PluginIssue into code quality layer.

    Args:
        issue: PluginIssue object with category field

    Returns:
        Layer number (0-4)
    """
    return classify_error_layer(issue.category)
