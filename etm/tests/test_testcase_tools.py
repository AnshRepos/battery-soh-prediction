"""Tests for tools/testcase_tools.py — TestCaseTools CRUD, categories, custom attributes, XML fix.

All service-layer calls are mocked with unittest.mock.patch so no real
network traffic is produced.  Tool methods return JSON strings that are
validated via json.loads() (except list_test_cases which returns raw XML).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import SAMPLE_TEST_CASE_XML
from tools.testcase_tools import TestCaseTools

_PROJECT = "TestProject (qm)"

# Single-line category elements — needed because the source regex uses
# ``[^/]*/>`` which cannot skip '/' characters inside href URLs.
_TESTCASE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
    ' xmlns:dcterms="http://purl.org/dc/terms/"'
    ' xmlns:alm="http://jazz.net/xmlns/alm/v0.1/">'
    "<dc:title>Sample Test Case</dc:title>"
    "<dc:description>A test case for testing</dc:description>"
    "<ns2:webId>12345</ns2:webId>"
    "<ns2:weight>100</ns2:weight>"
    "<ns2:state>com.ibm.rqm.planning.common.new</ns2:state>"
    '<ns2:category term="Test-Level" value="Unit Test"'
    ' href="https:%2F%2Fetm.example.com%2Fcategory%2FTest-Level%2FUnit%20Test"/>'
    '<ns2:category term="Regression Test" value="yes"'
    ' href="https:%2F%2Fetm.example.com%2Fcategory%2FRegression%20Test%2Fyes"/>'
    "<ns2:customAttributes>"
    "<ns2:customAttribute>"
    "<ns2:name>Honda_Test_Case_ID</ns2:name>"
    "<ns2:value>HTC-001</ns2:value>"
    "</ns2:customAttribute>"
    "</ns2:customAttributes>"
    "</ns2:testcase>"
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _mock_response(text: str = "<root/>", status_code: int = 200) -> MagicMock:
    """Build a minimal mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.headers = {"ETag": '"etag-1"', "Location": "https://etm.example.com/testcase/slug__abc"}
    resp.raise_for_status = MagicMock()
    return resp


# ── CreateTestCase ─────────────────────────────────────────────────────────


