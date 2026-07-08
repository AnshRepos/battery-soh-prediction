"""Tests for tools/execution_tools.py — execution results, records, links, and attachments."""

import json
from unittest.mock import MagicMock, patch

import pytest
from tools.execution_tools import ExecutionTools


@pytest.fixture
def tools():
    """Return a fresh ExecutionTools instance."""
    return ExecutionTools()


# ── GetAttachment ─────────────────────────────────────────────────────────


class TestGetAttachment:
    """Tests for ExecutionTools.get_attachment()."""

    @patch("tools.execution_tools.generic_get")
    def test_delegates_to_generic_get(self, mock_get, tools):
        mock_get.return_value = json.dumps({"id": "att-1", "title": "log.txt"})

        result = tools.get_attachment("att-1")

        assert json.loads(result)["id"] == "att-1"
        mock_get.assert_called_once_with(
            "attachment",
            "att-1",
            None,
            configuration_context=None,
        )

    @patch("tools.execution_tools.generic_get")
    def test_forwards_project_area(self, mock_get, tools):
        mock_get.return_value = json.dumps({"id": "att-2"})

        tools.get_attachment("att-2", project_area="Proj (qm)")

        mock_get.assert_called_once_with(
            "attachment",
            "att-2",
            "Proj (qm)",
            configuration_context=None,
        )


# ── GetTestPlanTemplate ──────────────────────────────────────────────────


class TestGetTestPlanTemplate:
    """Tests for ExecutionTools.get_test_plan_template()."""

    @patch("tools.execution_tools.parse_resource_to_json")
    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_returns_parsed_json(self, mock_url, mock_req, mock_parse, tools):
        mock_url.return_value = "https://etm.example.com/template"
        mock_response = MagicMock()
        mock_response.text = "<template/>"
        mock_req.return_value = mock_response
        mock_parse.return_value = json.dumps({"title": "Default Template"})

        result = tools.get_test_plan_template("Default Template", project_area="P (qm)")

        assert json.loads(result)["title"] == "Default Template"
        mock_url.assert_called_once_with("P (qm)", "template")
        expected_endpoint = "https://etm.example.com/template/testplan/Default%20Template"
        mock_req.assert_called_once_with(expected_endpoint, configuration_context=None)

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_missing_project_returns_error(self, mock_url, mock_req, tools):
        """Empty project_area AND env-default yield an error JSON."""
        with patch("tools.execution_tools.ETM_PROJECT_AREA", ""):
            result = tools.get_test_plan_template("tpl", project_area="")

        data = json.loads(result)
        assert "error" in data
        mock_req.assert_not_called()


# ── ListExecutionResults ─────────────────────────────────────────────────


class TestListExecutionResults:
    """Tests for ExecutionTools.list_execution_results()."""

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_returns_raw_response_text(self, mock_url, mock_req, tools):
        mock_url.return_value = "https://etm.example.com/executionresult"
        mock_response = MagicMock()
        mock_response.text = "<feed><entry/></feed>"
        mock_req.return_value = mock_response

        result = json.loads(tools.list_execution_results(project_area="P (qm)", limit=10))

        assert result["count"] == 0
        assert result["page_size"] == 10
        assert result["entries"] == []

    def test_invalid_limit_returns_error(self, tools):
        result = tools.list_execution_results(limit=0)
        assert json.loads(result)["error"] == "limit must be between 1 and 200"

    def test_limit_above_max_returns_error(self, tools):
        result = tools.list_execution_results(limit=201)
        assert "error" in json.loads(result)

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_href")
    @patch("tools.execution_tools.build_resource_url")
    def test_filters_by_test_plan_and_state(self, mock_url, mock_href, mock_req, tools):
        mock_url.return_value = "https://etm.example.com/executionresult"
        mock_href.return_value = "https://etm.example.com/testplan/123"
        mock_response = MagicMock()
        mock_response.text = "<feed/>"
        mock_req.return_value = mock_response

        tools.list_execution_results(
            project_area="P (qm)",
            test_plan_id="123",
            state="passed",
        )

        _, call_kwargs = mock_req.call_args
        params = call_kwargs["params"]
        assert "fields" in params
        assert "testplan" in params["fields"]
        assert "state='passed'" in params["fields"]


# ── GetExecutionResult ───────────────────────────────────────────────────


class TestGetExecutionResult:
    """Tests for ExecutionTools.get_execution_result()."""

    @patch("tools.execution_tools.generic_get")
    def test_delegates_to_generic_get(self, mock_get, tools):
        mock_get.return_value = json.dumps({"id": "res-1", "state": "passed"})

        result = tools.get_execution_result("res-1")

        assert json.loads(result)["state"] == "passed"
        mock_get.assert_called_once_with(
            "executionresult",
            "res-1",
            None,
            configuration_context=None,
        )


