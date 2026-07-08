"""ETM Execution Tools -- MCP tools for execution results, records, links, and related operations."""

import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import Annotated, Any, Optional
from urllib.parse import quote
from xml.sax.saxutils import escape

from core.config import (
    ALM_NAMESPACE,
    CONFIG_CONTEXT_DESC,
    ETM_NAMESPACE,
    ETM_PROJECT_AREA,
    EXECUTION_STATE_MAP,
    PROJECT_AREA_DESC,
)
from pydantic import Field
from services.etm_client import (
    build_resource_href,
    build_resource_url,
    extract_resource_id,
    generic_get,
    generic_update,
    handle_error,
    make_request,
    project_area_required_error,
    resolve_to_web_id,
)
from services.xml_helpers import create_xml_resource, parse_resource_to_json

logger = logging.getLogger(__name__)


# ========================================================================
# ATTACHMENTS
# ========================================================================


class ExecutionTools:
    """ETM Execution tools methods."""

    def get_attachment(
        self,
        attachment_id: Annotated[str, Field(description="Numeric attachment ID.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get detailed information about a specific attachment."""
        return generic_get("attachment", attachment_id, project_area, configuration_context=configuration_context)

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    def get_test_plan_template(
        self,
        template_name: Annotated[
            str, Field(description="Exact template name string (e.g., 'Default Test Plan Template').")
        ],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get a specific test plan template."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = f"{build_resource_url(project, 'template')}/testplan/{quote(template_name, safe='')}"
            response = make_request(endpoint, configuration_context=configuration_context)
            return parse_resource_to_json(response.text)
        except Exception as e:
            return handle_error("get_test_plan_template", e)

    # ========================================================================
    # EXECUTION RESULTS
    # ========================================================================

    def list_execution_results(
        self,
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        limit: Annotated[int, Field(description="Maximum results (1-200).", ge=1, le=200)] = 50,
        test_plan_id: Annotated[
            Optional[str], Field(description="Optional: filter by test plan numeric webId.")
        ] = None,
        state: Annotated[
            Optional[str],
            Field(description="Optional: filter by state (e.g., 'passed', 'failed', 'blocked', 'incomplete')."),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """List execution results with optional filtering."""
        try:
            if not (1 <= limit <= 200):
                return json.dumps({"error": "limit must be between 1 and 200"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "executionresult")
            params = {
                "abbreviate": "true",
                "pageSize": str(limit),
            }

            if test_plan_id or state:
                conditions = []
                if test_plan_id:
                    conditions.append(f"testplan[@href='{build_resource_href(project, 'testplan', test_plan_id)}']")
                if state:
                    conditions.append(f"state='{state}'")
                params["fields"] = f"executionresult[{' and '.join(conditions)}]"

            response = make_request(endpoint, params=params, timeout=180, configuration_context=configuration_context)
            from services.xml_helpers import extract_entries_from_feed

            entries, next_url = extract_entries_from_feed(response.text, "executionresult")
            result: dict[str, Any] = {
                "count": len(entries),
                "page_size": limit,
                "entries": entries,
            }
            if next_url:
                result["has_more"] = True
            return json.dumps(result, indent=2)
        except Exception as e:
            return handle_error("list_execution_results", e)

    def get_execution_result(
        self,
        result_id: Annotated[str, Field(description="Numeric execution result ID.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get detailed information about a specific execution result."""
        return generic_get("executionresult", result_id, project_area, configuration_context=configuration_context)

    def create_execution_record(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId of the test case to execute.")],
        result: Annotated[
            str,
            Field(description="Execution result status. One of: 'passed', 'failed', 'incomplete', 'blocked'."),
        ],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        test_plan_id: Annotated[
            Optional[str], Field(description="Optional: numeric webId of the test plan to associate with.")
        ] = None,
        executed_by: Annotated[
            Optional[str],
            Field(
                description="Optional: contributor URI (must be http/https URL, e.g., 'https://server/jts/users/john')."
            ),
        ] = None,
        comments: Annotated[Optional[str], Field(description="Optional: comments about the execution.")] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Create a test execution record (TCER + Execution Result)."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            logger.info(f"Step 1: Creating TCER for test case {test_case_id}")

            state = EXECUTION_STATE_MAP.get(result.lower(), EXECUTION_STATE_MAP["incomplete"])

            # Step 1: Create TCER
            tcer_extra: dict[str, str] = {"href_testcase": build_resource_href(project, "testcase", test_case_id)}
            if test_plan_id:
                tcer_extra["href_testplan"] = build_resource_href(project, "testplan", test_plan_id)

            tcer_endpoint = build_resource_url(project, "executionworkitem")
            tcer_xml = create_xml_resource("executionworkitem", "Execution Record", "", categories=None, **tcer_extra)

            tcer_response = make_request(
                tcer_endpoint,
                method="POST",
                data=tcer_xml.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                configuration_context=configuration_context,
            )

            tcer_id = extract_resource_id(tcer_response, "executionworkitem")
            if not tcer_id:
                return json.dumps({"error": "Failed to extract TCER ID"})

            tcer_id = resolve_to_web_id(tcer_response, "executionworkitem", tcer_id, configuration_context)
            logger.info(f"TCER created: {tcer_id}")
            time.sleep(1)

            logger.info(f"Step 2: Creating execution result for TCER {tcer_id}")

            # Step 2: Create Execution Result
            tcer_href = build_resource_href(project, "executionworkitem", tcer_id)
            testcase_href = build_resource_href(project, "testcase", test_case_id)

            result_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <qm:executionresult xmlns:qm="{ETM_NAMESPACE}" xmlns:alm="{ALM_NAMESPACE}" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Execution Result</dc:title>
    <dc:description>{escape(comments or "")}</dc:description>
    <alm:state>{state}</alm:state>
    <qm:testcase href="{testcase_href}"/>
    <qm:executionworkitem href="{tcer_href}"/>"""

            if test_plan_id:
                result_xml += f'\n    <qm:testplan href="{build_resource_href(project, "testplan", test_plan_id)}"/>'

            if executed_by:
                if not executed_by.startswith(("http://", "https://")):
                    return json.dumps(
                        {
                            "error": "executed_by must be a contributor URI (http/https URL)",
                            "field": "executed_by",
                        }
                    )
                _quote_map = {'"': "&quot;", "'": "&apos;"}
                result_xml += f'\n    <qm:executedby href="{escape(executed_by, _quote_map)}"/>'

            result_xml += "\n</qm:executionresult>"

            result_endpoint = build_resource_url(project, "executionresult")
            result_response = make_request(
                result_endpoint,
                method="POST",
                data=result_xml.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                configuration_context=configuration_context,
            )

            result_id = extract_resource_id(result_response, "executionresult") or "unknown"
            logger.info(f"Execution result created: {result_id}")

            return json.dumps(
                {
                    "success": True,
                    "execution_result_id": result_id,
                    "execution_record_id": tcer_id,
                    "result": result,
                    "message": f"Execution record created with result: {result}",
                }
            )
        except Exception as e:
            return handle_error("create_execution_record", e)

    def update_execution_result(
        self,
        execution_result_id: Annotated[str, Field(description="Numeric webId of the execution result to update.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        state: Annotated[
            Optional[str],
            Field(
                description="New state. One of: passed, failed, incomplete, blocked, paused, inprogress, notrun, deferred, perm_failed, inconclusive, partially_blocked, error."
            ),
        ] = None,
        comments: Annotated[Optional[str], Field(description="New comments text.")] = None,
        owner: Annotated[Optional[str], Field(description="New owner username.")] = None,
        weight: Annotated[Optional[int], Field(description="Execution weight value.")] = None,
        machine: Annotated[Optional[str], Field(description="Machine name where test was executed.")] = None,
        starttime: Annotated[
            Optional[str], Field(description="Execution start time in ISO 8601 format (e.g., '2024-01-15T10:30:00Z').")
        ] = None,
        endtime: Annotated[Optional[str], Field(description="Execution end time in ISO 8601 format.")] = None,
        locked: Annotated[
            Optional[bool], Field(description="Whether to lock (true) or unlock (false) the execution result.")
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Update an existing execution result. Only pass the fields you want to change."""
        updates: dict[str, str] = {}
        if state:
            updates["state"] = EXECUTION_STATE_MAP.get(state.lower(), state)
        if comments:
            updates["description"] = comments
        if owner:
            updates["owner"] = owner
        if weight is not None:
            updates["weight"] = str(weight)
        if machine:
            updates["machine"] = machine
        if starttime:
            updates["starttime"] = starttime
        if endtime:
            updates["endtime"] = endtime
        if locked is not None:
            updates["locked"] = str(locked).lower()
        return generic_update(
            "executionresult",
            execution_result_id,
            project_area,
            configuration_context=configuration_context,
            **updates,
        )

    # ========================================================================
    # REQUIREMENT CUSTOM ATTRIBUTES
    # ========================================================================

    def get_requirement_custom_attributes(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3507421'), NOT a slug identifier.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get requirement-related custom attributes from the Summary section of a test case.

        [AI-developed] Reads custom attributes whose names contain 'verifies' or
        'requirement' (e.g. verifiesCodebeamerRequirement, verifiesSphinxNeedsRequirement).
        Values are typically semicolon-separated URLs or URNs and are split into a list."""
        try:
            if not test_case_id or not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)
            response = make_request(
                endpoint,
                accept_type="application/xml",
                configuration_context=configuration_context,
            )

            root = ET.fromstring(response.text)
            ns = {"ns2": ETM_NAMESPACE}

            # Filter custom attributes by name containing "verif" or "requirement"
            requirement_attrs = []
            for custom_attr in root.findall(".//ns2:customAttributes/ns2:customAttribute", ns):
                name_elem = custom_attr.find("ns2:name", ns)
                value_elem = custom_attr.find("ns2:value", ns)
                if name_elem is None or not name_elem.text:
                    continue
                attr_name = name_elem.text
                if "verif" not in attr_name.lower() and "requirement" not in attr_name.lower():
                    continue
                raw_value = value_elem.text if value_elem is not None else ""
                # Split semicolon-separated values into individual entries
                values = [v.strip() for v in raw_value.split(";") if v.strip()] if raw_value else []
                requirement_attrs.append(
                    {
                        "name": attr_name,
                        "raw_value": raw_value,
                        "values": values,
                        "count": len(values),
                    }
                )

            return json.dumps(
                {
                    "test_case_id": test_case_id,
                    "requirement_custom_attributes": requirement_attrs,
                    "total_count": sum(a["count"] for a in requirement_attrs),
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_requirement_custom_attributes", e)

    # ========================================================================
    # REQUIREMENT LINKS
    # ========================================================================

    def get_requirement_links(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3507421'), NOT a slug identifier.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get OSLC requirement links from the Requirement Links section of a test case.

        [AI-developed] Fetches the test case with ?calmlinks=true to retrieve
        OSLC back-links (DNG/DOORS, Codebeamer, etc.) stored as <ns2:requirement>
        elements. Without calmlinks=true these links are NOT present in the XML.
        Each link contains href, summary, rel (e.g. 'validates'), and isSuspected."""
        try:
            if not test_case_id or not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)
            # Key discovery: ?calmlinks=true is required to include OSLC requirement links
            response = make_request(
                endpoint,
                accept_type="application/xml",
                params={"calmlinks": "true"},
                configuration_context=configuration_context,
            )

            root = ET.fromstring(response.text)
            ns = {"ns2": ETM_NAMESPACE}

            # Parse <ns2:requirement> elements (NOT <ns2:validates> which don't exist)
            requirement_links = []
            for elem in root.findall(".//ns2:requirement", ns):
                href = elem.get("href", "")
                if not href:
                    continue
                requirement_links.append(
                    {
                        "href": href,
                        "summary": elem.get("summary", ""),
                        "rel": elem.get("rel", ""),
                        "isSuspected": elem.get("isSuspected", "false"),
                    }
                )

            return json.dumps(
                {
                    "test_case_id": test_case_id,
                    "requirement_links": requirement_links,
                    "count": len(requirement_links),
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_requirement_links", e)
