"""Tests for tools/traceability_tools.py — plan trees, timelines, traceability, and orphan detection."""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from tools.traceability_tools import TraceabilityTools

# ── Constants ─────────────────────────────────────────────────────────────

_PROJECT = "TestProject (qm)"

_PATCH_MAKE_REQUEST = "tools.traceability_tools.make_request"
_PATCH_BUILD_URL = "tools.traceability_tools.build_resource_url"
_PATCH_COLLECT = "tools.traceability_tools.collect_paginated_entries"
_PATCH_FETCH_ALL = "tools.traceability_tools.fetch_all_pages"

_PLAN_XML = (
    '<ns2:testplan xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:title>Master Plan</dc:title>"
    '<ns2:testsuite href="urn:suite:100"/>'
    '<ns2:testcase href="urn:tc:200"/>'
    "</ns2:testplan>"
)

_SUITE_XML = (
    '<ns2:testsuite xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:title>Suite Alpha</dc:title>"
    '<ns2:testcase href="urn:tc:300"/>'
    "</ns2:testsuite>"
)

_TC_XML_TMPL = (
    '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
    "<dc:title>{title}</dc:title>"
    "</ns2:testcase>"
)

_TODAY = datetime.now().strftime("%Y-%m-%d")

_TIMELINE_FEED_XML = (
    '<feed xmlns="http://www.w3.org/2005/Atom"'
    ' xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
    "<entry><content><ns2:executionresult>"
    '<ns2:testplan href="urn:plan:P1"/>'
    "<ns2:state>com.ibm.rqm.execution.common.state.passed</ns2:state>"
    f"<ns2:updated>{_TODAY}T08:00:00Z</ns2:updated>"
    "</ns2:executionresult></content></entry>"
    "<entry><content><ns2:executionresult>"
    '<ns2:testplan href="urn:plan:P1"/>'
    "<ns2:state>com.ibm.rqm.execution.common.state.failed</ns2:state>"
    f"<ns2:updated>{_TODAY}T09:00:00Z</ns2:updated>"
    "</ns2:executionresult></content></entry>"
    "<entry><content><ns2:executionresult>"
    '<ns2:testplan href="urn:plan:OTHER"/>'
    "<ns2:state>com.ibm.rqm.execution.common.state.passed</ns2:state>"
    f"<ns2:updated>{_TODAY}T10:00:00Z</ns2:updated>"
    "</ns2:executionresult></content></entry>"
    "</feed>"
)

_EXEC_RESULTS_FEED_XML = (
    '<feed xmlns="http://www.w3.org/2005/Atom"'
    ' xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
    "<entry><content><ns2:executionresult>"
    '<ns2:testplan href="urn:plan:P1"/>'
    "</ns2:executionresult></content></entry>"
    "<entry><content><ns2:executionresult>"
    '<ns2:testplan href="urn:plan:OTHER"/>'
    "</ns2:executionresult></content></entry>"
    "</feed>"
)


# ── Helpers ───────────────────────────────────────────────────────────────


def _mock_response(text: str, etag: str = '"etag-1"') -> MagicMock:
    """Return a MagicMock imitating a requests.Response."""
    resp = MagicMock()
    resp.text = text
    resp.headers = {"ETag": etag}
    resp.status_code = 200
    return resp


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def tools() -> TraceabilityTools:
    """Return a fresh TraceabilityTools instance."""
    return TraceabilityTools()


# ── GetTestPlanTree ───────────────────────────────────────────────────────