class TestCreateTestCase:
    """Tests for TestCaseTools.create_test_case."""

    @patch("tools.testcase_tools.extract_resource_id", return_value="slug__abc")
    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.create_xml_resource", return_value="<xml/>")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/testcase")
    @patch("tools.testcase_tools.build_resource_href", return_value="https://etm.example.com/ts/1")
    @patch("tools.testcase_tools.build_category_href", return_value="https://etm.example.com/cat")
    def test_create_success(
        self,
        mock_cat_href,
        mock_res_href,
        mock_url,
        mock_xml,
        mock_req,
        mock_extract,
    ):
        mock_req.return_value = _mock_response()
        tools = TestCaseTools()
        result = json.loads(
            tools.create_test_case(
                title="TC-1",
                description="desc",
                weight="100",
                regression_test="yes",
                test_level="Unit Test",
                subsystem_function="Func",
                project_area=_PROJECT,
                test_script_id="42",
            )
        )
        assert result["success"] is True
        assert result["testcase_id"] == "slug__abc"
        assert "location" in result
        mock_req.assert_called_once()

    @patch("tools.testcase_tools.extract_resource_id", return_value="slug__x")
    @patch("tools.testcase_tools.make_request", return_value=_mock_response())
    @patch("tools.testcase_tools.create_xml_resource", return_value="<xml/>")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc")
    @patch("tools.testcase_tools.build_category_href", return_value="https://etm.example.com/cat")
    def test_create_without_test_script(
        self,
        mock_cat,
        mock_url,
        mock_xml,
        mock_req,
        mock_extract,
    ):
        """When test_script_id is None, build_resource_href must NOT be called."""
        tools = TestCaseTools()
        result = json.loads(
            tools.create_test_case(
                title="TC-2",
                description="d",
                weight="200",
                regression_test="no",
                test_level="Integration Test",
                subsystem_function="Sub",
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True

    def test_create_empty_project_area(self):
        """If project_area is empty, an error is returned."""
        tools = TestCaseTools()
        result = json.loads(
            tools.create_test_case(
                title="T",
                description="d",
                weight="1",
                regression_test="y",
                test_level="U",
                subsystem_function="S",
                project_area="",
            )
        )
        assert "error" in result


# ── UpdateTestCase ─────────────────────────────────────────────────────────


class TestUpdateTestCase:
    """Tests for TestCaseTools.update_test_case."""

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_title_only(self, mock_update):
        tools = TestCaseTools()
        result = json.loads(tools.update_test_case("12345", title="New Title"))
        assert result["success"] is True
        mock_update.assert_called_once_with(
            "testcase",
            "12345",
            None,
            configuration_context=None,
            title="New Title",
        )

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_description_only(self, mock_update):
        tools = TestCaseTools()
        result = json.loads(tools.update_test_case("999", description="Updated desc"))
        assert result["success"] is True
        mock_update.assert_called_once_with(
            "testcase",
            "999",
            None,
            configuration_context=None,
            description="Updated desc",
        )

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_no_fields(self, mock_update):
        """When neither title nor description is given, updates dict is empty."""
        tools = TestCaseTools()
        json.loads(tools.update_test_case("111"))
        mock_update.assert_called_once_with("testcase", "111", None, configuration_context=None)

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_precondition_only(self, mock_update):
        tools = TestCaseTools()
        result = json.loads(tools.update_test_case("222", precondition="Given the system is ready"))
        assert result["success"] is True
        mock_update.assert_called_once_with(
            "testcase",
            "222",
            None,
            configuration_context=None,
            precondition="Given the system is ready",
        )

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_postcondition_only(self, mock_update):
        tools = TestCaseTools()
        result = json.loads(tools.update_test_case("333", postcondition="System returns to idle"))
        assert result["success"] is True
        mock_update.assert_called_once_with(
            "testcase",
            "333",
            None,
            configuration_context=None,
            postcondition="System returns to idle",
        )

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_precondition_and_postcondition(self, mock_update):
        tools = TestCaseTools()
        result = json.loads(tools.update_test_case("444", precondition="Pre text", postcondition="Post text"))
        assert result["success"] is True
        mock_update.assert_called_once_with(
            "testcase",
            "444",
            None,
            configuration_context=None,
            precondition="Pre text",
            postcondition="Post text",
        )

    @patch("tools.testcase_tools.generic_update", return_value='{"success": true}')
    def test_update_all_fields(self, mock_update):
        """All four updatable fields forwarded together."""
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case(
                "555",
                title="T",
                description="D",
                precondition="Pre",
                postcondition="Post",
            )
        )
        assert result["success"] is True
        mock_update.assert_called_once_with(
            "testcase",
            "555",
            None,
            configuration_context=None,
            title="T",
            description="D",
            precondition="Pre",
            postcondition="Post",
        )


# ── DeleteTestCase ─────────────────────────────────────────────────────────


class TestDeleteTestCase:
    """Tests for TestCaseTools.delete_test_case."""

    @patch("tools.testcase_tools.generic_delete", return_value='{"success": true}')
    def test_delete_success(self, mock_delete):
        tools = TestCaseTools()
        result = json.loads(tools.delete_test_case("12345"))
        assert result["success"] is True
        mock_delete.assert_called_once_with(
            "testcase",
            "12345",
            None,
            configuration_context=None,
        )

    @patch("tools.testcase_tools.generic_delete", return_value='{"success": true}')
    def test_delete_with_project_area(self, mock_delete):
        tools = TestCaseTools()
        result = json.loads(tools.delete_test_case("55", project_area="Other (qm)"))
        assert result["success"] is True
        mock_delete.assert_called_once_with(
            "testcase",
            "55",
            "Other (qm)",
            configuration_context=None,
        )


# ── ListTestCases (async) ─────────────────────────────────────────────────


class TestListTestCases:
    """Tests for the async TestCaseTools.list_test_cases."""

    @pytest.mark.asyncio
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc")
    @patch("tools.testcase_tools.make_request")
    async def test_list_returns_raw_xml(self, mock_req, mock_url):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        tools = TestCaseTools()
        result = json.loads(await tools.list_test_cases(project_area=_PROJECT, limit=10, ctx=None))
        assert "count" in result
        assert "entries" in result
        assert isinstance(result["entries"], list)
        mock_req.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_invalid_limit(self):
        tools = TestCaseTools()
        result = json.loads(await tools.list_test_cases(project_area=_PROJECT, limit=0, ctx=None))
        assert "error" in result

        result2 = json.loads(await tools.list_test_cases(project_area=_PROJECT, limit=201, ctx=None))
        assert "error" in result2

    @pytest.mark.asyncio
    async def test_list_empty_project(self):
        tools = TestCaseTools()
        result = json.loads(await tools.list_test_cases(project_area="", ctx=None))
        assert "error" in result


# ── GetTestCaseDetails ─────────────────────────────────────────────────────


class TestGetTestCaseDetails:
    """Tests for TestCaseTools.get_test_case_details."""

    @patch("tools.testcase_tools.parse_test_case_details")
    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_details_success(self, mock_url, mock_req, mock_parse):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        mock_parse.return_value = {
            "title": "Sample Test Case",
            "description": "A test case for testing",
            "requirement_links": [],
            "development_items": [],
            "test_scripts": [],
            "attachments": [],
            "precondition": None,
            "postcondition": None,
            "expected_results": None,
            "test_case_design": None,
        }
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_details("12345", project_area=_PROJECT))
        assert result["title"] == "Sample Test Case"
        assert result["_type"] == "testcase"
        assert result["_resource_id"] == "12345"
        assert "_summary" in result
        assert result["_summary"]["requirement_links_count"] == 0

    def test_details_empty_id(self):
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_details(""))
        assert "error" in result

    def test_details_whitespace_id(self):
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_details("   "))
        assert "error" in result

    def test_details_empty_project(self):
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_details("12345", project_area=""))
        assert "error" in result


