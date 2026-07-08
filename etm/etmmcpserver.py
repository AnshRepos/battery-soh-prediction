#!/usr/bin/env python3
"""
ETM MCP Server -- Entry Point

An IBM Engineering Test Management (ETM) MCP server entry point.
Exposes ETM quality management operations through MCP for use with
VS Code / GitHub Copilot Chat.

Provides comprehensive test management capabilities including test plans,
test cases, test suites, execution results, OSLC queries, traceability,
and bulk operations.
"""

import logging
import os
import signal
import sys

# Add project root to path so that core/, services/, tools/ resolve
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.config import get_mcp_init_vars, setup_logging  # noqa: E402
from fastmcp import FastMCP  # noqa: E402
from prompts.prompts import register_prompts  # noqa: E402
from tools import ETMToolsManager  # noqa: E402


class MCPServerRunner:
    """Main server runner class with lifecycle management."""

    def __init__(self, transport: str = "stdio"):
        setup_logging(transport=transport)
        self.logger = logging.getLogger(__name__)
        self._setup_signal_handlers()

        self.mcp = FastMCP(name="ETMMCP Server")
        self.tools_manager = ETMToolsManager()
        self._register_tools()
        register_prompts(self.mcp)
        self.logger.info("ETM MCP Server initialized successfully.")

    def _register_tools(self) -> None:
        """Register all MCP tools with FastMCP."""
        try:
            # -- Connection & utility tools (ConnectionTools) --
            self.mcp.tool(
                name="test_project_connection",
                description=(
                    "Test connection to a specific ETM project area. "
                    "Pass the project area NAME as a string (e.g., 'My Project (qm)'). "
                    "Use list_project_areas() first to discover available project names."
                ),
            )(self.tools_manager.test_project_connection)

            self.mcp.tool(
                name="list_project_areas",
                description=(
                    "List all available ETM project areas. Returns project names, URLs, and "
                    "project_area_uri for each project. START HERE to discover projects. "
                    "Workflow: list_project_areas() -> list_project_components(project_area_uri) "
                    "-> list_cm_configurations(project_area_uri) -> use configuration_context in other tools."
                ),
            )(self.tools_manager.list_project_areas)

            self.mcp.tool(
                name="oslc_query_resources",
                description=(
                    "Search for ETM resources by name, ID, date, or other properties using OSLC server-side filtering. "
                    "PREFERRED tool for finding specific resources. "
                    "resource_type must be one of: testcase, testplan, testsuite, testscript, executionresult, executionworkitem. "
                    'Use oslc:shortId="28931" (NOT dcterms:identifier) for ID lookups. '
                    "String values in where clauses MUST be in double quotes. "
                    "After finding a testcase ID, use get_test_case_details() for full details. "
                    "For testplans, use get_resource() or get_test_plan_tree()."
                ),
            )(self.tools_manager.oslc_query_resources)

            self.mcp.tool(
                name="get_resource",
                description=(
                    "Get full details of any ETM resource by type and numeric webId. "
                    "resource_type: testplan, testcase, testsuite, testscript, testphase, "
                    "executionresult, executionworkitem, attachment, template, buildrecord, configuration. "
                    "resource_id must be a numeric webId (e.g., '3435411'), NOT a slug identifier. "
                    "For testcase details, prefer get_test_case_details() instead (richer parsed output). "
                    "Returns parsed JSON."
                ),
            )(self.tools_manager.get_resource)

            self.mcp.tool(
                name="list_project_components",
                description=(
                    "List all Configuration Management (CM) components in an ETM project area. "
                    "Requires project_area_uri (a full URL from list_project_areas(), e.g., "
                    "'https://server/qm/process/project-areas/<uuid>'). "
                    "Next step: call list_cm_configurations() with the returned component_uri. "
                    "If no components found, the project does not use CM and configuration_context is not needed."
                ),
            )(self.tools_manager.list_project_components)

            self.mcp.tool(
                name="list_cm_configurations",
                description=(
                    "List CM streams and baselines to get configuration_context URIs. "
                    "NOT for test configurations (OS/browser/HW combos) — use get_resource(resource_type='configuration') for that. "
                    "Pass project_area_uri (for ALL components) or component_uri (for one component). "
                    "Use a returned stream URI directly as configuration_context in other tools. "
                    "Workflow: list_project_areas() -> list_project_components() -> list_cm_configurations()."
                ),
            )(self.tools_manager.list_cm_configurations)

            # -- Test plan tools (TestPlanTools) --
            self.mcp.tool(
                name="create_test_plan",
                description=(
                    "Create a new test plan. Requires: title, description, release (must match an existing "
                    "Release category value, e.g., 'Release 1.0'), and test_level (must match an existing "
                    "Test Level category value, e.g., 'Integration Test'). "
                    "project_area is the project name string (defaults to ETM_PROJECT_AREA env var)."
                ),
            )(self.tools_manager.create_test_plan)

            self.mcp.tool(
                name="update_test_plan",
                description=(
                    "Update an existing test plan's title, description, start/end date, or owner. "
                    "test_plan_id must be a numeric webId (e.g., '105520'), NOT a slug identifier. "
                    "Only pass the fields you want to change."
                ),
            )(self.tools_manager.update_test_plan)

            self.mcp.tool(
                name="delete_test_plan",
                description=(
                    "Permanently delete a test plan. DESTRUCTIVE — cannot be undone. "
                    "test_plan_id must be a numeric webId."
                ),
            )(self.tools_manager.delete_test_plan)

            self.mcp.tool(
                name="get_test_plan_statistics",
                description=(
                    "Get execution analysis for a test plan. "
                    "mode='statistics' (default): pass/fail/blocked counts and pass rate. "
                    "mode='timeline': daily execution trend over days_back days (1-365, default 30). "
                    "mode='raw': full execution result details. "
                    "test_plan_id must be a numeric webId."
                ),
            )(self.tools_manager.get_test_plan_statistics)

            # -- Test case tools (TestCaseTools) --
            self.mcp.tool(
                name="list_test_cases",
                description=(
                    "List test cases with pagination. Returns parsed JSON with count, page, page_size, "
                    "entries, and optional has_more. "
                    "Use oslc_query_resources() instead if you need to search by title, ID, or date. "
                    "limit: 1-200 (default 50). page: 0-based. "
                    "category: optional filter (e.g., 'Regression'). "
                    "project_area: project name string (defaults to ETM_PROJECT_AREA env var)."
                ),
            )(self.tools_manager.list_test_cases)

            self.mcp.tool(
                name="create_test_case",
                description=(
                    "Create a new test case. All these are mandatory: title, description, weight (priority string), "
                    "regression_test (Regression Test category value), test_level (Test Level category value), "
                    "subsystem_function (Subsystem/Function category value). "
                    "Category values must match existing values in the ETM project. "
                    "Optionally link a test_script_id (numeric webId)."
                ),
            )(self.tools_manager.create_test_case)

            self.mcp.tool(
                name="update_test_case",
                description=(
                    "Update a test case's title and/or description. "
                    "test_case_id must be a numeric webId (e.g., '3435411'), NOT a slug identifier. "
                    "Only pass the fields you want to change. "
                    "To update categories, use update_test_case_category instead. "
                    "To update custom attributes, use update_test_case_custom_attribute instead."
                ),
            )(self.tools_manager.update_test_case)

            self.mcp.tool(
                name="delete_test_case",
                description=(
                    "Permanently delete a test case. DESTRUCTIVE — cannot be undone. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.delete_test_case)

            self.mcp.tool(
                name="duplicate_test_case",
                description=(
                    "Duplicate a test case using ETM's native copy service (ICopyJobRestService). "
                    "Mirrors the 'Duplicate' button in the ETM UI. Creates an identical copy "
                    "prefixed with 'Copy of'. Returns the new test case webId and ETM link. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.duplicate_test_case)

            self.mcp.tool(
                name="get_test_case_details",
                description=(
                    "Get FULL parsed details of a test case by numeric webId. "
                    "PREFERRED tool for test case details — returns structured JSON with title, description, "
                    "preconditions, postconditions, test design, requirement links, categories, custom attributes, "
                    "test scripts, attachments, and execution record count. "
                    "Use this instead of get_resource for testcase type. "
                    "test_case_id must be a numeric webId (e.g., '3435411'), NOT a slug identifier."
                ),
            )(self.tools_manager.get_test_case_details)

            self.mcp.tool(
                name="update_test_case_category",
                description=(
                    "Modify category values on a test case. "
                    "action='add' (default): append a value to a multi-select category. "
                    "action='remove': remove a specific value. "
                    "action='replace': swap old_value with value (requires old_value param). "
                    "action='set': clear ALL values for the term, assign exactly one (single-select). "
                    "term: category name (e.g., 'Variant', 'Test Level'). "
                    "value: the new value. test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.update_test_case_category)

            self.mcp.tool(
                name="get_test_case_categories",
                description=(
                    "Read all category assignments (term/value pairs) on a test case. "
                    "Returns grouped categories indicating single-select vs multi-select. "
                    "Use before update_test_case_category to see current values. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.get_test_case_categories)

            self.mcp.tool(
                name="get_test_case_custom_attributes",
                description=(
                    "Get all custom attributes of a test case as a JSON list (name/value pairs). "
                    "Custom attributes are project-specific fields (e.g., 'verifiesRequirement'). "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.get_test_case_custom_attributes)

            self.mcp.tool(
                name="update_test_case_custom_attribute",
                description=(
                    "Update a single custom attribute on a test case. "
                    "attribute_name: exact custom attribute name. value: the new value. "
                    "append=False replaces the existing value; append=True appends to it. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.update_test_case_custom_attribute)

            self.mcp.tool(
                name="get_architecture_element_links",
                description=(
                    "Get architecture element links from a test case. "
                    "Returns all architecture element hrefs linked to the test case. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.get_architecture_element_links)

            self.mcp.tool(
                name="update_architecture_element_links",
                description=(
                    "Add, remove, or set architecture element links on a test case. "
                    "action: 'add' (append new links), 'remove' (delete matching links), "
                    "or 'set' (replace all links with provided list). "
                    "hrefs: list of architecture element URLs. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.update_architecture_element_links)

            self.mcp.tool(
                name="fix_test_case_xml",
                description=(
                    "Detect and repair XML corruption in a test case caused by ElementTree re-serialization "
                    "(broken rich-text sections like testCaseDesign or Review Criteria). "
                    "Use dry_run=True to preview changes without applying them. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.fix_test_case_xml)

            # -- Test suite tools (TestSuiteTools) --
            self.mcp.tool(
                name="create_test_suite",
                description=(
                    "Create a new test suite. Requires title and description. "
                    "A test suite groups related test cases. "
                    "After creation, use add_test_cases_to_suite() to add test cases, "
                    "and link_test_suite_to_plan() to associate it with a test plan."
                ),
            )(self.tools_manager.create_test_suite)

            self.mcp.tool(
                name="update_test_suite",
                description=(
                    "Update a test suite's title and/or description. "
                    "test_suite_id must be a numeric webId (e.g., '7423'), NOT a slug identifier."
                ),
            )(self.tools_manager.update_test_suite)

            self.mcp.tool(
                name="delete_test_suite",
                description=(
                    "Permanently delete a test suite. DESTRUCTIVE — cannot be undone. "
                    "test_suite_id must be a numeric webId."
                ),
            )(self.tools_manager.delete_test_suite)

            # -- Execution tools (ExecutionTools) --
            self.mcp.tool(
                name="get_attachment",
                description=(
                    "Get metadata about a specific attachment by numeric ID. "
                    "Returns attachment details (filename, size, content type). "
                    "attachment_id must be numeric."
                ),
            )(self.tools_manager.get_attachment)

            self.mcp.tool(
                name="get_test_plan_template",
                description=(
                    "Get a specific test plan template by exact name string. "
                    "template_name must match exactly (e.g., 'Default Test Plan Template')."
                ),
            )(self.tools_manager.get_test_plan_template)

            self.mcp.tool(
                name="list_execution_results",
                description=(
                    "List execution results (test run outcomes). "
                    "Optional filters: test_plan_id (numeric webId) and/or state (e.g., 'passed', 'failed'). "
                    "limit: 1-200 (default 50). Returns parsed JSON with count, page_size, entries, "
                    "and optional has_more. "
                    "For a single result's details, use get_execution_result(). "
                    "For all results of a specific plan, use get_execution_results_by_test_plan()."
                ),
            )(self.tools_manager.list_execution_results)

            self.mcp.tool(
                name="get_execution_result",
                description=(
                    "Get full details of a SINGLE execution result by numeric webId. "
                    "An execution result is the outcome of running a test (passed/failed/blocked/etc). "
                    "NOT for listing results — use list_execution_results() for that. "
                    "NOT for execution records (TCER) — use get_test_execution_record() for that."
                ),
            )(self.tools_manager.get_execution_result)

            self.mcp.tool(
                name="create_execution_record",
                description=(
                    "Record a test execution: creates both a Test Case Execution Record (TCER) and an "
                    "Execution Result in a single two-step operation. "
                    "test_case_id: numeric webId of the test case. "
                    "result: 'passed', 'failed', 'incomplete', or 'blocked'. "
                    "Optionally associate with test_plan_id, executed_by (contributor URI), and comments."
                ),
            )(self.tools_manager.create_execution_record)

            self.mcp.tool(
                name="update_execution_result",
                description=(
                    "Update an existing execution result. execution_result_id must be a numeric webId. "
                    "Updatable fields: state (passed/failed/incomplete/blocked/notrun/deferred/perm_failed/"
                    "inconclusive/partially_blocked/error), comments, owner, weight, machine, "
                    "starttime (ISO 8601), endtime (ISO 8601), locked (boolean). "
                    "Only pass the fields you want to change."
                ),
            )(self.tools_manager.update_execution_result)

            self.mcp.tool(
                name="get_requirement_custom_attributes",
                description=(
                    "Get requirement-related custom attributes from a test case's Summary section. "
                    "Reads attributes whose names contain 'verifies' or 'requirement' "
                    "(e.g., verifiesCodebeamerRequirement, verifiesSphinxNeedsRequirement). "
                    "Values are typically semicolon-separated URIs. test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.get_requirement_custom_attributes)

            self.mcp.tool(
                name="get_requirement_links",
                description=(
                    "Get OSLC requirement links (validates/verifies relationships) from a test case. "
                    "Returns the links from the Requirement Links section. "
                    "For custom attributes containing requirement URIs, use get_requirement_custom_attributes instead. "
                    "test_case_id must be a numeric webId."
                ),
            )(self.tools_manager.get_requirement_links)

            # -- Linking tools (LinkingTools) --
            self.mcp.tool(
                name="add_test_cases_to_suite",
                description=(
                    "Add one or more test cases to an existing test suite. "
                    "test_suite_id: numeric webId of the suite. "
                    "test_case_ids: list of numeric webIds (e.g., ['3435411', '3435412']). "
                    "Preserves existing test cases in the suite."
                ),
            )(self.tools_manager.add_test_cases_to_suite)

            self.mcp.tool(
                name="link_testcase_to_testplan",
                description=(
                    "Link a single test case directly to a test plan (not through a suite). "
                    "test_plan_id and test_case_id must both be numeric webIds. "
                    "To add through a suite instead, use add_test_cases_to_suite() + link_test_suite_to_plan()."
                ),
            )(self.tools_manager.link_testcase_to_testplan)

            self.mcp.tool(
                name="link_test_suite_to_plan",
                description=(
                    "Link an existing test suite to a test plan. "
                    "test_suite_id and test_plan_id must both be numeric webIds. "
                    "The suite and its test cases become part of the plan's hierarchy."
                ),
            )(self.tools_manager.link_test_suite_to_plan)

            self.mcp.tool(
                name="get_test_cases_by_use_case",
                description=(
                    "Find test cases related to a use case. Searches by: "
                    "(1) category matching the use_case_name, "
                    "(2) title containing the use_case_name, "
                    "(3) description containing the use_case_name. "
                    "use_case_name: the name or identifier to search for."
                ),
            )(self.tools_manager.get_test_cases_by_use_case)

            self.mcp.tool(
                name="get_failed_executions_without_defects",
                description=(
                    "Find failed test executions that have NO defects linked to them. "
                    "Useful for identifying untriaged failures. "
                    "Returns a list of execution results with state=failed but no defect links. "
                    "Use link_defect_to_execution_result() to link defects to them."
                ),
            )(self.tools_manager.get_failed_executions_without_defects)

            self.mcp.tool(
                name="get_execution_defects",
                description=(
                    "Get all defects (bug tickets) linked to a specific execution result. "
                    "execution_result_id must be a numeric webId. "
                    "Returns defect URIs and details."
                ),
            )(self.tools_manager.get_execution_defects)

            self.mcp.tool(
                name="link_defect_to_execution_result",
                description=(
                    "Link a defect (e.g., JIRA ticket URL) to a failed test execution result. "
                    "execution_result_id: numeric webId. "
                    "defect_url: full URL of the defect (e.g., JIRA issue URL)."
                ),
            )(self.tools_manager.link_defect_to_execution_result)

            # -- Traceability tools (TraceabilityTools) --
            self.mcp.tool(
                name="get_test_plan_tree",
                description=(
                    "Get the complete hierarchy of a test plan: child plans, test suites (with their test cases "
                    "and scripts), and directly linked test cases. Returns a JSON tree with statistics. "
                    "test_plan_id must be a numeric webId. "
                    "For pass/fail statistics, use get_test_plan_statistics() instead."
                ),
            )(self.tools_manager.get_test_plan_tree)

            self.mcp.tool(
                name="get_execution_timeline",
                description=(
                    "Get daily execution result trends for a test plan over a date range. "
                    "Returns a day-by-day breakdown of passed/failed/blocked counts. "
                    "test_plan_id: numeric webId. days_back: 1-365 (default 30). "
                    "For aggregate stats (not daily), use get_test_plan_statistics(mode='statistics')."
                ),
            )(self.tools_manager.get_execution_timeline)

            self.mcp.tool(
                name="get_requirement_to_test_mapping",
                description=(
                    "Build a traceability matrix mapping requirements to their test cases. "
                    "Returns which requirements are covered by which test cases. "
                    "For finding test cases without ANY requirements, use find_orphaned_test_cases()."
                ),
            )(self.tools_manager.get_requirement_to_test_mapping)

            self.mcp.tool(
                name="find_orphaned_test_cases",
                description=(
                    "Find test cases that are NOT linked to any requirement or test plan. "
                    "Useful for identifying gaps in test coverage and maintenance. "
                    "Returns a list of unlinked test cases."
                ),
            )(self.tools_manager.find_orphaned_test_cases)

            self.mcp.tool(
                name="get_execution_results_by_test_plan",
                description=(
                    "Get ALL execution results for a specific test plan. "
                    "test_plan_id must be a numeric webId. Returns complete execution data. "
                    "For a filtered/paginated view, use list_execution_results(test_plan_id=...) instead. "
                    "For pass/fail statistics, use get_test_plan_statistics()."
                ),
            )(self.tools_manager.get_execution_results_by_test_plan)

            # -- Bulk tools (BulkTools) --
            self.mcp.tool(
                name="bulk_create_test_cases",
                description=(
                    "Create multiple test cases in a single batch operation. "
                    "test_cases_data: list of dicts, each requiring at minimum 'title' key, "
                    "optionally 'description'. Returns success/failure counts and per-item results. "
                    "For creating a single test case with full categories, use create_test_case() instead."
                ),
            )(self.tools_manager.bulk_create_test_cases)

            self.mcp.tool(
                name="bulk_execute_tests",
                description=(
                    "Execute multiple tests in a single batch operation. "
                    "Creates TCER + Execution Result for each test case. "
                    "For executing a single test, use create_execution_record() instead."
                ),
            )(self.tools_manager.bulk_execute_tests)

            # -- Misc tools (MiscTools) --
            self.mcp.tool(
                name="list_test_scripts",
                description=(
                    "List test scripts (manual or automated step definitions). "
                    "Supports pagination via page, page_size, and limit (default 50). "
                    "Returns parsed JSON containing the list results and pagination metadata. "
                    "A test script defines the steps to execute a test case."
                ),
            )(self.tools_manager.list_test_scripts)

            self.mcp.tool(
                name="get_test_script",
                description=(
                    "Get full details of a specific test script by numeric ID. "
                    "test_script_id must be numeric. Returns the script's steps, type, and metadata."
                ),
            )(self.tools_manager.get_test_script)

            self.mcp.tool(
                name="create_test_script",
                description=(
                    "Create a new manual test script. Requires title and description. "
                    "Optionally provide steps as plain text. "
                    "After creation, link it to a test case via create_test_case(test_script_id=...)."
                ),
            )(self.tools_manager.create_test_script)

            self.mcp.tool(
                name="list_build_records",
                description=(
                    "List build records (software build metadata tracked in ETM). "
                    "limit: max results (default 50). Returns parsed JSON containing the list results "
                    "and pagination metadata."
                ),
            )(self.tools_manager.list_build_records)

            self.mcp.tool(
                name="get_build_record",
                description=("Get details of a specific build record by numeric ID. build_id must be numeric."),
            )(self.tools_manager.get_build_record)

            self.mcp.tool(
                name="list_test_execution_records",
                description=(
                    "List Test Case Execution Records (TCERs). A TCER links a test case to its execution context. "
                    "NOT execution results (pass/fail outcomes) — use list_execution_results() for those. "
                    "limit: max results (default 50). Returns parsed JSON containing the list results "
                    "and pagination metadata."
                ),
            )(self.tools_manager.list_test_execution_records)

            self.mcp.tool(
                name="get_test_execution_record",
                description=(
                    "Get details of a specific Test Case Execution Record (TCER) by numeric ID. "
                    "A TCER links a test case to its execution context. "
                    "NOT an execution result (pass/fail) — use get_execution_result() for that. "
                    "test_record_id must be numeric."
                ),
            )(self.tools_manager.get_test_execution_record)

            self.logger.info("All ETM MCP tools registered successfully")
        except Exception as e:
            self.logger.exception(f"Failed to register tools: {e}")
            raise

    def _setup_signal_handlers(self) -> None:
        def signal_handler(signum: int, frame: object) -> None:
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            sys.exit(0)

        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal_handler)

    def run(self, transport: str = "stdio", host: str = "", port: int = 0) -> None:
        try:
            self.logger.info(f"Starting ETM MCP Server with transport: {transport}")
            if transport == "stdio":
                self.mcp.run(transport="stdio")
            else:
                self.mcp.run(transport=transport, host=host, port=port)
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.exception(f"Fatal error: {e}")
            raise


def main() -> None:
    """Main entry point for the ETM MCP server."""
    transport, host, port = get_mcp_init_vars()
    runner = MCPServerRunner(transport=transport)
    runner.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
