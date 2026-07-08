"""Tests for tools/linking_tools.py — suite/plan linking, defect linking, and use-case lookup."""

import json
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

import pytest
from tools.linking_tools import LinkingTools

# ── Constants ─────────────────────────────────────────────────────────────

_PROJECT = "TestProject (qm)"

_PATCH_MAKE_REQUEST = "tools.linking_tools.make_request"
_PATCH_BUILD_URL = "tools.linking_tools.build_resource_url"
_PATCH_BUILD_HREF = "tools.linking_tools.build_resource_href"
_PATCH_COLLECT = "tools.linking_tools.collect_paginated_entries"
_PATCH_FETCH_ALL = "tools.linking_tools.fetch_all_pages"

_SUITE_XML = (
    '<ns2:testsuite xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
    "<ns2:title>Test Suite 1</ns2:title>"
    "<ns2:suiteelements/>"
    "</ns2:testsuite>"
)

_PLAN_XML = (
    '<ns2:testplan xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:title>Test Plan 1</dc:title>"
    "</ns2:testplan>"
)

_EXEC_RESULT_XML = (
    '<ns2:executionresult xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
    '<ns2:relatedworkitem href="https://jira.example.com/PROJ-123"/>'
    '<ns2:relatedworkitem href="https://jira.example.com/PROJ-456"/>'
    "</ns2:executionresult>"
)

_FEED_XML = (
    '<feed xmlns="http://www.w3.org/2005/Atom"'
    ' xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<entry><content><ns2:testcase>"
    "<dc:title>Login Use Case Test</dc:title>"
    '<ns2:category term="UseCase" value="Login"/>'
    "</ns2:testcase></content></entry>"
    "<entry><content><ns2:testcase>"
    "<dc:title>Unrelated Test</dc:title>"
    "</ns2:testcase></content></entry>"
    "</feed>"
)


# ── Helpers ───────────────────────────────────────────────────────────────


def _mock_response(text: str, etag: str = '"etag-1"') -> MagicMock:
    """Return a MagicMock with .text and .headers pre-set."""
    resp = MagicMock()
    resp.text = text
    resp.headers = {"ETag": etag}
    resp.status_code = 200
    return resp


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def tools() -> LinkingTools:
    """Return a fresh LinkingTools instance."""
    return LinkingTools()


# ── AddTestCasesToSuite ───────────────────────────────────────────────────


class TestAddTestCasesToSuite:
    """Tests for LinkingTools.add_test_cases_to_suite."""

    @patch(_PATCH_BUILD_HREF, return_value="https://etm/tc/1")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/suite/S1")
    @patch(_PATCH_MAKE_REQUEST)
    def test_success_adds_cases(self, mock_req, mock_url, mock_href):
        """Successful add returns correct count and sets success=True."""
        get_resp = _mock_response(_SUITE_XML)
        put_resp = MagicMock(status_code=200)
        mock_req.side_effect = [get_resp, put_resp]

        result = json.loads(LinkingTools().add_test_cases_to_suite("S1", ["tc1", "tc2"], project_area=_PROJECT))

        assert result["success"] is True
        assert result["test_cases_added"] == 2
        assert mock_req.call_count == 2

    @patch(_PATCH_BUILD_URL)
    @patch(_PATCH_MAKE_REQUEST)
    def test_empty_suite_id_returns_error(self, mock_req, mock_url):
        """Empty test_suite_id returns a validation error."""
        result = json.loads(LinkingTools().add_test_cases_to_suite("", ["tc1"]))

        assert "error" in result
        mock_req.assert_not_called()

    @patch(_PATCH_BUILD_URL)
    @patch(_PATCH_MAKE_REQUEST)
    def test_empty_case_ids_returns_error(self, mock_req, mock_url):
        """Empty test_case_ids list returns a validation error."""
        result = json.loads(LinkingTools().add_test_cases_to_suite("S1", []))

        assert "error" in result
        mock_req.assert_not_called()


