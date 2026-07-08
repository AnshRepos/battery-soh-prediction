"""Tests for tools/testsuite_tools.py — TestSuite CRUD wrappers."""

import json
from unittest.mock import patch

import pytest
from tools.testsuite_tools import TestSuiteTools


@pytest.fixture
def tools():
    """Return a fresh TestSuiteTools instance."""
    return TestSuiteTools()


# ── CreateTestSuite ───────────────────────────────────────────────────────


class TestCreateTestSuite:
    """Tests for TestSuiteTools.create_test_suite()."""

    @patch("tools.testsuite_tools.generic_create")
    def test_returns_json_from_generic_create(self, mock_create, tools):
        """Verify the returned value is the JSON string from generic_create."""
        mock_create.return_value = json.dumps({"success": True, "testsuite_id": "42"})

        result = tools.create_test_suite("Smoke Suite", "Smoke tests")

        assert json.loads(result)["testsuite_id"] == "42"
        mock_create.assert_called_once_with(
            "testsuite",
            "Smoke Suite",
            "Smoke tests",
            None,
            configuration_context=None,
        )

    @patch("tools.testsuite_tools.generic_create")
    def test_forwards_project_area(self, mock_create, tools):
        """Explicit project_area is forwarded to generic_create."""
        mock_create.return_value = json.dumps({"success": True})

        tools.create_test_suite("S", "D", project_area="Custom (qm)")

        mock_create.assert_called_once_with(
            "testsuite",
            "S",
            "D",
            "Custom (qm)",
            configuration_context=None,
        )

    @patch("tools.testsuite_tools.generic_create")
    def test_forwards_configuration_context(self, mock_create, tools):
        """configuration_context kwarg is forwarded."""
        mock_create.return_value = json.dumps({"success": True})

        tools.create_test_suite("S", "D", configuration_context="https://cfg/ctx")

        mock_create.assert_called_once_with(
            "testsuite",
            "S",
            "D",
            None,
            configuration_context="https://cfg/ctx",
        )


# ── UpdateTestSuite ───────────────────────────────────────────────────────


class TestUpdateTestSuite:
    """Tests for TestSuiteTools.update_test_suite()."""

    @patch("tools.testsuite_tools.generic_update")
    def test_update_title_only(self, mock_update, tools):
        """Only non-None fields appear as kwargs."""
        mock_update.return_value = json.dumps({"success": True})

        tools.update_test_suite("7423", title="New Title")

        mock_update.assert_called_once_with(
            "testsuite",
            "7423",
            None,
            configuration_context=None,
            title="New Title",
        )

    @patch("tools.testsuite_tools.generic_update")
    def test_update_title_and_description(self, mock_update, tools):
        """Both title and description forwarded when provided."""
        mock_update.return_value = json.dumps({"success": True})

        tools.update_test_suite("100", title="T", description="D")

        mock_update.assert_called_once_with(
            "testsuite",
            "100",
            None,
            configuration_context=None,
            title="T",
            description="D",
        )

    @patch("tools.testsuite_tools.generic_update")
    def test_no_updates_skips_kwargs(self, mock_update, tools):
        """When neither title nor description is given, no extra kwargs are passed."""
        mock_update.return_value = json.dumps({"success": True})

        tools.update_test_suite("7423", project_area="P (qm)")

        mock_update.assert_called_once_with(
            "testsuite",
            "7423",
            "P (qm)",
            configuration_context=None,
        )


# ── DeleteTestSuite ───────────────────────────────────────────────────────


class TestDeleteTestSuite:
    """Tests for TestSuiteTools.delete_test_suite()."""

    @patch("tools.testsuite_tools.generic_delete")
    def test_delete_default_project(self, mock_delete, tools):
        """Default project_area (None) is forwarded."""
        mock_delete.return_value = json.dumps({"success": True})

        result = tools.delete_test_suite("7423")

        assert json.loads(result)["success"] is True
        mock_delete.assert_called_once_with(
            "testsuite",
            "7423",
            None,
            configuration_context=None,
        )

    @patch("tools.testsuite_tools.generic_delete")
    def test_delete_with_project_area(self, mock_delete, tools):
        """Explicit project_area is forwarded."""
        mock_delete.return_value = json.dumps({"success": True})

        tools.delete_test_suite("99", project_area="Other (qm)")

        mock_delete.assert_called_once_with(
            "testsuite",
            "99",
            "Other (qm)",
            configuration_context=None,
        )

    @patch("tools.testsuite_tools.generic_delete")
    def test_delete_with_configuration_context(self, mock_delete, tools):
        """configuration_context kwarg is forwarded."""
        mock_delete.return_value = json.dumps({"success": True})

        tools.delete_test_suite("50", configuration_context="https://cfg/ctx")

        mock_delete.assert_called_once_with(
            "testsuite",
            "50",
            None,
            configuration_context="https://cfg/ctx",
        )