# ── CreateExecutionRecord ────────────────────────────────────────────────


class TestCreateExecutionRecord:
    """Tests for ExecutionTools.create_execution_record()."""

    @patch("tools.execution_tools.time.sleep")
    @patch("tools.execution_tools.extract_resource_id")
    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.create_xml_resource")
    @patch("tools.execution_tools.build_resource_url")
    @patch("tools.execution_tools.build_resource_href")
    def test_creates_tcer_then_result(
        self,
        mock_href,
        mock_url,
        mock_xml,
        mock_req,
        mock_extract,
        mock_sleep,
        tools,
    ):
        """Verify the two-step create: TCER POST then execution result POST."""
        mock_href.return_value = "https://etm.example.com/href"
        mock_url.return_value = "https://etm.example.com/endpoint"
        mock_xml.return_value = "<executionworkitem/>"

        tcer_resp = MagicMock()
        result_resp = MagicMock()
        mock_req.side_effect = [tcer_resp, result_resp]
        # Use a numeric TCER id (as returned after real creation) so the
        # slug→webId resolution branch is not triggered.
        mock_extract.side_effect = ["608562", "420591"]

        result = tools.create_execution_record(
            test_case_id="3435948",
            result="passed",
            project_area="CC-DA ESM Sandbox",
        )

        data = json.loads(result)
        assert data["success"] is True
        assert data["execution_record_id"] == "608562"
        assert data["execution_result_id"] == "420591"
        assert mock_req.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch("tools.execution_tools.time.sleep")
    @patch("tools.execution_tools.extract_resource_id")
    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.create_xml_resource")
    @patch("tools.execution_tools.build_resource_url")
    @patch("tools.execution_tools.build_resource_href")
    def test_returns_error_when_tcer_extraction_fails(
        self,
        mock_href,
        mock_url,
        mock_xml,
        mock_req,
        mock_extract,
        mock_sleep,
        tools,
    ):
        mock_href.return_value = "https://etm.example.com/href"
        mock_url.return_value = "https://etm.example.com/endpoint"
        mock_xml.return_value = "<executionworkitem/>"
        mock_req.return_value = MagicMock()
        mock_extract.return_value = None

        result = tools.create_execution_record(
            test_case_id="tc-100",
            result="failed",
            project_area="P (qm)",
        )

        data = json.loads(result)
        assert "error" in data
        assert "TCER" in data["error"]

    def test_missing_project_returns_error(self, tools):
        with patch("tools.execution_tools.ETM_PROJECT_AREA", ""):
            result = tools.create_execution_record(
                test_case_id="tc-1",
                result="passed",
                project_area="",
            )

        assert "error" in json.loads(result)

    @patch("tools.execution_tools.time.sleep")
    @patch("tools.execution_tools.extract_resource_id")
    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.create_xml_resource")
    @patch("tools.execution_tools.build_resource_url")
    @patch("tools.execution_tools.build_resource_href")
    def test_invalid_executed_by_returns_error(
        self,
        mock_href,
        mock_url,
        mock_xml,
        mock_req,
        mock_extract,
        mock_sleep,
        tools,
    ):
        """executed_by must be an http/https URL."""
        mock_href.return_value = "https://etm.example.com/href"
        mock_url.return_value = "https://etm.example.com/endpoint"
        mock_xml.return_value = "<executionworkitem/>"
        mock_req.return_value = MagicMock()
        mock_extract.return_value = "tcer_1"

        result = tools.create_execution_record(
            test_case_id="tc-1",
            result="passed",
            project_area="P (qm)",
            executed_by="plain-user",
        )

        data = json.loads(result)
        assert data["error"] == "executed_by must be a contributor URI (http/https URL)"


# ── UpdateExecutionResult ────────────────────────────────────────────────


class TestUpdateExecutionResult:
    """Tests for ExecutionTools.update_execution_result()."""

    @patch("tools.execution_tools.generic_update")
    def test_maps_passed_state(self, mock_update, tools):
        """'passed' is mapped to the full IBM state URI."""
        mock_update.return_value = json.dumps({"success": True})

        tools.update_execution_result("er-1", state="passed")

        _, kwargs = mock_update.call_args
        assert kwargs["state"] == "com.ibm.rqm.execution.common.state.passed"

    @patch("tools.execution_tools.generic_update")
    def test_maps_comments_to_description(self, mock_update, tools):
        """comments parameter is forwarded as 'description'."""
        mock_update.return_value = json.dumps({"success": True})

        tools.update_execution_result("er-1", comments="Test comment")

        _, kwargs = mock_update.call_args
        assert kwargs["description"] == "Test comment"

    @patch("tools.execution_tools.generic_update")
    def test_forwards_all_optional_fields(self, mock_update, tools):
        mock_update.return_value = json.dumps({"success": True})

        tools.update_execution_result(
            "er-1",
            state="failed",
            owner="user1",
            weight=100,
            machine="server-01",
            locked=True,
        )

        _, kwargs = mock_update.call_args
        assert kwargs["state"] == "com.ibm.rqm.execution.common.state.failed"
        assert kwargs["owner"] == "user1"
        assert kwargs["weight"] == "100"
        assert kwargs["machine"] == "server-01"
        assert kwargs["locked"] == "true"