# ── LinkTestcaseToTestplan ────────────────────────────────────────────────


class TestLinkTestcaseToTestplan:
    """Tests for LinkingTools.link_testcase_to_testplan."""

    @patch(_PATCH_BUILD_HREF, return_value="https://etm/tc/100")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/plan/P1")
    @patch(_PATCH_MAKE_REQUEST)
    def test_success_links_case(self, mock_req, mock_url, mock_href):
        """Happy path: links test case and returns success message."""
        get_resp = _mock_response(_PLAN_XML)
        put_resp = MagicMock(status_code=200)
        mock_req.side_effect = [get_resp, put_resp]

        result = json.loads(LinkingTools().link_testcase_to_testplan("P1", "100", project_area=_PROJECT))

        assert result["success"] is True
        assert "100" in result["message"]
        assert "P1" in result["message"]

    @patch(_PATCH_BUILD_HREF, return_value="https://etm/tc/100")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/plan/P1")
    @patch(_PATCH_MAKE_REQUEST)
    def test_etag_passed_on_put(self, mock_req, mock_url, mock_href):
        """ETag from GET is forwarded as If-Match on the PUT."""
        get_resp = _mock_response(_PLAN_XML, etag='"plan-etag"')
        put_resp = MagicMock(status_code=200)
        mock_req.side_effect = [get_resp, put_resp]

        LinkingTools().link_testcase_to_testplan("P1", "100", project_area=_PROJECT)

        _, put_kwargs = mock_req.call_args_list[1]
        assert put_kwargs["extra_headers"]["If-Match"] == '"plan-etag"'

    @patch(_PATCH_BUILD_HREF)
    @patch(_PATCH_BUILD_URL)
    @patch(_PATCH_MAKE_REQUEST)
    def test_no_project_returns_error(self, mock_req, mock_url, mock_href):
        """Missing project_area (env cleared) returns error."""
        with patch("tools.linking_tools.ETM_PROJECT_AREA", ""):
            result = json.loads(LinkingTools().link_testcase_to_testplan("P1", "100", project_area=""))

        assert "error" in result


# ── LinkTestSuiteToPlan ───────────────────────────────────────────────────


class TestLinkTestSuiteToPlan:
    """Tests for LinkingTools.link_test_suite_to_plan."""

    @patch(_PATCH_BUILD_HREF, return_value="https://etm/suite/S5")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/plan/P2")
    @patch(_PATCH_MAKE_REQUEST)
    def test_success_links_suite(self, mock_req, mock_url, mock_href):
        """Happy path returns correct IDs in response."""
        get_resp = _mock_response(_PLAN_XML)
        put_resp = MagicMock(status_code=200)
        mock_req.side_effect = [get_resp, put_resp]

        result = json.loads(LinkingTools().link_test_suite_to_plan("S5", "P2", project_area=_PROJECT))

        assert result["success"] is True
        assert result["test_suite_id"] == "S5"
        assert result["test_plan_id"] == "P2"

    @patch(_PATCH_MAKE_REQUEST)
    def test_empty_ids_returns_error(self, mock_req):
        """Both IDs empty returns validation error without any HTTP call."""
        result = json.loads(LinkingTools().link_test_suite_to_plan("", ""))

        assert "error" in result
        mock_req.assert_not_called()

    @patch(_PATCH_BUILD_HREF, return_value="https://etm/suite/S5")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/plan/P2")
    @patch(_PATCH_MAKE_REQUEST)
    def test_put_sends_xml_content_type(self, mock_req, mock_url, mock_href):
        """PUT request uses application/rdf+xml content type."""
        mock_req.side_effect = [_mock_response(_PLAN_XML), MagicMock()]

        LinkingTools().link_test_suite_to_plan("S5", "P2", project_area=_PROJECT)

        _, put_kwargs = mock_req.call_args_list[1]
        assert put_kwargs["content_type"] == "application/rdf+xml"


# ── GetTestCasesByUseCase ─────────────────────────────────────────────────


