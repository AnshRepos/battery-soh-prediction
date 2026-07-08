# ETM MCP Server Release Notes

This file describes the changes introduced with each version of ETM MCP Server.

## 0.5.0

- Added `get_architecture_element_links` and `update_architecture_element_links` tools for managing architecture element links on test cases
- Added `precondition` and `postcondition` parameters to `update_test_case`

## 0.4.0

- Added `duplicate_test_case` tool
- Fixed `link_defect` to use two-step OSLC pattern with JIRA PAT fallback
- Fixed `get_defects` to scan additional defect element variants with OSLC fallback
- Fixed XML safety using `fix_xml_raw` on all parse/serialise calls

## 0.3.3

- Updated dependencies to address security vulnerabilities

## 0.3.2

- Updated base Docker image

## 0.3.1

- Added `prompts/` module with two MCP prompts for guided LLM workflows:
  - `get_test_case_details_workflow` — step-by-step workflow for fetching a test case with optional CM stream discovery.
  - `oslc_query_guide` — quick-reference guide for constructing `oslc_query_resources` calls (ID lookups, title search, syntax rules, common pitfalls).
- Added `Annotated` + `pydantic.Field` parameter annotations and updated tool descriptions across all tool modules so parameter descriptions are surfaced directly in the LLM's tool schema.

## 0.3.0

- Refactored monolithic `etmmcpserver.py` into modular `core/`, `services/`, `tools/` packages.
- 5 new tools added — `get_resource`, `get_test_case_details`, `oslc_query_resources`, `list_project_components`, `list_cm_configurations` and removed redundant tools with overlapping functionalities
- Added `configuration_context` parameter to all MCP tools for handling the CM enabled projects.
- Introduced `ETMToolsManager` class with nine child classes (`ConnectionTools`, `TestPlanTools`, `TestCaseTools`, `TestSuiteTools`, `ExecutionTools`, `LinkingTools`, `TraceabilityTools`, `BulkTools`, `MiscTools`).
- Added thin entry point with `MCPServerRunner` class, signal handling, and structured logging.

## 0.2.0

- Added MCP tools for reading and updating test case categories (`get_test_case_categories`, `update_test_case_category`).
- Added MCP tools for reading and updating custom attributes (`get_test_case_custom_attributes`, `update_test_case_custom_attribute`, `get_requirement_custom_attributes`).
- Added MCP tool for reading OSLC requirement back-links (`get_requirement_links`).
- Added utility tool to detect and repair ElementTree re-serialization corruption in test case XML (`fix_test_case_xml`).
- Replaced ElementTree-based XML update logic with string/regex approach to prevent namespace corruption of rich HTML sections.
- Added persistent session, pagination support, and weight-field fix for update operations.

## 0.1.0

- Added MCP server transport type as a user input.
- Fixed issues with `create_execution_record` MCP tool.
- Enhanced docstrings.

## 0.0.0

- Initial beta release.