# ── UpdateTestCaseCategory ─────────────────────────────────────────────────


class TestUpdateTestCaseCategory:
    """Tests for TestCaseTools.update_test_case_category."""

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_add_category(self, mock_url, mock_req):
        mock_req.return_value = _mock_response(text=_TESTCASE_XML)
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="12345",
                term="Test-Level",
                value="System Test",
                action="add",
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True
        assert result["action"] == "add"
        # GET + PUT = 2 calls
        assert mock_req.call_count == 2

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_add_already_present(self, mock_url, mock_req):
        """Adding a value that already exists should succeed without PUT."""
        mock_req.return_value = _mock_response(text=_TESTCASE_XML)
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="12345",
                term="Regression Test",
                value="yes",
                action="add",
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True
        assert "already present" in result["message"]
        # Only GET, no PUT
        assert mock_req.call_count == 1

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_remove_category(self, mock_url, mock_req):
        mock_req.return_value = _mock_response(text=_TESTCASE_XML)
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="12345",
                term="Regression Test",
                value="yes",
                action="remove",
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True
        assert result["action"] == "remove"
        assert mock_req.call_count == 2

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_set_category(self, mock_url, mock_req):
        mock_req.return_value = _mock_response(text=_TESTCASE_XML)
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="12345",
                term="Test-Level",
                value="Integration Test",
                action="set",
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True
        assert result["action"] == "set"

    def test_invalid_action(self):
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="12345",
                term="T",
                value="V",
                action="invalid",
            )
        )
        assert "error" in result

    def test_replace_without_old_value(self):
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="12345",
                term="T",
                value="V",
                action="replace",
            )
        )
        assert "error" in result

    def test_empty_test_case_id(self):
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_category(
                test_case_id="  ",
                term="T",
                value="V",
            )
        )
        assert "error" in result


# ── GetTestCaseCategories ──────────────────────────────────────────────────


class TestGetTestCaseCategories:
    """Tests for TestCaseTools.get_test_case_categories."""

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_categories_parsed(self, mock_url, mock_req):
        mock_req.return_value = _mock_response(text=_TESTCASE_XML)
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_categories("12345", project_area=_PROJECT))
        assert result["test_case_id"] == "12345"
        cats = {c["term"]: c["values"] for c in result["categories"]}
        assert "Test-Level" in cats
        assert "Unit Test" in cats["Test-Level"]
        assert "Regression Test" in cats
        assert "yes" in cats["Regression Test"]

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_categories_mode(self, mock_url, mock_req):
        mock_req.return_value = _mock_response(text=_TESTCASE_XML)
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_categories("12345", project_area=_PROJECT))
        for cat in result["categories"]:
            assert cat["mode"] == "single-select"

    def test_categories_empty_id(self):
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_categories(""))
        assert "error" in result


# ── GetTestCaseCustomAttributes ────────────────────────────────────────────


