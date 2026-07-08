"""Tests for tools/misc_tools.py — thin wrappers around generic CRUD functions."""

import json
from unittest.mock import patch
from xml.sax.saxutils import escape

from tools.misc_tools import MiscTools


class TestListTestScripts:
    """Tests for MiscTools.list_test_scripts."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_list")
    def test_delegates_to_generic_list(self, mock_list):
        mock_list.return_value = json.dumps({"scripts": []})
        result = self.tools.list_test_scripts(project_area="Proj (qm)", limit=10)

        mock_list.assert_called_once_with("testscript", "Proj (qm)", 10, configuration_context=None)
        assert json.loads(result) == {"scripts": []}

    @patch("tools.misc_tools.generic_list")
    def test_default_limit(self, mock_list):
        mock_list.return_value = json.dumps({"scripts": []})
        self.tools.list_test_scripts()

        mock_list.assert_called_once_with("testscript", None, 50, configuration_context=None)


class TestGetTestScript:
    """Tests for MiscTools.get_test_script."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_get")
    def test_delegates_to_generic_get(self, mock_get):
        mock_get.return_value = json.dumps({"id": "42", "title": "Script A"})
        result = self.tools.get_test_script("42", project_area="Proj (qm)")

        mock_get.assert_called_once_with("testscript", "42", "Proj (qm)", configuration_context=None)
        assert json.loads(result)["id"] == "42"


class TestCreateTestScript:
    """Tests for MiscTools.create_test_script."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_create")
    def test_without_steps(self, mock_create):
        mock_create.return_value = json.dumps({"success": True, "testscript_id": "37290"})
        result = self.tools.create_test_script("My Script", "A description", project_area="CC-DA ESM Sandbox")

        mock_create.assert_called_once_with(
            "testscript",
            "My Script",
            "A description",
            "CC-DA ESM Sandbox",
            configuration_context=None,
            scripttype="com.ibm.rqm.planning.common.scripttype.manual",
        )
        assert json.loads(result)["success"] is True

    @patch("tools.misc_tools.generic_create")
    def test_with_steps(self, mock_create):
        mock_create.return_value = json.dumps({"success": True, "testscript_id": "37290"})
        self.tools.create_test_script("Script B", "Desc", project_area="CC-DA ESM Sandbox", steps="Step 1")

        expected_steps = f"<div xmlns='http://www.w3.org/1999/xhtml'>{escape('Step 1')}</div>"
        mock_create.assert_called_once_with(
            "testscript",
            "Script B",
            "Desc",
            "CC-DA ESM Sandbox",
            configuration_context=None,
            scripttype="com.ibm.rqm.planning.common.scripttype.manual",
            steps=expected_steps,
        )

    @patch("tools.misc_tools.generic_create")
    def test_steps_with_special_chars(self, mock_create):
        mock_create.return_value = json.dumps({"success": True})
        self.tools.create_test_script("S", "D", project_area="P", steps="a < b & c")

        call_kwargs = mock_create.call_args.kwargs
        assert "&lt;" in call_kwargs["steps"]
        assert "&amp;" in call_kwargs["steps"]


class TestListBuildRecords:
    """Tests for MiscTools.list_build_records."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_list")
    def test_delegates_to_generic_list(self, mock_list):
        mock_list.return_value = json.dumps({"builds": []})
        result = self.tools.list_build_records(project_area="Proj (qm)", limit=25)

        mock_list.assert_called_once_with("buildrecord", "Proj (qm)", 25, configuration_context=None)
        assert json.loads(result) == {"builds": []}


class TestGetBuildRecord:
    """Tests for MiscTools.get_build_record."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_get")
    def test_delegates_to_generic_get(self, mock_get):
        mock_get.return_value = json.dumps({"id": "b1"})
        result = self.tools.get_build_record("b1", project_area="Proj (qm)")

        mock_get.assert_called_once_with("buildrecord", "b1", "Proj (qm)", configuration_context=None)
        assert json.loads(result)["id"] == "b1"


class TestListTestExecutionRecords:
    """Tests for MiscTools.list_test_execution_records."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_list")
    def test_delegates_to_generic_list(self, mock_list):
        mock_list.return_value = json.dumps({"records": []})
        result = self.tools.list_test_execution_records(project_area="Proj (qm)", limit=20)

        mock_list.assert_called_once_with("executionworkitem", "Proj (qm)", 20, configuration_context=None)
        assert json.loads(result) == {"records": []}


class TestGetTestExecutionRecord:
    """Tests for MiscTools.get_test_execution_record."""

    def setup_method(self):
        self.tools = MiscTools()

    @patch("tools.misc_tools.generic_get")
    def test_delegates_to_generic_get(self, mock_get):
        mock_get.return_value = json.dumps({"id": "tcer_99"})
        result = self.tools.get_test_execution_record("tcer_99", project_area="Proj (qm)")

        mock_get.assert_called_once_with(
            "executionworkitem",
            "tcer_99",
            "Proj (qm)",
            configuration_context=None,
        )
        assert json.loads(result)["id"] == "tcer_99"
