"""Unit tests for tools.testplan_tools.TestPlanTools.

All service-layer calls are mocked so no network I/O occurs.
Every tool method returns a JSON string; we parse with json.loads()
and assert on the resulting dict.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from tools.testplan_tools import TestPlanTools


@pytest.fixture
def tools() -> TestPlanTools:
    """Return a fresh TestPlanTools instance for each test."""
    return TestPlanTools()


# ── Helpers ────────────────────────────────────────────────────────────────


def _make_entry(testplan_id: str, state: str, updated: str) -> dict:
    """Build a minimal execution-result entry dict."""
    return {
        "testplan": f"urn:com.ibm.rqm:testplan:{testplan_id}",
        "state": state,
        "updated": updated,
    }


# ── create_test_plan ──────────────────────────────────────────────────────


class TestCreateTestPlan:
    """Tests for TestPlanTools.create_test_plan."""

    @patch("tools.testplan_tools.extract_resource_id", return_value="slug__123")
    @patch("tools.testplan_tools.make_request")
    @patch("tools.testplan_tools.create_xml_resource", return_value="<xml/>")
    @patch("tools.testplan_tools.build_resource_url", return_value="/endpoint")
    @patch("tools.testplan_tools.build_category_href", return_value="https://example.com/cat")
    def test_success(
        self,
        mock_cat_href: MagicMock,
        mock_build_url: MagicMock,
        mock_create_xml: MagicMock,
        mock_request: MagicMock,
        mock_extract: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """Successful creation returns success=True and the testplan_id."""
        mock_response = MagicMock()
        mock_response.headers = {"Location": "https://etm.example.com/testplan/slug__123"}
        mock_request.return_value = mock_response

        result = json.loads(
            tools.create_test_plan(
                title="My Plan",
                description="desc",
                release="R1",
                test_level="Unit Test",
                project_area="Proj",
            )
        )

        assert result["success"] is True
        assert result["testplan_id"] == "slug__123"
        assert "location" in result
        mock_build_url.assert_called_once_with("Proj", "testplan")
        mock_request.assert_called_once()

    def test_empty_project_area_returns_error(self, tools: TestPlanTools) -> None:
        """An empty project_area (when env default is also blank) produces an error."""
        with patch("tools.testplan_tools.ETM_PROJECT_AREA", ""):
            result = json.loads(
                tools.create_test_plan(
                    title="P",
                    description="d",
                    release="R",
                    test_level="T",
                    project_area="",
                )
            )

        assert "error" in result
        assert "required" in result["error"].lower()

    @patch("tools.testplan_tools.build_category_href", return_value="href")
    @patch("tools.testplan_tools.build_resource_url", return_value="/ep")
    @patch("tools.testplan_tools.create_xml_resource", return_value="<xml/>")
    @patch("tools.testplan_tools.make_request", side_effect=RuntimeError("boom"))
    @patch(
        "tools.testplan_tools.handle_error",
        return_value='{"error": "boom", "function": "create_test_plan"}',
    )
    def test_exception_handled(
        self,
        mock_handle: MagicMock,
        mock_request: MagicMock,
        mock_xml: MagicMock,
        mock_url: MagicMock,
        mock_cat: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """Exceptions from make_request are forwarded to handle_error."""
        result = json.loads(tools.create_test_plan("T", "D", "R", "L", project_area="P"))

        assert result["error"] == "boom"
        mock_handle.assert_called_once()


# ── update_test_plan ──────────────────────────────────────────────────────


class TestUpdateTestPlan:
    """Tests for TestPlanTools.update_test_plan."""

    @patch("tools.testplan_tools.generic_update", return_value='{"success": true}')
    def test_only_non_none_fields_forwarded(self, mock_update: MagicMock, tools: TestPlanTools) -> None:
        """Only non-None update values are included in the kwargs."""
        tools.update_test_plan(test_plan_id="100", description="new desc")

        _, kwargs = mock_update.call_args
        assert "description" in kwargs
        assert kwargs["description"] == "new desc"
        # title was not supplied → should not appear
        assert "title" not in kwargs

    @patch("tools.testplan_tools.generic_update", return_value='{"success": true}')
    def test_all_fields(self, mock_update: MagicMock, tools: TestPlanTools) -> None:
        """When every optional field is provided, all are forwarded."""
        tools.update_test_plan(
            test_plan_id="200",
            project_area="Proj",
            title="New Title",
            description="New Desc",
            start_date="2026-01-01",
            end_date="2026-12-31",
            owner="alice",
        )

        _, kwargs = mock_update.call_args
        assert kwargs["title"] == "New Title"
        assert kwargs["description"] == "New Desc"
        assert kwargs["startdate"] == "2026-01-01"
        assert kwargs["enddate"] == "2026-12-31"
        assert kwargs["owner"] == "alice"

    @patch("tools.testplan_tools.generic_update", return_value='{"success": true}')
    def test_configuration_context_forwarded(self, mock_update: MagicMock, tools: TestPlanTools) -> None:
        """configuration_context is passed through to generic_update."""
        tools.update_test_plan(test_plan_id="300", configuration_context="https://ctx")

        _, kwargs = mock_update.call_args
        assert kwargs["configuration_context"] == "https://ctx"


# ── delete_test_plan ──────────────────────────────────────────────────────


class TestDeleteTestPlan:
    """Tests for TestPlanTools.delete_test_plan."""

    @patch("tools.testplan_tools.generic_delete", return_value='{"success": true}')
    def test_delegates_to_generic_delete(self, mock_delete: MagicMock, tools: TestPlanTools) -> None:
        """Deletion delegates to generic_delete with the correct arguments."""
        result = json.loads(tools.delete_test_plan("42", project_area="Proj"))

        assert result["success"] is True
        mock_delete.assert_called_once_with("testplan", "42", "Proj", configuration_context=None)

    @patch("tools.testplan_tools.generic_delete", return_value='{"success": true}')
    def test_configuration_context_forwarded(self, mock_delete: MagicMock, tools: TestPlanTools) -> None:
        """configuration_context is passed through to generic_delete."""
        tools.delete_test_plan("99", configuration_context="https://ctx")

        _, kwargs = mock_delete.call_args
        assert kwargs["configuration_context"] == "https://ctx"


# ── get_test_plan_statistics ──────────────────────────────────────────────


class TestGetTestPlanStatistics:
    """Tests for TestPlanTools.get_test_plan_statistics."""

    # ── validation ────────────────────────────────────────────────────────

    def test_missing_test_plan_id_returns_error(self, tools: TestPlanTools) -> None:
        """An empty test_plan_id produces an error."""
        result = json.loads(tools.get_test_plan_statistics(""))

        assert "error" in result
        assert "test_plan_id" in result["error"].lower()

    def test_invalid_mode_returns_error(self, tools: TestPlanTools) -> None:
        """An unrecognised mode produces an error."""
        result = json.loads(tools.get_test_plan_statistics("1", mode="bad"))

        assert "error" in result
        assert "mode" in result["error"].lower()

    # ── statistics mode ───────────────────────────────────────────────────

    @patch("tools.testplan_tools.classify_execution_state")
    @patch("tools.testplan_tools.collect_paginated_entries")
    @patch("tools.testplan_tools.build_resource_url", return_value="/ep")
    def test_statistics_mode(
        self,
        mock_url: MagicMock,
        mock_collect: MagicMock,
        mock_classify: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """statistics mode computes pass rate from classified states."""
        mock_collect.return_value = [
            _make_entry("100", "state.passed", "2026-01-15T10:00:00.000Z"),
            _make_entry("100", "state.passed", "2026-01-15T11:00:00.000Z"),
            _make_entry("100", "state.failed", "2026-01-15T12:00:00.000Z"),
            _make_entry("999", "state.passed", "2026-01-15T10:00:00.000Z"),  # different plan
        ]
        mock_classify.side_effect = lambda s: "passed" if "passed" in s else "failed"

        result = json.loads(tools.get_test_plan_statistics("100", project_area="Proj", mode="statistics"))

        assert result["success"] is True
        assert result["mode"] == "statistics"
        stats = result["statistics"]
        assert stats["total"] == 3
        assert stats["passed"] == 2
        assert stats["failed"] == 1
        expected_rate = round((2 / 3) * 100, 2)
        assert stats["pass_rate"] == expected_rate

    @patch("tools.testplan_tools.classify_execution_state")
    @patch("tools.testplan_tools.collect_paginated_entries", return_value=[])
    @patch("tools.testplan_tools.build_resource_url", return_value="/ep")
    def test_statistics_no_entries(
        self,
        mock_url: MagicMock,
        mock_collect: MagicMock,
        mock_classify: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """statistics mode with no matching entries returns pass_rate 0."""
        result = json.loads(tools.get_test_plan_statistics("100", project_area="Proj", mode="statistics"))

        assert result["statistics"]["total"] == 0
        assert result["statistics"]["pass_rate"] == 0.0

    # ── timeline mode ─────────────────────────────────────────────────────

    @patch("tools.testplan_tools.classify_execution_state", return_value="passed")
    @patch("tools.testplan_tools.collect_paginated_entries")
    @patch("tools.testplan_tools.build_resource_url", return_value="/ep")
    def test_timeline_mode(
        self,
        mock_url: MagicMock,
        mock_collect: MagicMock,
        mock_classify: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """timeline mode groups entries by date and reports daily stats."""
        today = datetime.now().strftime("%Y-%m-%d")
        mock_collect.return_value = [
            _make_entry("200", "state.passed", f"{today}T10:00:00.000Z"),
            _make_entry("200", "state.passed", f"{today}T11:00:00.000Z"),
        ]

        result = json.loads(tools.get_test_plan_statistics("200", project_area="Proj", mode="timeline", days_back=5))

        assert result["success"] is True
        assert result["mode"] == "timeline"
        assert "timeline" in result
        assert result["summary"]["total_executions"] == 2

    # ── raw mode ──────────────────────────────────────────────────────────

    @patch("tools.testplan_tools.collect_paginated_entries")
    @patch("tools.testplan_tools.build_resource_url", return_value="/ep")
    def test_raw_mode_returns_entries(
        self,
        mock_url: MagicMock,
        mock_collect: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """raw mode returns matched entries without transformation."""
        entries = [
            _make_entry("300", "state.passed", "2026-01-15T10:00:00.000Z"),
            _make_entry("999", "state.passed", "2026-01-15T10:00:00.000Z"),
        ]
        mock_collect.return_value = entries

        result = json.loads(tools.get_test_plan_statistics("300", project_area="Proj", mode="raw"))

        assert result["count"] == 1
        assert len(result["executionresults"]) == 1
        assert "300" in result["executionresults"][0]["testplan"]

    # ── exception handling ────────────────────────────────────────────────

    @patch("tools.testplan_tools.collect_paginated_entries", side_effect=RuntimeError("fail"))
    @patch("tools.testplan_tools.build_resource_url", return_value="/ep")
    @patch(
        "tools.testplan_tools.handle_error",
        return_value='{"error": "fail", "function": "get_test_plan_statistics"}',
    )
    def test_exception_handled(
        self,
        mock_handle: MagicMock,
        mock_url: MagicMock,
        mock_collect: MagicMock,
        tools: TestPlanTools,
    ) -> None:
        """Exceptions are forwarded to handle_error."""
        result = json.loads(tools.get_test_plan_statistics("1", project_area="Proj"))

        assert result["error"] == "fail"
        mock_handle.assert_called_once()
