# ETM MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that provides seamless integration with IBM Engineering Test Management (ETM).

## Overview

The ETM MCP Server provides comprehensive integration with IBM's Engineering Test Management system (RB-Tracker). It exposes a rich set of tools for managing test plans, test cases, test suites, execution results, and defect linking directly inside MCP-enabled clients (e.g. VS Code Copilot Chat) while keeping credentials secure via environment variables.

The server is built with the `FastMCP` framework and uses the ETM REST API.

### Project Structure

```text
mcp/etm/
├── etmmcpserver.py          # Thin entry point (MCPServerRunner)
├── core/
│   ├── config.py            # Constants, namespaces, env vars, logging setup
│   └── custom_exceptions.py # ETM-specific exception hierarchy
├── services/
│   ├── auth.py              # Authentication, persistent HTTP session
│   ├── etm_client.py        # HTTP helpers, URL builders, generic CRUD
│   ├── oslc.py              # OSLC service provider discovery and queries
│   └── xml_helpers.py       # XML create/update/parse, corruption fix
├── prompts/
│   └── prompts.py           # MCP prompts (guided LLM workflows)
├── tools/
│   ├── connection_tools.py  # Connection testing, project areas, OSLC queries
│   ├── testplan_tools.py    # Test plan CRUD + statistics
│   ├── testcase_tools.py    # Test case CRUD, categories, custom attributes
│   ├── testsuite_tools.py   # Test suite CRUD
│   ├── execution_tools.py   # Execution results, records, links
│   ├── linking_tools.py     # Linking test cases/suites/defects
│   ├── traceability_tools.py# Plan trees, timelines, requirement mapping
│   ├── bulk_tools.py        # Batch create/execute operations
│   └── misc_tools.py        # Scripts and build records
├── tests/
├── Dockerfile
├── pyproject.toml
└── mcp.json
```

### Limitations

- Depending on the LLM models, accuracy might differ
- Complex test script steps with rich formatting may need special handling
- Execution records creation requires pre-requisites to be met

## Getting Started

### Prerequisites