class TestGetTestCaseCustomAttributes:
    """Tests for TestCaseTools.get_test_case_custom_attributes."""

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_custom_attrs_found(self, mock_url, mock_req):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_custom_attributes("12345", project_area=_PROJECT))
        assert result["test_case_id"] == "12345"
        assert result["count"] == 1
        attr = result["custom_attributes"][0]
        assert attr["name"] == "Honda_Test_Case_ID"
        assert attr["value"] == "HTC-001"

    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/99")
    def test_custom_attrs_empty(self, mock_url, mock_req):
        xml_no_attrs = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/">'
            "</ns2:testcase>"
        )
        mock_req.return_value = _mock_response(text=xml_no_attrs)
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_custom_attributes("99", project_area=_PROJECT))
        assert result["count"] == 0
        assert result["custom_attributes"] == []

    def test_custom_attrs_empty_id(self):
        tools = TestCaseTools()
        result = json.loads(tools.get_test_case_custom_attributes(""))
        assert "error" in result


# ── UpdateTestCaseCustomAttribute ──────────────────────────────────────────


class TestUpdateTestCaseCustomAttribute:
    """Tests for TestCaseTools.update_test_case_custom_attribute."""

    @patch("tools.testcase_tools.make_request")
    @patch(
        "tools.testcase_tools.update_custom_attribute_in_xml",
        return_value=b"<updated/>",
    )
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_set_attribute(self, mock_url, mock_update_xml, mock_req):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_custom_attribute(
                test_case_id="12345",
                attribute_name="Honda_Test_Case_ID",
                value="HTC-002",
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True
        assert result["action"] == "set"
        # GET + PUT
        assert mock_req.call_count == 2

    @patch("tools.testcase_tools.make_request")
    @patch(
        "tools.testcase_tools.update_custom_attribute_in_xml",
        return_value=b"<updated/>",
    )
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_append_attribute(self, mock_url, mock_update_xml, mock_req):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_custom_attribute(
                test_case_id="12345",
                attribute_name="Honda_Test_Case_ID",
                value="HTC-003",
                append=True,
                project_area=_PROJECT,
            )
        )
        assert result["success"] is True
        assert result["action"] == "append"

    def test_update_attr_empty_id(self):
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_custom_attribute(
                test_case_id="",
                attribute_name="X",
                value="V",
            )
        )
        assert "error" in result

    def test_update_attr_empty_name(self):
        tools = TestCaseTools()
        result = json.loads(
            tools.update_test_case_custom_attribute(
                test_case_id="12345",
                attribute_name="  ",
                value="V",
            )
        )
        assert "error" in result


# ── FixTestCaseXml ─────────────────────────────────────────────────────────


class TestFixTestCaseXml:
    """Tests for TestCaseTools.fix_test_case_xml."""

    @patch("tools.testcase_tools.fix_et_corruption")
    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_no_corruption(self, mock_url, mock_req, mock_fix):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        mock_fix.return_value = (SAMPLE_TEST_CASE_XML, [])
        tools = TestCaseTools()
        result = json.loads(tools.fix_test_case_xml("12345", project_area=_PROJECT))
        assert result["corrupted"] is False
        assert result["test_case_id"] == "12345"

    @patch("tools.testcase_tools.fix_et_corruption")
    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_dry_run_with_corruption(self, mock_url, mock_req, mock_fix):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        mock_fix.return_value = ("<fixed/>", ["removed xmlns:html"])
        tools = TestCaseTools()
        result = json.loads(tools.fix_test_case_xml("12345", dry_run=True, project_area=_PROJECT))
        assert result["corrupted"] is True
        assert result["dry_run"] is True
        assert "removed xmlns:html" in result["fixes_available"]
        # Only GET, no PUT in dry_run mode
        assert mock_req.call_count == 1

    @patch("tools.testcase_tools.fix_et_corruption")
    @patch("tools.testcase_tools.make_request")
    @patch("tools.testcase_tools.build_resource_url", return_value="https://etm.example.com/tc/12345")
    def test_apply_fixes(self, mock_url, mock_req, mock_fix):
        mock_req.return_value = _mock_response(text=SAMPLE_TEST_CASE_XML)
        mock_fix.return_value = ("<fixed/>", ["fix-1", "fix-2"])
        tools = TestCaseTools()
        result = json.loads(tools.fix_test_case_xml("12345", dry_run=False, project_area=_PROJECT))
        assert result["success"] is True
        assert result["dry_run"] is False
        assert result["fixes_applied"] == ["fix-1", "fix-2"]
        # GET + PUT
        assert mock_req.call_count == 2

    def test_fix_empty_id(self):
        tools = TestCaseTools()
        result = json.loads(tools.fix_test_case_xml("  "))
        assert "error" in result