# ── GetRequirementCustomAttributes ───────────────────────────────────────


class TestGetRequirementCustomAttributes:
    """Tests for ExecutionTools.get_requirement_custom_attributes()."""

    _CUSTOM_ATTR_XML = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
        "<ns2:customAttributes>"
        "<ns2:customAttribute>"
        "<ns2:name>verifiesCodebeamerRequirement</ns2:name>"
        "<ns2:value>https://cb.example.com/req/1; https://cb.example.com/req/2</ns2:value>"
        "</ns2:customAttribute>"
        "<ns2:customAttribute>"
        "<ns2:name>otherAttr</ns2:name>"
        "<ns2:value>some value</ns2:value>"
        "</ns2:customAttribute>"
        "</ns2:customAttributes>"
        "</ns2:testcase>"
    )

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_filters_requirement_attributes(self, mock_url, mock_req, tools):
        mock_url.return_value = "https://etm.example.com/testcase/123"
        mock_response = MagicMock()
        mock_response.text = self._CUSTOM_ATTR_XML
        mock_req.return_value = mock_response

        result = tools.get_requirement_custom_attributes("123", project_area="P (qm)")

        data = json.loads(result)
        attrs = data["requirement_custom_attributes"]
        assert len(attrs) == 1
        assert attrs[0]["name"] == "verifiesCodebeamerRequirement"
        assert len(attrs[0]["values"]) == 2
        assert data["total_count"] == 2

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_empty_custom_attributes(self, mock_url, mock_req, tools):
        """No matching attributes yields an empty list."""
        xml = (
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
            "<ns2:customAttributes>"
            "<ns2:customAttribute>"
            "<ns2:name>unrelatedField</ns2:name>"
            "<ns2:value>val</ns2:value>"
            "</ns2:customAttribute>"
            "</ns2:customAttributes>"
            "</ns2:testcase>"
        )
        mock_url.return_value = "https://etm.example.com/testcase/456"
        mock_response = MagicMock()
        mock_response.text = xml
        mock_req.return_value = mock_response

        result = tools.get_requirement_custom_attributes("456", project_area="P (qm)")

        data = json.loads(result)
        assert data["requirement_custom_attributes"] == []
        assert data["total_count"] == 0

    def test_empty_test_case_id_returns_error(self, tools):
        result = tools.get_requirement_custom_attributes("", project_area="P (qm)")
        assert "error" in json.loads(result)


# ── GetRequirementLinks ──────────────────────────────────────────────────


class TestGetRequirementLinks:
    """Tests for ExecutionTools.get_requirement_links()."""

    _REQUIREMENT_LINKS_XML = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
        '<ns2:requirement href="https://doors.example.com/req/123"'
        ' summary="Req 123" rel="validates" isSuspected="false"/>'
        '<ns2:requirement href="https://doors.example.com/req/456"'
        ' summary="Req 456" rel="validates" isSuspected="true"/>'
        "</ns2:testcase>"
    )

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_parses_requirement_elements(self, mock_url, mock_req, tools):
        mock_url.return_value = "https://etm.example.com/testcase/tc-1"
        mock_response = MagicMock()
        mock_response.text = self._REQUIREMENT_LINKS_XML
        mock_req.return_value = mock_response

        result = tools.get_requirement_links("tc-1", project_area="P (qm)")

        data = json.loads(result)
        assert data["count"] == 2
        links = data["requirement_links"]
        assert links[0]["href"] == "https://doors.example.com/req/123"
        assert links[0]["rel"] == "validates"
        assert links[1]["isSuspected"] == "true"

    @patch("tools.execution_tools.make_request")
    @patch("tools.execution_tools.build_resource_url")
    def test_calmlinks_param_is_set(self, mock_url, mock_req, tools):
        """Verify calmlinks=true is passed to make_request."""
        mock_url.return_value = "https://etm.example.com/testcase/tc-1"
        mock_response = MagicMock()
        mock_response.text = '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"/>'
        mock_req.return_value = mock_response

        tools.get_requirement_links("tc-1", project_area="P (qm)")

        _, kwargs = mock_req.call_args
        assert kwargs["params"] == {"calmlinks": "true"}

    def test_empty_test_case_id_returns_error(self, tools):
        result = tools.get_requirement_links("  ", project_area="P (qm)")
        assert "error" in json.loads(result)
