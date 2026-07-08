"""
ETM MCP Prompts

$ File_Name                 : prompts.py
$ Description               : Prompt registration for ETM MCP tools
"""

from typing import Literal

from fastmcp import FastMCP

# Valid OSLC resource types exposed as a reusable Literal type alias
OslcResourceType = Literal[
    "testcase",
    "testplan",
    "testsuite",
    "testscript",
    "executionresult",
    "executionworkitem",
]


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts for ETM MCP tools."""

    @mcp.prompt
    def get_test_case_details_workflow(
        test_case_id: str,
        project_name: str,
        component_name: str = "",
    ) -> str:
        """Fetch full details of an ETM test case using the correct discovery workflow.

        Workflow when component_name is provided (CM-enabled project):
        1. list_project_areas          -> get project_area_uri for project_name
        2. list_project_components     -> find component by exact title match with component_name
        3. list_cm_configurations      -> pick the mutable stream (type=stream) for that component
        4. get_test_case_details       -> fetch with the stream's configuration_context
           Fallback on 404: retry with project-wide fetch (no configuration_context)

        Workflow when component_name is NOT provided:
        1. list_project_areas          -> get project_area_uri
        2. get_test_case_details       -> fetch project-wide (no configuration_context)
        """
        cm_section = f'in component "{component_name}"' if component_name else ""

        cm_steps = (
            f"""
**Step 2 — Find the component by exact title match**
Call `list_project_components(project_area_uri=<uri from Step 1>)` to list all components.

Find the component whose `title` matches "{component_name}" exactly
(case-insensitive comparison, strip leading/trailing whitespace).
Extract that component's `component_uri`.

Note: The component title and its stream name may have the same tokens in a different order
(e.g. component "rbx_pk_gen3_pf_sw" → stream "rbx_pk_gen3_sw_pf"). Always match on the
component `title` field, NOT the stream name.

**Step 3 — Get the stream's configuration_context**
Call `list_cm_configurations(component_uri=<uri from Step 2>)`.
From the returned list, select the entry with `"type": "stream"` and `"mutable": "true"`.
- There is typically exactly one stream per component — use it directly.
- If multiple streams exist, prefer the one whose title most closely matches "{component_name}".
- Extract its `configuration_context` URI.

**Step 4 — Fetch test case with configuration context**
Call `get_test_case_details(test_case_id="{test_case_id}", project_area="{project_name}",
configuration_context=<configuration_context URI from Step 3>)`.
- **Success**: proceed to the present-results step.
- **404 Not Found**: the test case was not found in that stream. As a fallback, call:
  `get_test_case_details(test_case_id="{test_case_id}", project_area="{project_name}")`
  without `configuration_context` (project-wide search).
- **400 Bad Request or validation error**: do NOT retry; report the error to the user.
"""
            if component_name
            else f"""
**Step 2 — No component provided — fetch project-wide**
No component name was supplied, so skip component and stream discovery entirely.
Call `get_test_case_details(test_case_id="{test_case_id}", project_area="{project_name}")`.
Omit the `configuration_context` parameter. ETM searches the project globally.
- If this returns a 404, the test case may not exist in project "{project_name}". Verify the ID.
"""
        )

        present_step = "**Step 5" if component_name else "**Step 3"

        return f"""Fetch the full details of ETM test case ID "{test_case_id}" from project \
"{project_name}" {cm_section}.

CRITICAL: Do NOT call get_test_case_details directly as the first action. Always complete \
Step 1 first, and Step 2-3 when a component name is provided.