class TestGetTestPlanTree:
    """Tests for TraceabilityTools.get_test_plan_tree."""

    @patch(_PATCH_BUILD_URL, return_value="https://etm/resource")
    @patch(_PATCH_MAKE_REQUEST)
    def test_success_returns_tree(self, mock_req, mock_url):
        """Happy path builds full tree with suites and direct test cases."""
        plan_resp = _mock_response(_PLAN_XML)
        suite_resp = _mock_response(_SUITE_XML)
        tc300_resp = _mock_response(_TC_XML_TMPL.format(title="TC 300"))
        tc200_resp = _mock_response(_TC_XML_TMPL.format(title="TC 200"))
        mock_req.side_effect = [plan_resp, suite_resp, tc300_resp, tc200_resp]

        result = json.loads(TraceabilityTools().get_test_plan_tree("P1", project_area=_PROJECT))

        plan = result["test_plan"]
        assert plan["title"] == "Master Plan"
        assert len(plan["test_suites"]) == 1
        assert plan["test_suites"][0]["title"] == "Suite Alpha"
        assert len(plan["direct_test_cases"]) == 1
        assert result["statistics"]["total_cases"] == 2

    @patch(_PATCH_MAKE_REQUEST)
    def test_empty_id_returns_error(self, mock_req):
        """Empty test_plan_id returns validation error."""
        result = json.loads(TraceabilityTools().get_test_plan_tree(""))

        assert "error" in result
        mock_req.assert_not_called()

    @patch(_PATCH_BUILD_URL, return_value="https://etm/resource")
    @patch(_PATCH_MAKE_REQUEST)
    def test_statistics_counts(self, mock_req, mock_url):
        """Statistics section has correct aggregate counts."""
        plan_resp = _mock_response(_PLAN_XML)
        suite_resp = _mock_response(_SUITE_XML)
        tc300_resp = _mock_response(_TC_XML_TMPL.format(title="TC 300"))
        tc200_resp = _mock_response(_TC_XML_TMPL.format(title="TC 200"))
        mock_req.side_effect = [plan_resp, suite_resp, tc300_resp, tc200_resp]

        result = json.loads(TraceabilityTools().get_test_plan_tree("P1", project_area=_PROJECT))

        stats = result["statistics"]
        assert stats["total_suites"] == 1
        assert stats["total_cases_in_suites"] == 1
        assert stats["total_direct_test_cases"] == 1


# ── GetExecutionTimeline ──────────────────────────────────────────────────


class TestGetExecutionTimeline:
    """Tests for TraceabilityTools.get_execution_timeline."""

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_FETCH_ALL)
    def test_filters_by_plan(self, mock_fetch, mock_url):
        """Only entries matching the test plan href are counted."""
        mock_fetch.return_value = ET.fromstring(_TIMELINE_FEED_XML)

        result = json.loads(TraceabilityTools().get_execution_timeline("P1", days_back=365, project_area=_PROJECT))

        assert result["success"] is True
        assert result["summary"]["total_executions"] == 2

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_FETCH_ALL)
    def test_pass_rate_calculation(self, mock_fetch, mock_url):
        """Overall pass rate is computed correctly (1 passed / 2 total = 50%)."""
        mock_fetch.return_value = ET.fromstring(_TIMELINE_FEED_XML)

        result = json.loads(TraceabilityTools().get_execution_timeline("P1", days_back=365, project_area=_PROJECT))

        assert result["summary"]["overall_pass_rate"] == 50.0

    def test_invalid_days_back_returns_error(self):
        """days_back outside 1-365 returns validation error."""
        result = json.loads(TraceabilityTools().get_execution_timeline("P1", days_back=0))

        assert "error" in result

    def test_empty_plan_id_returns_error(self):
        """Empty test_plan_id returns validation error."""
        result = json.loads(TraceabilityTools().get_execution_timeline(""))

        assert "error" in result


# ── GetRequirementToTestMapping ───────────────────────────────────────────


class TestGetRequirementToTestMapping:
    """Tests for TraceabilityTools.get_requirement_to_test_mapping."""

    _ENTRIES = [
        {"identifier": "tc1", "title": "Test 1", "validates": ["https://req/1"]},
        {"identifier": "tc2", "title": "Test 2", "validates": ["https://req/1", "https://req/2"]},
        {"identifier": "tc3", "title": "Test 3"},
    ]

    @patch(_PATCH_BUILD_URL, return_value="https://etm/tc")
    @patch(_PATCH_COLLECT, return_value=_ENTRIES)
    def test_builds_mapping(self, mock_collect, mock_url):
        """Two requirements are mapped; tc3 is orphaned."""
        result = json.loads(TraceabilityTools().get_requirement_to_test_mapping(project_area=_PROJECT))

        assert result["success"] is True
        analysis = result["coverage_analysis"]
        assert analysis["total_requirements"] == 2
        assert analysis["orphaned_test_cases"] == 1

    @patch(_PATCH_BUILD_URL, return_value="https://etm/tc")
    @patch(_PATCH_COLLECT, return_value=_ENTRIES)
    def test_requirement_sorted_by_coverage(self, mock_collect, mock_url):
        """Requirements are sorted descending by coverage_count."""
        result = json.loads(TraceabilityTools().get_requirement_to_test_mapping(project_area=_PROJECT))

        reqs = result["requirements"]
        assert reqs[0]["coverage_count"] >= reqs[1]["coverage_count"]

    @patch(_PATCH_BUILD_URL, return_value="https://etm/tc")
    @patch(_PATCH_COLLECT, return_value=[])
    def test_empty_entries(self, mock_collect, mock_url):
        """No entries yields zero requirements and zero orphans."""
        result = json.loads(TraceabilityTools().get_requirement_to_test_mapping(project_area=_PROJECT))

        assert result["coverage_analysis"]["total_requirements"] == 0
        assert result["coverage_analysis"]["orphaned_test_cases"] == 0