- Github Copilot Subscription ([GH-Copilot Access](https://docs.boschdevcloud.com/userguide/index.html?id=GHCopilot_getstarted))
- [WSL setup](https://inside-docupedia.bosch.com/confluence/x/37HoYQ)
- Access to [PMT MCP servers](https://artifactory.boschdevcloud.com/ui/repos/tree/General/pmt-mcp-servers-docker-local) ([Get access to Artifactory](../README.md#access-to-pmt-artifactory-repository))
- Access to IBM ETM [ALM-ETM Instance - Example](https://rb-alm-13-q.de.bosch.com/qm)
- Valid ETM credentials (username and password)
- ETM Project Area name [Example](CC-DA ESM Sandbox)

### MCP Client Integration

The easiest way to integrate the MCP server with your VSCode GitHub Copilot is by adding a configuration file './vscode/mcp.json'. Use this [`mcp.json`](mcp.json) as a reference and replace all placeholders.

Start the Docker version MCP server after adding './vscode/mcp.json'. It is ready to use now.

Check out the [`../README.md`](../README.md) to find out more about [`Running MCP Servers using uv/python`](../README.md#running-mcp-servers-for-development)

### Features

The server provides 55 MCP tools and 2 guided prompts for comprehensive ETM management:

- **Connection & OSLC** (`connection_tools`):
  - `test_project_connection` - Test connection to a specific project area
  - `list_project_areas` - List all available project areas
  - `oslc_query_resources` - Query resources via OSLC QM with server-side filtering
  - `get_resource` - Get detailed info about any ETM resource by type and ID

- **Test Plan Management** (`testplan_tools`):
  - `create_test_plan` - Create a new test plan with release and test level
  - `update_test_plan` - Update test plan details
  - `delete_test_plan` - Delete a test plan
  - `get_test_plan_statistics` - Get execution statistics (pass rate, timeline, raw)

- **Test Case Management** (`testcase_tools`):
  - `list_test_cases` - List test cases with pagination and category filter
  - `create_test_case` - Create a new test case with categories
  - `update_test_case` - Update test case details
  - `delete_test_case` - Delete a test case
  - `duplicate_test_case` - Duplicate a test case (mirrors the ETM UI 'Duplicate' button)
  - `get_test_case_details` - Get comprehensive test case data
  - `get_test_case_categories` - Read all category assignments for a test case
  - `update_test_case_category` - Add, remove, replace, or set a category value
  - `get_test_case_custom_attributes` - Get all custom attributes of a test case
  - `update_test_case_custom_attribute` - Update a custom attribute value
  - `get_architecture_element_links` - Get architecture element links from a test case
  - `update_architecture_element_links` - Add, remove, or set architecture element links on a test case
  - `fix_test_case_xml` - Detect and repair XML corruption from ElementTree

- **Test Suite Management** (`testsuite_tools`):
  - `create_test_suite` - Create a new test suite
  - `update_test_suite` - Update test suite details
  - `delete_test_suite` - Delete a test suite

- **Execution & Results** (`execution_tools`):
  - `list_execution_results` - List execution results with filtering
  - `get_execution_result` - Get detailed execution result info
  - `create_execution_record` - Create test execution record (TCER + result)
  - `update_execution_result` - Update execution status, comments, etc.
  - `get_requirement_custom_attributes` - Read requirement-related custom attributes
  - `get_requirement_links` - Read OSLC requirement back-links
  - `get_attachment` - Get attachment details
  - `get_test_plan_template` - Get a test plan template

- **Linking Operations** (`linking_tools`):
  - `add_test_cases_to_suite` - Add test cases to a suite
  - `link_testcase_to_testplan` - Link a test case to a test plan
  - `link_test_suite_to_plan` - Link a test suite to a test plan
  - `get_test_cases_by_use_case` - Find test cases by use case name
  - `get_failed_executions_without_defects` - Find failed tests without defect links
  - `get_execution_defects` - Get defects linked to an execution result
  - `link_defect_to_execution_result` - Link a defect to an execution result

- **Traceability & Analysis** (`traceability_tools`):
  - `get_test_plan_tree` - Get complete plan hierarchy (suites → cases → scripts)
  - `get_execution_timeline` - Get execution trend over time
  - `get_requirement_to_test_mapping` - Get requirements → test cases traceability
  - `find_orphaned_test_cases` - Find test cases not linked to requirements or plans
  - `get_execution_results_by_test_plan` - Get all executions for a test plan

- **Bulk Operations** (`bulk_tools`):
  - `bulk_create_test_cases` - Create multiple test cases in batch
  - `bulk_execute_tests` - Execute multiple tests in batch

- **Additional Resources** (`misc_tools`):
  - `list_test_scripts` / `get_test_script` / `create_test_script` - Test script management
  - `list_build_records` / `get_build_record` - Build record access
  - `list_test_execution_records` / `get_test_execution_record` - TCER access

- **Prompts** (guided LLM workflows):
  - `get_test_case_details_workflow` - Step-by-step workflow for fetching a test case with optional CM stream discovery
  - `oslc_query_guide` - Quick-reference guide for constructing `oslc_query_resources` calls

### Configuration

| Variable | Description | Example |
| ---------- | ----------- | ------- |
| `ETM_BASE_URL` | Base URL for ETM instance | `https://rb-alm-13-q.de.bosch.com/qm` |
| `ETM_USERNAME` | Username for ETM authentication | `soz1kor` |
| `ETM_PASSWORD` | Password for ETM authentication | `xxxxx` |
| `ETM_PROJECT_AREA` | Default project area to work with | `CC-DA ESM Sandbox` |
| `ETM_VERIFY_SSL` | Enable/disable SSL verification | `true` (default) |
| `CERTIFICATE_PATH` | Path to custom SSL certificate file (optional) | `""` (default, uses system certs) |
| `TRANSPORT` | MCP transport protocol (optional) | `stdio` (default), `http`, `sse` |
| `HOST` | Server host address for non-stdio transport (optional) | `localhost` (default) |
| `HOST_PORT` | Server port for non-stdio transport (optional) | `8000` (default) |

**Note:** When using the provided `mcp.json` configuration, you'll be prompted for credentials and configuration at runtime.

### Usage Examples

Once connected to an MCP-compatible client, you can interact with ETM using natural language. Try these examples in your VSCode GitHub Copilot chat:

- "List the test plans based on the latest release in my project"
- "Create a new test case titled 'Login validation'"
- "Show me all failed test executions for test plan 105520"
- "Link the test cases `<testcaseID>` to test plan `<testplanID>`"
- "Show me test plan 105520 with all its test suites and cases"
- "Add test cases 3435411, 3435412, 3435413 to test suite 7423"

The AI assistant will translate these natural language requests into actual API requests and execute them in ETM.

### Troubleshooting

#### Connection Issues

- **"Failed to connect to ETM"**: Verify `ETM_BASE_URL`, `ETM_USERNAME`, and `ETM_PASSWORD` are correct
- **Authentication failures**: Check if credentials are valid and not expired
- **Permission errors**: Ensure user has necessary project and execution permissions

#### Common Errors

- **"Resource not found"**: Verify resource ID format - use numeric webId for GET/UPDATE operations
- **"Project not found"**: Check project area name - use `list_project_areas` to see available projects
- **Network timeouts**: Check proxy settings if running in corporate environment
- **"Invalid URL"**: Ensure `ETM_BASE_URL` includes the protocol (https://) and correct hostname
- **"Permission denied"**: User may not have write permissions - check user roles in ETM

#### Resource ID Issues

- **"Cannot update/delete resource"**: Make sure you're using the numeric webId, not the slug__ identifier
- **"Resource created but cannot be retrieved"**: After creation, list resources to get the numeric webId
- **How to get webId**: Use list operations (e.g., `list_test_cases`) to see both slug__ and webId for resources

## Further Information

- [IBM Engineering Test Management Documentation](https://www.ibm.com/docs/en/engineering-test-management)
- [ETM REST API Guide](https://jazz.net/wiki/bin/view/Main/RqmApi)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
