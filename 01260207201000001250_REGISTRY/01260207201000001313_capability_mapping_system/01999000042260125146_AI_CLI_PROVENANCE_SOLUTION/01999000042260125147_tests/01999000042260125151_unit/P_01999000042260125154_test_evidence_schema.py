# DOC_ID: DOC-TEST-0629
"""
Unit tests for Evidence Schema Validation
Created: 2026-01-04

Tests the EVIDENCE_SCHEMA_EXTENDED.yaml structure and validation logic.
"""

import pytest
from pathlib import Path
import yaml


class TestEvidenceSchema:
    """Test evidence schema structure and validation."""

    @pytest.fixture
    def schema_path(self):
        """Provide path to evidence schema file."""
        return Path(__file__).parent.parent.parent / "EVIDENCE_SCHEMA_EXTENDED.yaml"

    @pytest.fixture
    def schema_data(self, schema_path):
        """Load evidence schema YAML data."""
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def test_schema_file_exists(self, schema_path):
        """Test that evidence schema file exists."""
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_schema_is_valid_yaml(self, schema_data):
        """Test that schema is valid YAML."""
        assert schema_data is not None
        assert isinstance(schema_data, dict)

    def test_schema_has_required_top_level_keys(self, schema_data):
        """Test that schema has all required top-level keys."""
        required_keys = [
            "schema_version",
            "description",
            "evidence_paths",
            "collectors",
            "validation",
            "privacy",
            "safety"
        ]

        for key in required_keys:
            assert key in schema_data, f"Missing required key: {key}"

    def test_schema_version_format(self, schema_data):
        """Test that schema version is properly formatted."""
        version = schema_data.get("schema_version")
        assert version is not None
        assert isinstance(version, str)
        assert version == "2.0", f"Expected version 2.0, got: {version}"

    def test_evidence_paths_structure(self, schema_data):
        """Test that evidence paths have correct structure."""
        evidence_paths = schema_data.get("evidence_paths", {})

        assert "evidence" in evidence_paths, "Missing 'evidence' section"
        assert "provenance" in evidence_paths, "Missing 'provenance' section"

    def test_deterministic_evidence_paths_exist(self, schema_data):
        """Test that deterministic evidence paths are defined."""
        evidence = schema_data["evidence_paths"]["evidence"]

        required_categories = ["edge", "graph", "entrypoint", "runtime"]
        for category in required_categories:
            assert category in evidence, f"Missing evidence category: {category}"

    def test_ai_provenance_paths_exist(self, schema_data):
        """Test that AI provenance paths are defined."""
        provenance = schema_data["evidence_paths"]["provenance"]

        assert "ai_cli_logs" in provenance, "Missing 'ai_cli_logs' section"
        assert "git" in provenance, "Missing 'git' section"

        # Check AI CLI logs structure
        ai_cli = provenance["ai_cli_logs"]
        assert "timeline" in ai_cli, "Missing 'timeline' in ai_cli_logs"

        timeline = ai_cli["timeline"]
        required_fields = ["exists", "session_count", "tool_use_count", "intent_signals"]
        for field in required_fields:
            assert field in timeline, f"Missing timeline field: {field}"

    def test_collectors_are_defined(self, schema_data):
        """Test that collectors are properly defined."""
        collectors = schema_data.get("collectors", [])

        assert len(collectors) > 0, "No collectors defined"

        # Check for AI CLI provenance collector
        collector_ids = [c.get("collector_id") for c in collectors]
        assert "ai_cli_provenance_collector" in collector_ids, \
            "Missing ai_cli_provenance_collector"

    def test_privacy_settings(self, schema_data):
        """Test that privacy settings are correct."""
        privacy = schema_data.get("privacy", {})

        assert privacy.get("prompt_storage") == "SHA256_HASH_ONLY", \
            "Prompt storage should be SHA256_HASH_ONLY"
        assert privacy.get("path_filtering") == "REPO_SCOPED_ONLY", \
            "Path filtering should be REPO_SCOPED_ONLY"
        assert "repo_root" in privacy, "Missing repo_root setting"

    def test_safety_settings(self, schema_data):
        """Test that safety settings are configured."""
        safety = schema_data.get("safety", {})

        assert safety.get("graceful_degradation") is True, \
            "Graceful degradation should be enabled"
        assert safety.get("default_behavior") == "CONSERVATIVE", \
            "Default behavior should be CONSERVATIVE"

    def test_intent_signals_defined(self, schema_data):
        """Test that intent signals are properly defined."""
        intent_signals = schema_data["evidence_paths"]["provenance"]["ai_cli_logs"]["timeline"]["intent_signals"]

        required_intents = ["migration_intent", "deprecation_intent", "removal_intent"]
        for intent in required_intents:
            assert intent in intent_signals, f"Missing intent signal: {intent}"

            # Check structure
            intent_def = intent_signals[intent]
            assert "type" in intent_def, f"Missing type for {intent}"
            assert intent_def["type"] == "boolean", f"{intent} should be boolean"

    def test_tool_use_count_structure(self, schema_data):
        """Test that tool use count has correct structure."""
        tool_use = schema_data["evidence_paths"]["provenance"]["ai_cli_logs"]["timeline"]["tool_use_count"]

        required_tools = ["view", "edit", "create"]
        for tool in required_tools:
            assert tool in tool_use, f"Missing tool use type: {tool}"
            assert tool_use[tool]["type"] == "integer", f"{tool} should be integer type"