# ── FindOrphanedTestCases ─────────────────────────────────────────────────


class TestFindOrphanedTestCases:
    """Tests for TraceabilityTools.find_orphaned_test_cases."""

    _TC_ENTRIES = [
        {"identifier": "tc1", "title": "T1", "validates": "req1"},
        {"identifier": "tc2", "title": "T2"},
    ]
    _TP_ENTRIES = [
        {"testcase": "urn:tc:tc1"},
    ]

    @patch(_PATCH_BUILD_URL, return_value="https://etm/resource")
    @patch(_PATCH_COLLECT)
    def test_detects_orphans(self, mock_collect, mock_url):
        """tc2 has no requirements and no plan refs → completely isolated."""
        mock_collect.side_effect = [self._TC_ENTRIES, self._TP_ENTRIES]

        result = json.loads(TraceabilityTools().find_orphaned_test_cases(project_area=_PROJECT))

        assert result["success"] is True
        stats = result["statistics"]
        assert stats["total_test_cases"] == 2
        assert stats["completely_isolated_count"] == 1
        isolated_ids = [tc["id"] for tc in result["orphaned_categories"]["completely_isolated"]]
        assert "tc2" in isolated_ids

    @patch(_PATCH_BUILD_URL, return_value="https://etm/resource")
    @patch(_PATCH_COLLECT)
    def test_tc1_not_isolated(self, mock_collect, mock_url):
        """tc1 has requirements and is in a plan → not isolated."""
        mock_collect.side_effect = [self._TC_ENTRIES, self._TP_ENTRIES]

        result = json.loads(TraceabilityTools().find_orphaned_test_cases(project_area=_PROJECT))

        isolated_ids = [tc["id"] for tc in result["orphaned_categories"]["completely_isolated"]]
        assert "tc1" not in isolated_ids

    @patch(_PATCH_BUILD_URL, return_value="https://etm/resource")
    @patch(_PATCH_COLLECT)
    def test_orphan_percentage(self, mock_collect, mock_url):
        """Orphan percentage is 50% (1 isolated / 2 total)."""
        mock_collect.side_effect = [self._TC_ENTRIES, self._TP_ENTRIES]

        result = json.loads(TraceabilityTools().find_orphaned_test_cases(project_area=_PROJECT))

        assert result["statistics"]["orphan_percentage"] == 50.0


# ── GetExecutionResultsByTestPlan ─────────────────────────────────────────


class TestGetExecutionResultsByTestPlan:
    """Tests for TraceabilityTools.get_execution_results_by_test_plan."""

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_FETCH_ALL)
    def test_returns_filtered_xml(self, mock_fetch, mock_url):
        """Returns XML string (not JSON) containing only matching entries."""
        mock_fetch.return_value = ET.fromstring(_EXEC_RESULTS_FEED_XML)

        xml_str = TraceabilityTools().get_execution_results_by_test_plan("P1", project_area=_PROJECT)

        # The result is raw XML, not JSON.
        root = ET.fromstring(xml_str)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//atom:entry", ns)
        assert len(entries) == 1

    @patch(_PATCH_BUILD_URL, return_value="https://etm/er")
    @patch(_PATCH_FETCH_ALL)
    def test_no_match_returns_empty_feed(self, mock_fetch, mock_url):
        """No matching entries returns feed XML with zero entries."""
        mock_fetch.return_value = ET.fromstring(_EXEC_RESULTS_FEED_XML)

        xml_str = TraceabilityTools().get_execution_results_by_test_plan("NONEXISTENT", project_area=_PROJECT)

        root = ET.fromstring(xml_str)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        assert len(root.findall(".//atom:entry", ns)) == 0

    def test_empty_plan_id_returns_error(self):
        """Empty test_plan_id returns JSON error."""
        result = json.loads(TraceabilityTools().get_execution_results_by_test_plan(""))

        assert "error" in result