class TestGetTestCasesByUseCase:
    """Tests for LinkingTools.get_test_cases_by_use_case."""

    @patch(_PATCH_BUILD_URL, return_value="https://etm/tc")
    @patch(_PATCH_FETCH_ALL)
    def test_matches_by_category(self, mock_fetch, mock_url):
        """Test case with matching category term is returned."""
        mock_fetch.return_value = ET.fromstring(_FEED_XML)

        result = json.loads(LinkingTools().get_test_cases_by_use_case("Login", project_area=_PROJECT))

        assert result["success"] is True
        assert result["count"] >= 1
        titles = [tc["title"] for tc in result["test_cases"]]
        assert "Login Use Case Test" in titles

    @patch(_PATCH_BUILD_URL, return_value="https://etm/tc")
    @patch(_PATCH_FETCH_ALL)
    def test_matches_by_title(self, mock_fetch, mock_url):
        """Test case whose title contains the use-case name is returned."""
        mock_fetch.return_value = ET.fromstring(_FEED_XML)

        result = json.loads(LinkingTools().get_test_cases_by_use_case("Login Use Case", project_area=_PROJECT))

        matching = [tc for tc in result["test_cases"] if tc["title"] == "Login Use Case Test"]
        assert len(matching) == 1

    @patch(_PATCH_FETCH_ALL)
    def test_empty_name_returns_error(self, mock_fetch):
        """Empty use_case_name returns validation error."""
        result = json.loads(LinkingTools().get_test_cases_by_use_case(""))

        assert "error" in result
        mock_fetch.assert_not_called()

    @patch(_PATCH_BUILD_URL, return_value="https://etm/tc")
    @patch(_PATCH_FETCH_ALL)
    def test_no_match_returns_zero(self, mock_fetch, mock_url):
        """Non-matching name returns empty list with count=0."""
        mock_fetch.return_value = ET.fromstring(_FEED_XML)

        result = json.loads(LinkingTools().get_test_cases_by_use_case("NonExistent", project_area=_PROJECT))

        assert result["count"] == 0
        assert result["test_cases"] == []


# ── GetFailedExecutionsWithoutDefects ─────────────────────────────────────


class TestGetFailedExecutionsWithoutDefects:
    """Tests for LinkingTools.get_failed_executions_without_defects."""

    _ENTRIES = [
        {
            "state": "com.ibm.rqm.execution.common.state.failed",
            "identifier": "exec1",
            "testcase": "tc1",
            "updated": "2026-01-15T10:00:00Z",
        },
        {
            "state": "com.ibm.rqm.execution.common.state.passed",
            "identifier": "exec2",
        },
        {
            "state": "com.ibm.rqm.execution.common.state.failed",
            "identifier": "exec3",
            "relatedworkitem": "http://jira/123",
        },
    ]

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_COLLECT, return_value=_ENTRIES)
    def test_filters_correctly(self, mock_collect, mock_url):
        """Only failed entries without defects are returned."""
        result = json.loads(LinkingTools().get_failed_executions_without_defects(project_area=_PROJECT))

        assert result["success"] is True
        assert result["count"] == 1
        assert result["failed_without_defects"][0]["execution_id"] == "exec1"

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_COLLECT, return_value=[])
    def test_empty_entries(self, mock_collect, mock_url):
        """No entries at all returns empty list."""
        result = json.loads(LinkingTools().get_failed_executions_without_defects(project_area=_PROJECT))

        assert result["success"] is True
        assert result["count"] == 0

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_COLLECT, return_value=_ENTRIES)
    def test_date_filter(self, mock_collect, mock_url):
        """Entries outside date range are excluded."""
        result = json.loads(
            LinkingTools().get_failed_executions_without_defects(
                project_area=_PROJECT,
                start_date="2026-01-16",
                end_date="2026-01-31",
            )
        )

        assert result["count"] == 0


# ── GetExecutionDefects ───────────────────────────────────────────────────


