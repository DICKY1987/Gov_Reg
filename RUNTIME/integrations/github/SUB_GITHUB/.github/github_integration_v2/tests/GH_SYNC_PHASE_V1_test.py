"""
Test GH_SYNC_PHASE_V1 pattern implementation.

This is a unit test suite for the GitHub sync functionality.
Integration tests require a real GitHub token and project.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add .github/github_integration_v2 to path
repo_root = Path(__file__).resolve().parents[3]
github_v2_path = repo_root / ".github" / "github_integration_v2"
sys.path.insert(0, str(github_v2_path))

from executors.phase_sync import (
    GitHubIntegrationConfig,
    GitHubIssueConfig,
    GitHubProjectConfig,
    PhaseIdentity,
    _graphql_request,
    _render_issue_body,
    _render_issue_title,
)


class TestPhaseIdentity(unittest.TestCase):
    """Test PhaseIdentity model."""

    def test_basic_creation(self):
        phase = PhaseIdentity(
            phase_id="PH-001",
            workstream_id="ws-core",
            title="Test Phase",
            status="planned",
        )
        self.assertEqual(phase.phase_id, "PH-001")
        self.assertEqual(phase.workstream_id, "ws-core")
        self.assertIsNone(phase.risk_level)


class TestIssueRendering(unittest.TestCase):
    """Test issue title and body rendering."""

    def setUp(self):
        self.phase = PhaseIdentity(
            phase_id="PH-001",
            workstream_id="ws-core",
            title="Test Phase",
            status="planned",
            risk_level="medium",
            target_date="2025-12-31",
        )

    def test_render_issue_title_default_template(self):
        config = GitHubIssueConfig(
            mode="one-per-phase",
            number=None,
            title_template="[{phase_id}] {title}",
            body_template_path=None,
            labels=[],
            assignees=[],
        )
        title = _render_issue_title(self.phase, config)
        self.assertEqual(title, "[PH-001] Test Phase")

    def test_render_issue_title_custom_template(self):
        config = GitHubIssueConfig(
            mode="one-per-phase",
            number=None,
            title_template="{workstream_id}/{phase_id}: {title}",
            body_template_path=None,
            labels=[],
            assignees=[],
        )
        title = _render_issue_title(self.phase, config)
        self.assertEqual(title, "ws-core/PH-001: Test Phase")

    def test_render_issue_body(self):
        body = _render_issue_body(self.phase, "phases/test.yaml")
        self.assertIn("PH-001", body)
        self.assertIn("Test Phase", body)
        self.assertIn("ws-core", body)
        self.assertIn("planned", body)
        self.assertIn("medium", body)
        self.assertIn("2025-12-31", body)
        self.assertIn("phases/test.yaml", body)


class TestGraphQLRequest(unittest.TestCase):
    """Test GraphQL request handling."""

    @patch("executors.phase_sync.requests.post")
    def test_graphql_request_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {"user": {"projectV2": {"id": "PVT_123"}}}
        }
        mock_post.return_value = mock_response

        result = _graphql_request(
            "test_token", "query { user { projectV2 { id } } }", {}
        )

        self.assertEqual(result, {"user": {"projectV2": {"id": "PVT_123"}}})
        mock_post.assert_called_once()

    @patch("executors.phase_sync.requests.post")
    def test_graphql_request_with_errors(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"errors": [{"message": "Field not found"}]}
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            _graphql_request("test_token", "query { invalid }", {})

        self.assertIn("GraphQL errors", str(ctx.exception))

    @patch("executors.phase_sync.requests.post")
    def test_graphql_request_http_error(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as ctx:
            _graphql_request("invalid_token", "query { }", {})

        self.assertIn("401", str(ctx.exception))


class TestIntegrationConfig(unittest.TestCase):
    """Test configuration models."""

    def test_full_config_creation(self):
        config = GitHubIntegrationConfig(
            enabled=True,
            repo_owner="test-owner",
            repo_name="test-repo",
            default_branch="main",
            issue=GitHubIssueConfig(
                mode="one-per-phase",
                number=42,
                title_template="[{phase_id}] {title}",
                body_template_path=None,
                labels=["phase-plan"],
                assignees=["test-user"],
            ),
            project=GitHubProjectConfig(
                url=None,
                owner="test-owner",
                project_number=1,
                item_id=None,
                field_mappings={
                    "phase_id_field": "Phase ID",
                    "status_field": "Status",
                },
            ),
            automation={"sync_direction": "yaml->github"},
        )

        self.assertTrue(config.enabled)
        self.assertEqual(config.repo_owner, "test-owner")
        self.assertEqual(config.issue.number, 42)
        self.assertEqual(config.project.project_number, 1)


if __name__ == "__main__":
    unittest.main()