**Step 1 — Discover project areas**
Call `list_project_areas()` to list all available ETM projects.
Find the entry whose `name` matches "{project_name}" (exact, case-insensitive) and extract
its `project_area_uri`. This URI is needed for Step 2.
{cm_steps}
{present_step} — Present results**
Display the test case in a structured, human-readable format with the following sections:
- Title, description, state, priority, creation/update dates
- Categories table (all term/value pairs)
- Precondition steps (Step | Stimulation | Classification)
- Test case design steps (Step | Stimulation | Classification)
- Postcondition steps if present
- Custom attributes
- Summary (requirement links, test scripts, attachments counts)
"""

    @mcp.prompt
    def oslc_query_guide(
        project_name: str,
        resource_type: OslcResourceType = "testcase",
        search_term: str = "",
        resource_id: str = "",
    ) -> str:
        """Guide for searching ETM resources using the oslc_query_resources tool.

        Provides the correct OSLC query syntax, property names, and workflow
        to search for test cases, test plans, test suites, execution results,
        and other ETM resources by ID, title, date, or custom criteria.
        """
        valid_types = "testcase, testplan, testsuite, testscript, executionresult, executionworkitem"

        # Build the search-specific section
        if resource_id:
            search_section = f"""
**Your query — Find by ID**
Call:
```
oslc_query_resources(
    resource_type="{resource_type}",
    project_area="{project_name}",
    where='oslc:shortId="{resource_id}"',
    select="*"
)
```
IMPORTANT: Use `oslc:shortId` for numeric ID lookups, NOT `dcterms:identifier`.
"""
        elif search_term:
            search_section = f"""
**Your query — Search by title**
Call:
```
oslc_query_resources(
    resource_type="{resource_type}",
    project_area="{project_name}",
    where='dcterms:title="{search_term}"',
    select="dcterms:title,oslc:shortId,dcterms:modified"
)
```
Note: This is an exact match. ETM OSLC does not support wildcards or substring matching \
in `oslc.where`. If no results are found, try a broader approach or omit the `where` clause \
and increase the `limit`.
"""
        else:
            search_section = f"""
**Your query — Browse resources**
Call:
```
oslc_query_resources(
    resource_type="{resource_type}",
    project_area="{project_name}",
    select="dcterms:title,oslc:shortId,dcterms:modified",
    limit=50
)
```
"""

        return f"""Search for ETM {resource_type} resources in project "{project_name}" \
using the `oslc_query_resources` tool.

---

## OSLC Query Reference

### Supported resource types
`{valid_types}`

### OSLC where clause syntax

| Goal | where clause | Notes |
|------|-------------|-------|
| Find by numeric ID | `oslc:shortId="28931"` | Use `oslc:shortId`, NOT `dcterms:identifier` |
| Find by exact title | `dcterms:title="My Test Plan"` | String values MUST be in double quotes |
| Find by modifier | `dcterms:modified>="2025-01-01T00:00:00Z"` | ISO 8601 format |
| Combine conditions | `dcterms:title="X" and dcterms:modified>="2025-01-01T00:00:00Z"` | Use `and` to combine |

### OSLC select syntax
Comma-separated list of properties to include in results:
- `dcterms:title` — resource title
- `dcterms:identifier` — internal identifier
- `oslc:shortId` — numeric webId (the ID you need for other tools)
- `dcterms:modified` — last modification date
- `dcterms:created` — creation date
- `dcterms:creator` — creator URI
- `dcterms:description` — resource description
- `*` — all available properties

### Common pitfalls
1. **Wrong ID property**: Use `oslc:shortId` for numeric ID lookups, never `dcterms:identifier`
2. **Unquoted strings**: String values in `where` MUST be wrapped in double quotes
3. **No wildcards**: OSLC `where` does not support `*` or `%` wildcards for substring matching
4. **CM-enabled projects**: Pass `configuration_context` from `list_cm_configurations()` or results may be empty

---

{search_section}

## After finding results

- **Test case found**: Call `get_test_case_details(test_case_id=<shortId>)` for full parsed details
- **Test plan found**: Call `get_test_plan_tree(test_plan_id=<shortId>)` for hierarchy, \
or `get_test_plan_statistics(test_plan_id=<shortId>)` for execution stats
- **Any resource**: Call `get_resource(resource_type="...", resource_id=<shortId>)` for raw details
"""
