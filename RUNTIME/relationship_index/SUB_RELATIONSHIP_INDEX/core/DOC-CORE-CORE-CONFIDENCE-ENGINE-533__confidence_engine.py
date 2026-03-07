# DOC_LINK: DOC-CORE-CORE-CONFIDENCE-ENGINE-533
"""
Confidence Engine

Loads confidence rules from confidence_rules.yaml and provides confidence scoring
for relationship edges based on extraction method and target resolution status.

Confidence Model:
- 1.0 (high): Edge verified via AST/schema parsing, target found in registry
- 0.0 (broken): Edge extracted but target doc_id not found in registry
"""
# DOC_ID: DOC-CORE-CORE-CONFIDENCE-ENGINE-533

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfidenceEngine:
    """
    Rule-based confidence scoring engine for relationship edges.

    Loads confidence_rules.yaml and maps extraction methods to confidence tiers.
    """

    def __init__(self, rules_path: Optional[Path] = None):
        """
        Initialize the confidence engine.

        Args:
            rules_path: Path to confidence_rules.yaml. If None, uses default location
                       (schemas/confidence_rules.yaml relative to this file's parent)
        """
        if rules_path is None:
            # Default: SUB_RELATIONSHIP_INDEX/schemas/confidence_rules.yaml
            current_file = Path(__file__).resolve()
            subsystem_root = current_file.parent.parent  # Go up from core/ to SUB_RELATIONSHIP_INDEX/
            rules_path = subsystem_root / "schemas" / "confidence_rules.yaml"

        self.rules_path = rules_path
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """
        Load confidence rules from YAML file.

        Returns:
            Dictionary containing confidence rules

        Raises:
            FileNotFoundError: If rules file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.rules_path.exists():
            raise FileNotFoundError(
                f"Confidence rules file not found: {self.rules_path}"
            )

        with open(self.rules_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)

        return rules

    def get_confidence(self, extraction_method: str, target_found: bool) -> float:
        """
        Get confidence score for an edge based on extraction method and target status.

        Args:
            extraction_method: Extraction method ID (e.g., "python_ast_import")
            target_found: True if target doc_id was found in registry, False otherwise

        Returns:
            Confidence score: 1.0 (high) or 0.0 (broken)

        Examples:
            >>> engine = ConfidenceEngine()
            >>> engine.get_confidence("python_ast_import", target_found=True)
            1.0

            >>> engine.get_confidence("python_ast_import", target_found=False)
            0.0

            >>> engine.get_confidence("json_schema_ref", target_found=True)
            1.0
        """
        # Validate extraction method exists
        extraction_methods = self.rules.get("extraction_methods", {})
        if extraction_method not in extraction_methods:
            raise ValueError(
                f"Unknown extraction method: {extraction_method}. "
                f"Valid methods: {list(extraction_methods.keys())}"
            )

        method_config = extraction_methods[extraction_method]
        confidence_tier = method_config["confidence_tier"]

        # If target not found, check if we should fallback to broken
        if not target_found:
            fallback_to_broken = method_config.get("fallback_to_broken", True)
            if fallback_to_broken:
                confidence_tier = "broken"

        # Get confidence value from tier
        tiers = self.rules.get("confidence_tiers", {})
        if confidence_tier not in tiers:
            raise ValueError(f"Unknown confidence tier: {confidence_tier}")

        return tiers[confidence_tier]["value"]

    def get_analyzer_for_method(self, extraction_method: str) -> str:
        """
        Get the analyzer ID that uses a given extraction method.

        Args:
            extraction_method: Extraction method ID

        Returns:
            Analyzer ID (e.g., "python_import_analyzer")

        Raises:
            ValueError: If extraction method is unknown
        """
        extraction_methods = self.rules.get("extraction_methods", {})
        if extraction_method not in extraction_methods:
            raise ValueError(f"Unknown extraction method: {extraction_method}")

        return extraction_methods[extraction_method]["analyzer"]

    def get_flags_for_broken_edge(self) -> List[str]:
        """
        Get the flags that should be applied to broken edges.

        Returns:
            List of flag names (e.g., ["target_missing"])
        """
        policy = self.rules.get("broken_edge_policy", {})
        return policy.get("flags", [])

    def should_include_broken_edges(self) -> bool:
        """
        Check if broken edges should be included in the index.

        Returns:
            True if broken edges should be included, False otherwise
        """
        policy = self.rules.get("broken_edge_policy", {})
        return policy.get("include_in_index", True)

    def get_valid_extraction_methods(self) -> List[str]:
        """
        Get list of all valid extraction method IDs.

        Returns:
            List of extraction method IDs
        """
        extraction_methods = self.rules.get("extraction_methods", {})
        return list(extraction_methods.keys())

    def validate_edge(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an edge against confidence rules.

        Args:
            edge: Edge dictionary with keys: extraction_method, confidence, flags, etc.

        Returns:
            Validation result with keys:
            - valid: bool
            - errors: list of error messages
            - warnings: list of warning messages
        """
        errors = []
        warnings = []

        validation_rules = self.rules.get("validation_rules", {})

        # Check confidence is 0.0 or 1.0
        if validation_rules.get("confidence_must_be_0_or_1", True):
            confidence = edge.get("confidence")
            if confidence not in [0.0, 1.0]:
                errors.append(f"Confidence must be 0.0 or 1.0, got {confidence}")

        # Check broken edges have target_missing flag
        if validation_rules.get("broken_edges_must_have_target_missing_flag", True):
            if edge.get("confidence") == 0.0:
                flags = edge.get("flags", [])
                if "target_missing" not in flags:
                    errors.append("Broken edge (confidence=0.0) must have 'target_missing' flag")

        # Check evidence exists
        if validation_rules.get("edge_must_have_evidence", True):
            if "evidence" not in edge:
                errors.append("Edge must have evidence field")
            else:
                evidence = edge["evidence"]

                if validation_rules.get("evidence_must_have_location", True):
                    if "location" not in evidence:
                        errors.append("Evidence must have location field")

                if validation_rules.get("evidence_must_have_snippet", True):
                    if "snippet" not in evidence:
                        errors.append("Evidence must have snippet field")

                if validation_rules.get("evidence_must_have_extraction_method", True):
                    if "extraction_method" not in evidence:
                        errors.append("Evidence must have extraction_method field")
                    else:
                        method = evidence["extraction_method"]
                        if validation_rules.get("extraction_method_must_be_valid", True):
                            if method not in self.get_valid_extraction_methods():
                                errors.append(
                                    f"Invalid extraction_method: {method}. "
                                    f"Valid methods: {self.get_valid_extraction_methods()}"
                                )

                        # Check analyzer_id matches extraction_method
                        if validation_rules.get("analyzer_id_must_match_extraction_method", True):
                            expected_analyzer = self.get_analyzer_for_method(method)
                            actual_analyzer = edge.get("analyzer_id")
                            if actual_analyzer != expected_analyzer:
                                errors.append(
                                    f"Analyzer ID mismatch: expected {expected_analyzer}, "
                                    f"got {actual_analyzer} for method {method}"
                                )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # Example usage
    print("\n=== Confidence Engine Examples ===\n")

    # Create engine (assumes confidence_rules.yaml exists)
    try:
        engine = ConfidenceEngine()

        # Example 1: Get confidence for successful edge
        print("Example 1: Successful edge (target found)")
        confidence = engine.get_confidence("python_ast_import", target_found=True)
        print(f"  Extraction method: python_ast_import")
        print(f"  Target found: True")
        print(f"  Confidence: {confidence}")
        print()

        # Example 2: Get confidence for broken edge
        print("Example 2: Broken edge (target not found)")
        confidence = engine.get_confidence("python_ast_import", target_found=False)
        print(f"  Extraction method: python_ast_import")
        print(f"  Target found: False")
        print(f"  Confidence: {confidence}")
        print()

        # Example 3: Get analyzer for method
        print("Example 3: Get analyzer for extraction method")
        analyzer = engine.get_analyzer_for_method("json_schema_ref")
        print(f"  Extraction method: json_schema_ref")
        print(f"  Analyzer: {analyzer}")
        print()

        # Example 4: Validate edge
        print("Example 4: Validate edge")
        edge = {
            "confidence": 1.0,
            "analyzer_id": "python_import_analyzer",
            "evidence": {
                "location": "file.py:15",
                "snippet": "import module",
                "extraction_method": "python_ast_import"
            },
            "flags": []
        }
        result = engine.validate_edge(edge)
        print(f"  Edge: {edge}")
        print(f"  Valid: {result['valid']}")
        print(f"  Errors: {result['errors']}")
        print()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run this from SUB_RELATIONSHIP_INDEX/ directory or ensure confidence_rules.yaml exists")
