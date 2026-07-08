"""Tests for tools/bulk_tools.py — bulk test case creation and execution."""

import json
from unittest.mock import MagicMock, patch

from tools.bulk_tools import BulkTools


class TestBulkCreateTestCases:
    """Tests for BulkTools.bulk_create_test_cases."""

    def setup_method(self):
        self.tools = BulkTools()

    @patch("tools.bulk_tools.generic_create")
    def test_success_two_items(self, mock_generic_create):
        """Two valid test case dicts should produce two successes."""
        mock_generic_create.return_value = json.dumps({"success": True, "testcase_id": "tc_1"})

        test_cases = [
            {"title": "TC One", "description": "First test case"},
            {"title": "TC Two", "description": "Second test case"},
        ]
        raw = self.tools.bulk_create_test_cases(test_cases, project_area="TestProject (qm)")
        result = json.loads(raw)

        assert result["success"] is True
        assert result["total_requested"] == 2
        assert result["created"] == 2
        assert result["failed"] == 0
        assert len(result["results"]["success"]) == 2
        assert result["results"]["success"][0]["test_case_id"] == "tc_1"
        assert mock_generic_create.call_count == 2

    @patch("tools.bulk_tools.generic_create")
    def test_empty_list_returns_error(self, mock_generic_create):
        """An empty list should return an error without calling generic_create."""
        raw = self.tools.bulk_create_test_cases([], project_area="TestProject (qm)")
        result = json.loads(raw)

        assert "error" in result
        assert "non-empty list" in result["error"]
        mock_generic_create.assert_not_called()

    @patch("tools.bulk_tools.generic_create")
    def test_not_a_list_returns_error(self, mock_generic_create):
        """A non-list input should return an error."""
        raw = self.tools.bulk_create_test_cases("not a list", project_area="TestProject (qm)")
        result = json.loads(raw)

        assert "error" in result
        assert "non-empty list" in result["error"]
        mock_generic_create.assert_not_called()

    @patch("tools.bulk_tools.generic_create")
    def test_item_missing_title_is_failed(self, mock_generic_create):
        """A dict without 'title' should appear in failed results."""
        mock_generic_create.return_value = json.dumps({"success": True, "testcase_id": "tc_ok"})

        test_cases = [
            {"description": "No title here"},
            {"title": "Valid TC", "description": "Has title"},
        ]
        raw = self.tools.bulk_create_test_cases(test_cases, project_area="TestProject (qm)")
        result = json.loads(raw)

        assert result["success"] is True
        assert result["created"] == 1
        assert result["failed"] == 1
        assert result["results"]["failed"][0]["error"] == "Missing title"
        mock_generic_create.assert_called_once()


class TestBulkExecuteTests:
    """Tests for BulkTools.bulk_execute_tests."""

    def setup_method(self):
        self.tools = BulkTools()

    @patch("tools.bulk_tools.time.sleep", return_value=None)
    @patch("tools.bulk_tools.create_xml_resource", return_value="<xml/>")
    @patch("tools.bulk_tools.build_resource_href", return_value="https://etm.example.com/href")
    @patch("tools.bulk_tools.build_resource_url", return_value="https://etm.example.com/endpoint")
    @patch("tools.bulk_tools.extract_resource_id")
    @patch("tools.bulk_tools.make_request")
    def test_success_two_requests(
        self,
        mock_make_request,
        mock_extract_id,
        mock_build_url,
        mock_build_href,
        mock_create_xml,
        mock_sleep,
    ):
        """Two valid execution requests should each create a TCER + result."""
        mock_response = MagicMock()
        mock_response.text = "<created/>"
        mock_make_request.return_value = mock_response

        # Each _create_single_execution_record calls extract_resource_id twice:
        # once for TCER, once for execution result.
        mock_extract_id.side_effect = ["tcer_1", "er_1", "tcer_2", "er_2"]

        requests_data = [
            {"test_case_id": "100", "result": "passed"},
            {"test_case_id": "200", "result": "failed"},
        ]
        raw = self.tools.bulk_execute_tests(requests_data, project_area="TestProject (qm)")
        result = json.loads(raw)

        assert result["success"] is True
        assert result["total_requested"] == 2
        assert result["executed"] == 2
        assert result["failed"] == 0
        assert result["results"]["success"][0]["execution_result_id"] == "er_1"
        assert result["results"]["success"][1]["execution_result_id"] == "er_2"
        # 2 POSTs per execution (TCER + result), 2 executions = 4 calls
        assert mock_make_request.call_count == 4

    def test_empty_list_returns_error(self):
        """An empty list should return an error."""
        raw = self.tools.bulk_execute_tests([], project_area="TestProject (qm)")
        result = json.loads(raw)

        assert "error" in result
        assert "non-empty list" in result["error"]

    @patch("tools.bulk_tools.time.sleep", return_value=None)
    @patch("tools.bulk_tools.create_xml_resource", return_value="<xml/>")
    @patch("tools.bulk_tools.build_resource_href", return_value="https://etm.example.com/href")
    @patch("tools.bulk_tools.build_resource_url", return_value="https://etm.example.com/endpoint")
    @patch("tools.bulk_tools.extract_resource_id", return_value="id_1")
    @patch("tools.bulk_tools.make_request")
    def test_missing_fields_in_failed_results(
        self,
        mock_make_request,
        mock_extract_id,
        mock_build_url,
        mock_build_href,
        mock_create_xml,
        mock_sleep,
    ):
        """Dicts missing test_case_id or result should appear in failed results."""
        mock_response = MagicMock()
        mock_response.text = "<ok/>"
        mock_make_request.return_value = mock_response

        requests_data = [
            {"result": "passed"},  # missing test_case_id
            {"test_case_id": "100"},  # missing result
            {"test_case_id": "200", "result": "passed"},  # valid
        ]
        raw = self.tools.bulk_execute_tests(requests_data, project_area="TestProject (qm)")
        result = json.loads(raw)

        assert result["success"] is True
        assert result["executed"] == 1
        assert result["failed"] == 2
        for failed in result["results"]["failed"]:
            assert "Missing test_case_id or result" in failed["error"]