class TestGetExecutionDefects:
    """Tests for LinkingTools.get_execution_defects."""

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er/42")
    @patch(_PATCH_MAKE_REQUEST)
    def test_returns_defect_list(self, mock_req, mock_url):
        """Parses relatedworkitem hrefs from XML."""
        mock_req.return_value = _mock_response(_EXEC_RESULT_XML)

        result = json.loads(LinkingTools().get_execution_defects("42", project_area=_PROJECT))

        assert result["success"] is True
        assert result["defect_count"] == 2
        assert "https://jira.example.com/PROJ-123" in result["defects"]
        assert "https://jira.example.com/PROJ-456" in result["defects"]

    @patch(_PATCH_MAKE_REQUEST)
    def test_empty_id_returns_error(self, mock_req):
        """Empty execution_result_id returns validation error."""
        result = json.loads(LinkingTools().get_execution_defects(""))

        assert "error" in result
        mock_req.assert_not_called()

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er/99")
    @patch(_PATCH_MAKE_REQUEST)
    def test_no_defects_returns_zero(self, mock_req, mock_url):
        """Execution result with no relatedworkitem returns empty list."""
        xml = '<ns2:executionresult xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"/>'
        mock_req.return_value = _mock_response(xml)

        result = json.loads(LinkingTools().get_execution_defects("99", project_area=_PROJECT))

        assert result["defect_count"] == 0
        assert result["defects"] == []


# ── LinkDefectToExecutionResult ───────────────────────────────────────────


class TestLinkDefectToExecutionResult:
    """Tests for LinkingTools.link_defect_to_execution_result."""

    _OSLC_ER_URL = (
        "https://etm.example.com/qm/oslc_qm/contexts/PA-UUID-1"
        "/resources/com.ibm.rqm.execution.ExecutionResult/ER-UUID-1"
    )
    _MOCK_OSLC_RETURN = json.dumps({"executionresults": [{"url": _OSLC_ER_URL}]})

    @patch("tools.linking_tools.oslc_query")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/er/10")
    @patch(_PATCH_MAKE_REQUEST)
    def test_success_links_defect(self, mock_req, mock_url, mock_oslc):
        """Happy path: OSLC two-step links defect and returns success JSON."""
        mock_oslc.return_value = self._MOCK_OSLC_RETURN
        mock_req.side_effect = [
            _mock_response("{}"),  # proxy GET
            MagicMock(status_code=200, text=""),  # proxy PUT
            MagicMock(status_code=200, text=""),  # newLink POST
        ]

        result = json.loads(
            LinkingTools().link_defect_to_execution_result("10", "https://jira/PROJ-1", project_area=_PROJECT)
        )

        assert result["success"] is True
        assert result["defect_url"] == "https://jira/PROJ-1"

    @patch(_PATCH_MAKE_REQUEST)
    def test_empty_params_returns_error(self, mock_req):
        """Missing required params returns validation error."""
        result = json.loads(LinkingTools().link_defect_to_execution_result("", ""))

        assert "error" in result
        mock_req.assert_not_called()

    @patch("tools.linking_tools.oslc_query")
    @patch(_PATCH_BUILD_URL, return_value="https://etm/er/10")
    @patch(_PATCH_MAKE_REQUEST)
    def test_put_includes_defect_href(self, mock_req, mock_url, mock_oslc):
        """newLink POST registers the defect URL (cmUri) on the ETM side."""
        mock_oslc.return_value = self._MOCK_OSLC_RETURN
        mock_req.side_effect = [
            _mock_response("{}"),  # proxy GET
            MagicMock(status_code=200, text=""),  # proxy PUT
            MagicMock(status_code=200, text=""),  # newLink POST
        ]

        LinkingTools().link_defect_to_execution_result("10", "https://jira/BUG-5", project_area=_PROJECT)

        newlink_call = mock_req.call_args_list[2]
        newlink_body = newlink_call[1]["data"]
        if isinstance(newlink_body, bytes):
            newlink_body = newlink_body.decode("utf-8")
        assert "BUG-5" in newlink_body
