"""Integration tests for the ETMToolsManager aggregated tool class.

Verifies that ETMToolsManager correctly inherits from all nine parent
tool classes and exposes all 54 expected tool methods.
"""

import pytest
from tools import ETMToolsManager
from tools.bulk_tools import BulkTools
from tools.connection_tools import ConnectionTools
from tools.execution_tools import ExecutionTools
from tools.linking_tools import LinkingTools
from tools.misc_tools import MiscTools
from tools.testcase_tools import TestCaseTools
from tools.testplan_tools import TestPlanTools
from tools.testsuite_tools import TestSuiteTools
from tools.traceability_tools import TraceabilityTools

# ── Parent classes ─────────────────────────────────────────────────────────

_PARENT_CLASSES = (
    ConnectionTools,
    TestPlanTools,
    TestCaseTools,
    TestSuiteTools,
    ExecutionTools,
    LinkingTools,
    TraceabilityTools,
    BulkTools,
    MiscTools,
)

# ── Expected tool methods grouped by parent class ──────────────────────────

_CONNECTION_TOOLS = [
    "test_project_connection",
    "list_project_areas",
    "oslc_query_resources",
    "get_resource",
    "list_project_components",
    "list_cm_configurations",
]

_TEST_PLAN_TOOLS = [
    "create_test_plan",
    "update_test_plan",
    "delete_test_plan",
    "get_test_plan_statistics",
]

_TEST_CASE_TOOLS = [
    "list_test_cases",
    "create_test_case",
    "update_test_case",
    "delete_test_case",
    "get_test_case_details",
    "update_test_case_category",
    "get_test_case_categories",
    "get_test_case_custom_attributes",
    "update_test_case_custom_attribute",
    "fix_test_case_xml",
    "get_architecture_element_links",
    "update_architecture_element_links",
    "duplicate_test_case",
]

_TEST_SUITE_TOOLS = [
    "create_test_suite",
    "update_test_suite",
    "delete_test_suite",
]

_EXECUTION_TOOLS = [
    "get_attachment",
    "get_test_plan_template",
    "list_execution_results",
    "get_execution_result",
    "create_execution_record",
    "update_execution_result",
    "get_requirement_custom_attributes",
    "get_requirement_links",
]

_LINKING_TOOLS = [
    "add_test_cases_to_suite",
    "link_testcase_to_testplan",
    "link_test_suite_to_plan",
    "get_test_cases_by_use_case",
    "get_failed_executions_without_defects",
    "get_execution_defects",
    "link_defect_to_execution_result",
]

_TRACEABILITY_TOOLS = [
    "get_test_plan_tree",
    "get_execution_timeline",
    "get_requirement_to_test_mapping",
    "find_orphaned_test_cases",
    "get_execution_results_by_test_plan",
]

_BULK_TOOLS = [
    "bulk_create_test_cases",
    "bulk_execute_tests",
]

_MISC_TOOLS = [
    "list_test_scripts",
    "get_test_script",
    "create_test_script",
    "list_build_records",
    "get_build_record",
    "list_test_execution_records",
    "get_test_execution_record",
]

ALL_TOOL_METHODS = (
    _CONNECTION_TOOLS
    + _TEST_PLAN_TOOLS
    + _TEST_CASE_TOOLS
    + _TEST_SUITE_TOOLS
    + _EXECUTION_TOOLS
    + _LINKING_TOOLS
    + _TRACEABILITY_TOOLS
    + _BULK_TOOLS
    + _MISC_TOOLS
)

EXPECTED_TOOL_COUNT = 55


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def manager() -> ETMToolsManager:
    """Create a fresh ETMToolsManager instance."""
    return ETMToolsManager()


# ── Tests ──────────────────────────────────────────────────────────────────


class TestETMToolsManagerInstantiation:
    """Verify ETMToolsManager can be created."""

    def test_instantiation(self, manager: ETMToolsManager) -> None:
        assert manager is not None

    def test_is_etm_tools_manager(self, manager: ETMToolsManager) -> None:
        assert isinstance(manager, ETMToolsManager)


class TestETMToolsManagerInheritance:
    """Verify ETMToolsManager inherits from all nine parent classes."""

    @pytest.mark.parametrize("parent_cls", _PARENT_CLASSES, ids=lambda c: c.__name__)
    def test_inherits_from_parent(self, manager: ETMToolsManager, parent_cls: type) -> None:
        assert isinstance(manager, parent_cls), f"ETMToolsManager should inherit from {parent_cls.__name__}"

    def test_parent_class_count(self) -> None:
        """MRO should contain all 9 parent classes (plus object)."""
        mro_classes = set(ETMToolsManager.__mro__)
        for parent_cls in _PARENT_CLASSES:
            assert parent_cls in mro_classes, f"{parent_cls.__name__} not found in MRO"


class TestETMToolsManagerMethods:
    """Verify all 54 expected tool methods exist and are callable."""

    def test_expected_tool_count(self) -> None:
        assert (
            len(ALL_TOOL_METHODS) == EXPECTED_TOOL_COUNT
        ), f"Expected {EXPECTED_TOOL_COUNT} tool methods, got {len(ALL_TOOL_METHODS)}"

    @pytest.mark.parametrize("method_name", ALL_TOOL_METHODS)
    def test_method_exists(self, manager: ETMToolsManager, method_name: str) -> None:
        assert hasattr(manager, method_name), f"ETMToolsManager is missing method '{method_name}'"

    @pytest.mark.parametrize("method_name", ALL_TOOL_METHODS)
    def test_method_is_callable(self, manager: ETMToolsManager, method_name: str) -> None:
        method = getattr(manager, method_name)
        assert callable(method), f"'{method_name}' on ETMToolsManager is not callable"

    # ── Group-level existence checks ───────────────────────────────────

    def test_connection_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _CONNECTION_TOOLS:
            assert hasattr(manager, name), f"Missing ConnectionTools method: {name}"

    def test_test_plan_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _TEST_PLAN_TOOLS:
            assert hasattr(manager, name), f"Missing TestPlanTools method: {name}"

    def test_test_case_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _TEST_CASE_TOOLS:
            assert hasattr(manager, name), f"Missing TestCaseTools method: {name}"

    def test_test_suite_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _TEST_SUITE_TOOLS:
            assert hasattr(manager, name), f"Missing TestSuiteTools method: {name}"

    def test_execution_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _EXECUTION_TOOLS:
            assert hasattr(manager, name), f"Missing ExecutionTools method: {name}"

    def test_linking_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _LINKING_TOOLS:
            assert hasattr(manager, name), f"Missing LinkingTools method: {name}"

    def test_traceability_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _TRACEABILITY_TOOLS:
            assert hasattr(manager, name), f"Missing TraceabilityTools method: {name}"

    def test_bulk_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _BULK_TOOLS:
            assert hasattr(manager, name), f"Missing BulkTools method: {name}"

    def test_misc_tools_methods(self, manager: ETMToolsManager) -> None:
        for name in _MISC_TOOLS:
            assert hasattr(manager, name), f"Missing MiscTools method: {name}"
