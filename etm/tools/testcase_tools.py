"""ETM Test Case Tools -- MCP tools for test case CRUD, categories, custom attributes, and XML fix."""

import asyncio
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Annotated, Any, Optional
from urllib.parse import quote, urlencode
from xml.sax.saxutils import escape

import requests
from core.config import (
    CONFIG_CONTEXT_DESC,
    ETM_BASE_URL,
    ETM_NAMESPACE,
    ETM_PROJECT_AREA,
    ETM_SERVICE_PATH,
    PROJECT_AREA_DESC,
)
from fastmcp.server.context import Context
from pydantic import Field
from services.etm_client import (
    build_category_href,
    build_resource_href,
    build_resource_url,
    extract_resource_id,
    generic_delete,
    generic_update,
    handle_error,
    invalid_id_error,
    make_request,
    project_area_required_error,
)
from services.oslc import oslc_query
from services.xml_helpers import (
    create_xml_resource,
    fix_et_corruption,
    parse_test_case_details,
    update_custom_attribute_in_xml,
)

logger = logging.getLogger(__name__)


def fetch_category_type_href(project: str, term: str) -> Optional[str]:
    """Look up the categoryType href for a given term name via the ETM API.

    Fetches the categoryType feed for the project and searches for the entry
    whose title matches *term* (case-insensitive).  Returns the self-link href
    of the matching categoryType resource, or None if not found.
    """
    try:
        encoded_project = quote(project, safe="")
        feed_url = f"{ETM_SERVICE_PATH}/{encoded_project}/categoryType"
        resp = make_request(feed_url, accept_type="application/xml")
        feed_xml = resp.text
        # Each entry looks like:
        # <entry>...<title>Variant</title>...<link rel="self" href="..."/>...</entry>
        # We parse with a lightweight regex to avoid namespace complexity.
        entry_re = re.compile(r"<entry\b[^>]*>(.*?)</entry>", re.DOTALL)
        title_re = re.compile(r"<title[^>]*>([^<]+)</title>")
        href_re = re.compile(r'<link[^>]+rel="self"[^>]+href="([^"]+)"')
        for entry_m in entry_re.finditer(feed_xml):
            entry_body = entry_m.group(1)
            title_m = title_re.search(entry_body)
            if title_m and title_m.group(1).strip().lower() == term.strip().lower():
                href_m = href_re.search(entry_body)
                if href_m:
                    return href_m.group(1)
        return None
    except requests.RequestException as e:
        logger.warning(f"Network error fetching categoryType for term '{term}': {e}")
        return None
    except Exception as e:
        logger.debug(f"Failed to resolve categoryType href for term '{term}': {e}", exc_info=True)
        return None


class TestCaseTools:
    """ETM TestCase tools methods."""

    async def list_test_cases(
        self,
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        limit: Annotated[int, Field(description="Number of test cases per page. Must be 1-200.", ge=1, le=200)] = 50,
        category: Annotated[
            Optional[str], Field(description="Optional category filter (e.g., 'Regression'). Omit for all.")
        ] = None,
        page: Annotated[int, Field(description="Page number, 0-based. Default 0 (first page).", ge=0)] = 0,
        ctx: Optional[Context] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """List test cases with pagination and optional category filter."""
        try:
            if not (1 <= limit <= 200):
                return json.dumps(
                    {
                        "error": "limit must be between 1 and 200",
                        "hint": "Pass an integer between 1 and 200 (default is 50).",
                    }
                )

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase")
            params = {
                "abbreviate": "true",
                "pageSize": str(limit),
                "page": str(page),
            }

            if category:
                params["fields"] = f"testcase[category/term='{category}']"

            if ctx:
                await ctx.report_progress(0, 1, f"Fetching test cases (page {page}, up to {limit} items)...")
                await ctx.info(f"Requesting page {page} of test cases from '{project}' (pageSize={limit})")

            task = asyncio.create_task(
                asyncio.to_thread(
                    make_request,
                    endpoint,
                    params=params,
                    timeout=120,
                    configuration_context=configuration_context,
                )
            )

            elapsed = 0
            ping_interval = 5
            while True:
                done, _ = await asyncio.wait({task}, timeout=ping_interval)
                if done:
                    break
                elapsed += ping_interval
                if ctx:
                    await ctx.info(f"Still fetching test cases... ({elapsed}s elapsed)")
                    await ctx.report_progress(0, 1, f"Waiting for ETM response ({elapsed}s)...")

            response = task.result()

            if ctx:
                await ctx.report_progress(1, 1, f"Done! Received response ({len(response.text)} bytes)")
                await ctx.info(f"Page {page}: received {len(response.text)} bytes")

            from services.xml_helpers import extract_entries_from_feed

            entries, next_url = extract_entries_from_feed(response.text, "testcase")
            result: dict[str, Any] = {
                "count": len(entries),
                "page": page,
                "page_size": limit,
                "entries": entries,
            }
            if next_url:
                result["has_more"] = True
            return json.dumps(result, indent=2)
        except Exception as e:
            return handle_error("list_test_cases", e)

    def create_test_case(
        self,
        title: Annotated[str, Field(description="Name of the test case (mandatory).")],
        description: Annotated[str, Field(description="Description of the test case.")],
        weight: Annotated[
            str, Field(description="Weight/priority of the test case (mandatory). Must match a project category value.")
        ],
        regression_test: Annotated[
            str, Field(description="Regression Test category value (mandatory). Must match a project category value.")
        ],
        test_level: Annotated[
            str, Field(description="Test Level category value (mandatory). Must match a project category value.")
        ],
        subsystem_function: Annotated[
            str,
            Field(description="Subsystem/Function category value (mandatory). Must match a project category value."),
        ],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        test_script_id: Annotated[
            Optional[str], Field(description="Numeric webId of a test script to link. Optional.")
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Create a new test case with categories."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            categories: list[dict[str, str]] = [
                {
                    "term": "Regression Test",
                    "value": regression_test,
                    "href": build_category_href(project, "Regression Test", regression_test),
                },
                {
                    "term": "Test Level",
                    "value": test_level,
                    "href": build_category_href(project, "Test Level", test_level),
                },
                {
                    "term": "Subsystem/Function",
                    "value": subsystem_function,
                    "href": build_category_href(project, "Subsystem/Function", subsystem_function),
                },
            ]

            endpoint = build_resource_url(project, "testcase")
            xml_payload = create_xml_resource(
                "testcase",
                title,
                description,
                categories=categories,
                weight=weight,
                **(
                    {"href_testscript": build_resource_href(project, "testscript", test_script_id)}
                    if test_script_id
                    else {}
                ),
            )
            logger.info(
                f"Creating testcase: '{title}' with weight='{weight}', "
                f"regression_test='{regression_test}', test_level='{test_level}', "
                f"subsystem_function='{subsystem_function}'"
            )

            response = make_request(
                endpoint,
                method="POST",
                data=xml_payload.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                configuration_context=configuration_context,
            )

            resource_id = extract_resource_id(response, "testcase")
            location = response.headers.get("Location", "")

            result: dict[str, Any] = {
                "success": True,
                "testcase_id": resource_id,
                "location": location,
                "message": (
                    f"Test case '{title}' created successfully. "
                    "Use oslc_query_resources with "
                    f"where='dcterms:title=\"{title}\"' and "
                    "select='dcterms:title,oslc:shortId' to retrieve "
                    "the numeric webId."
                ),
            }

            return json.dumps(result)
        except Exception as e:
            return handle_error("create_test_case", e)

    def update_test_case(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3435411'), NOT a slug identifier.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        title: Annotated[Optional[str], Field(description="New title. Omit to keep unchanged.")] = None,
        description: Annotated[Optional[str], Field(description="New description. Omit to keep unchanged.")] = None,
        precondition: Annotated[
            Optional[str], Field(description="New precondition text (HTML or plain text). Omit to keep unchanged.")
        ] = None,
        postcondition: Annotated[
            Optional[str], Field(description="New postcondition text (HTML or plain text). Omit to keep unchanged.")
        ] = None,
        test_case_design: Annotated[
            Optional[str], Field(description="New test case design content (HTML table or plain text). Omit to keep unchanged.")
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Update a test case's title, description, precondition, postcondition, and/or test case design.

        Supports both plain text and HTML content. HTML content (tables, lists) is automatically detected
        and preserved without escaping. Use HTML format for structured content like tables:
        
        Example HTML table format:
        <table border="1">
            <tr><th>Steps</th><th>Input Operations</th><th>Expected Result</th><th>Actual Results</th></tr>
            <tr><td>1</td><td>Call API</td><td>Success</td><td>Success</td></tr>
        </table>
        
        Example HTML list format:
        <ol>
            <li>First precondition</li>
            <li>Second precondition</li>
        </ol>

        For categories use update_test_case_category.
        For custom attributes use update_test_case_custom_attribute."""
        updates = {
            k: v
            for k, v in {
                "title": title,
                "description": description,
                "precondition": precondition,
                "postcondition": postcondition,
                "test_case_design": test_case_design,
            }.items()
            if v is not None
        }
        return generic_update(
            "testcase",
            test_case_id,
            project_area,
            configuration_context=configuration_context,
            **updates,
        )

    def delete_test_case(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId of the test case to delete.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Delete a test case. DESTRUCTIVE — cannot be undone."""
        return generic_delete("testcase", test_case_id, project_area, configuration_context=configuration_context)

    # Implements the ETM UI "Duplicate" button via ICopyJobRestService, an undocumented
    # internal REST service whose endpoint/payload were reverse-engineered from F12
    # browser captures.
    def duplicate_test_case(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId of the test case to duplicate.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Duplicate a test case using ETM's native copy service (ICopyJobRestService).

        Mirrors the "Duplicate" button in the ETM UI. Creates an identical copy of the
        test case (title, description, design, categories) prefixed with "Copy of".
        Returns the new test case webId and a direct ETM link.
        """
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            if not test_case_id:
                return json.dumps({"error": "test_case_id is required"})

            # Step 1: Resolve internal item IDs via OSLC query.
            oslc_json = oslc_query(
                resource_type="testcase",
                project_area=project,
                where=f'oslc:shortId="{test_case_id}"',
                select="dcterms:title",
                limit=1,
                configuration_context=configuration_context,
            )
            oslc_list = json.loads(oslc_json).get("testcases", [])
            if not oslc_list:
                return json.dumps({"error": f"Test case {test_case_id} not found in project '{project}'"})

            original_title = oslc_list[0].get("title", "")
            oslc_tc_url = oslc_list[0].get("url", "")

            m = re.search(
                r"oslc_qm/contexts/([^/\"?\s]+)/resources/com\.ibm\.rqm\.planning\.VersionedTestCase/([^/\"?\s&]+)",
                oslc_tc_url,
            )
            if not m:
                return json.dumps({"error": f"Could not extract item IDs from OSLC URL: {oslc_tc_url}"})
            pa_item_id = m.group(1)
            tc_item_id = m.group(2)

            qs = f"webContext.projectArea={quote(pa_item_id, safe='')}"

            # Step 2: POST copyJob
            body_data = {
                "targetItemTypeName": "VersionedTestCase",
                "targetItemTypeNamespaceURI": "com.ibm.rqm.planning",
                "targetItems": tc_item_id,
                "sourceProjectArea": pa_item_id,
                "targetProjectArea": pa_item_id,
                "deep": "false",
                "includeReferences": "true",
                "includeTCER": "false",
                "includeTCR": "false",
            }
            copy_resp = make_request(
                f"/service/com.ibm.rqm.copy.rest.ICopyJobRestService/copyJob?{qs}",
                method="POST",
                data=urlencode(body_data).encode("utf-8"),
                accept_type="text/json",
                content_type="application/x-www-form-urlencoded",
            )
            copy_data = json.loads(copy_resp.text)
            value: dict = copy_data.get("soapenv:Body", {}).get("response", {}).get("returnValue", {}).get("value", {})
            job_id = value.get("itemId", "")
            if not job_id:
                return json.dumps({"error": "Copy job did not return an itemId", "raw": str(copy_data)[:500]})

            # Step 2b: POST activeJobs to trigger execution
            try:
                make_request(
                    f"/service/com.ibm.rqm.copy.rest.ICopyJobRestService/activeJobs"
                    f"?copyJob={quote(job_id, safe='')}&{qs}",
                    method="POST",
                    data=b"",
                    accept_type="text/json",
                    content_type="application/x-www-form-urlencoded",
                )
            except requests.exceptions.HTTPError:
                pass  # ETM may return non-2xx during early job setup; poll will confirm completion

            # Step 3: Poll until job reaches a terminal state (max 30s)
            job_state = value.get("state", "")
            poll_deadline = time.monotonic() + 30.0
            while time.monotonic() < poll_deadline:
                try:
                    poll_resp = make_request(
                        f"/service/com.ibm.rqm.copy.rest.ICopyJobRestService/copyJob"
                        f"?copyJob={quote(job_id, safe='')}&{qs}",
                        method="GET",
                        accept_type="text/json",
                    )
                    poll_value = (
                        json.loads(poll_resp.text)
                        .get("soapenv:Body", {})
                        .get("response", {})
                        .get("returnValue", {})
                        .get("value", {})
                    )
                    job_state = poll_value.get("state", job_state)
                    if job_state in ("COMPLETE", "ERROR", "FAILED", "CANCELLED"):
                        break
                except Exception:
                    pass
                time.sleep(1.0)
            else:
                time.sleep(3.0)  # grace period on timeout

            # Step 4: Resolve new TC webId via OSLC (query for TCs created after original)
            new_web_id = ""
            new_title = ""
            try:
                pre_json = oslc_query(
                    resource_type="testcase",
                    project_area=project,
                    select="oslc:shortId,dcterms:title",
                    order_by="-oslc:shortId",
                    limit=5,
                    configuration_context=configuration_context,
                )
                for tc in json.loads(pre_json).get("testcases", []):
                    t = tc.get("title", "")
                    if "Copy of" in t and original_title in t:
                        new_web_id = str(tc.get("shortId", "") or tc.get("shortIdentifier", ""))
                        new_title = t
                        break
                if not new_web_id:
                    # fallback: just return the newest TC
                    tcs = json.loads(pre_json).get("testcases", [])
                    if tcs:
                        new_web_id = str(tcs[0].get("shortId", "") or tcs[0].get("shortIdentifier", ""))
                        new_title = tcs[0].get("title", "")
            except Exception as e:
                logger.warning("duplicate_test_case: could not resolve new webId: %s", e)

            # Step 5: Cleanup
            try:
                make_request(
                    f"/service/com.ibm.rqm.copy.rest.ICopyJobRestService/copyJob?copyJob={quote(job_id, safe='')}&{qs}",
                    method="DELETE",
                    accept_type="text/json",
                )
            except Exception:
                pass

            etm_link = (
                f"{ETM_BASE_URL}/web/console/{quote(project, safe='')}"
                f"#action=com.ibm.rqm.planning.home.actionDispatcher&subAction=viewTestCase&id={new_web_id}"
                if new_web_id
                else ""
            )

            return json.dumps(
                {
                    "success": True,
                    "original_test_case_id": test_case_id,
                    "original_title": original_title,
                    "new_test_case_id": new_web_id,
                    "new_title": new_title,
                    "job_state": job_state,
                    "etm_link": etm_link,
                }
            )
        except Exception as e:
            return handle_error("duplicate_test_case", e)

    def get_test_case_details(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3435411'), NOT a slug__ identifier.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(
                description=(
                    "CM stream URI for CM-enabled projects. "
                    "REQUIRED when the user mentioned a component name. "
                    "Discovery workflow (MUST be followed before calling this tool when a component is known): "
                    "1) list_project_areas() to get project_area_uri, "
                    "2) list_project_components(project_area_uri=<uri>) to find the component by title, "
                    "3) list_cm_configurations(component_uri=<uri>) to get the stream's configuration_context, "
                    "4) pass that URI here. "
                    "Omit only if the project is confirmed to not use CM."
                )
            ),
        ] = None,
    ) -> str:
        """Get full parsed details of a test case. Preferred over get_resource for test cases.

        IMPORTANT: For CM-enabled projects (any project where the user mentioned a component
        name), you MUST obtain configuration_context BEFORE calling this tool:
          list_project_areas() -> list_project_components(project_area_uri=...) ->
          list_cm_configurations(component_uri=...) -> use the stream's configuration_context.
        Calling this without configuration_context on a CM-enabled project returns 404."""
        try:
            if not test_case_id or not test_case_id.strip():
                return invalid_id_error("test_case_id", test_case_id or "")

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)
            response = make_request(
                endpoint, accept_type="application/xml", configuration_context=configuration_context
            )

            root = ET.fromstring(response.text)
            details = parse_test_case_details(root)
            details["_type"] = "testcase"
            details["_resource_id"] = test_case_id

            details["_summary"] = {
                "requirement_links_count": len(details.get("requirement_links", [])),
                "development_items_count": len(details.get("development_items", [])),
                "architecture_element_links_count": len(details.get("architecture_element_links", [])),
                "test_scripts_count": len(details.get("test_scripts", [])),
                "attachments_count": len(details.get("attachments", [])),
                "has_precondition": bool(details.get("precondition")),
                "has_postcondition": bool(details.get("postcondition")),
                "has_expected_results": bool(details.get("expected_results")),
                "has_test_case_design": bool(details.get("test_case_design")),
            }

            return json.dumps(details, indent=2)
        except Exception as e:
            return handle_error("get_test_case_details", e)

    # ----------------------------------------------------------------------------
    # AI-CHANGED (GitHub Copilot / Claude Sonnet 4.6) — 2026-03-11
    # New MCP tool to add or remove a category value from a test case without
    # using ElementTree re-serialization (which corrupts rich HTML sections).
    # Uses safe string manipulation on the raw XML, identical to _update_xml_resource.
    # ----------------------------------------------------------------------------
    # AI-CHANGED (GitHub Copilot / Claude Sonnet 4.6) — 2026-03-11
    # Extended with 'replace' and 'set' actions:
    #   replace — swap one specific value for another (single-value substitution)
    #   set     — remove ALL existing values for the term, then assign exactly one new value
    #             (single-selection semantics). Falls back to categoryType API to obtain
    #             the categoryType href when no existing value is available in the XML.
    # ----------------------------------------------------------------------------

    def update_test_case_category(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3599953'), NOT a slug identifier.")],
        term: Annotated[str, Field(description="Category term name (e.g., 'Variant', 'Test Level', 'Region').")],
        value: Annotated[str, Field(description="Category value to assign (e.g., 'HON', 'SYS_TST', 'EU').")],
        action: Annotated[str, Field(description="One of: 'add', 'remove', 'replace', 'set'. Default 'add'.")] = "add",
        old_value: Annotated[
            Optional[str], Field(description="Required when action='replace' — the value being replaced.")
        ] = None,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Add, remove, replace, or set a category value on a test case.

        AI-constructed tool (GitHub Copilot / Claude Sonnet 4.6 — 2026-03-11).

        Uses safe string manipulation (no ElementTree re-serialization) so that
        rich HTML sections (testCaseDesign, Review Criteria, etc.) are preserved.

        Supported actions
        -----------------
        add     — (default, multi-select) Append *value* to the term; existing
                  values for the same term are kept intact.
        remove  — Remove the specific *value* from those assigned to *term*.
        replace — (multi-or-single-select change) Remove *old_value* and add
                  *value* in a single atomic GET-PUT round-trip.  Requires
                  *old_value* to be supplied.
        set     — (single-select) Remove ALL currently assigned values for
                  *term*, then assign exactly *value*.  If the term has no
                  existing values in the XML the categoryType href is resolved
                  automatically via the ETM categoryType feed."""
        try:
            if not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})
            if action not in ("add", "remove", "replace", "set"):
                return json.dumps({"error": "action must be one of: 'add', 'remove', 'replace', 'set'"})
            if action == "replace" and not old_value:
                return json.dumps({"error": "old_value is required when action='replace'"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)
            response = make_request(
                endpoint,
                accept_type="application/xml",
                configuration_context=configuration_context,
            )
            xml_text = response.text

            # escape() does not encode quotes — use explicit mapping for attribute safety
            _quote_map = {'"': "&quot;", "'": "&apos;"}
            esc_term = escape(term, _quote_map)
            esc_value = escape(value, _quote_map)

            root_close_re = re.compile(r"(</ns2:testcase>)\s*$")

            # ------------------------------------------------------------------
            # Helper: find a category href for *term* from the current XML,
            # falling back to the categoryType feed if needed.
            # The raw XML uses  term="..." value="..." href="..."  attribute order,
            # so we use a lookahead to locate term anywhere inside the element.
            # ------------------------------------------------------------------
            def _resolve_href() -> Optional[str]:
                # Lookahead: <ns2:category that contains term="<esc_term>" anywhere,
                # then capture the href="..." value (which may come after term).
                pat = r'<ns2:category(?=[^>]*\bterm="' + re.escape(esc_term) + r'")[^>]*' r'\bhref="([^"]+)"'
                m = re.search(pat, xml_text)
                if m:
                    return m.group(1)
                # Fallback: query the categoryType feed
                return fetch_category_type_href(project, term)

            # ------------------------------------------------------------------
            # Helper: remove a specific value for *term* from xml_text.
            # Uses two lookaheads so attribute order does not matter.
            # ------------------------------------------------------------------
            def _remove_value(xml: str, esc_t: str, esc_v: str) -> tuple[str, int]:
                rm_re = re.compile(
                    r"\s*<ns2:category"
                    r'(?=[^>]*\bterm="' + re.escape(esc_t) + r'")'
                    r'(?=[^>]*\bvalue="' + re.escape(esc_v) + r'")[^/]*/>'
                )
                return rm_re.subn("", xml)

            # ------------------------------------------------------------------
            # Helper: remove ALL values for *term* from xml_text.
            # ------------------------------------------------------------------
            def _remove_all_values(xml: str, esc_t: str) -> str:
                rm_all_re = re.compile(r'\s*<ns2:category(?=[^>]*\bterm="' + re.escape(esc_t) + r'")[^/]*/>')
                return rm_all_re.sub("", xml)

            # ------------------------------------------------------------------
            # ADD
            # ------------------------------------------------------------------
            if action == "add":
                category_href = _resolve_href()
                if not category_href:
                    return json.dumps(
                        {
                            "error": f"Cannot find categoryType href for term '{term}'. "
                            "Ensure at least one existing value for this term exists, "
                            "or that the term is a valid category in this project."
                        }
                    )
                # Check if value already present (attribute-order agnostic)
                already_re = re.compile(
                    r'<ns2:category(?=[^>]*\bterm="' + re.escape(esc_term) + r'")'
                    r'(?=[^>]*\bvalue="' + re.escape(esc_value) + r'")[^/]*/>'
                )
                if already_re.search(xml_text):
                    return json.dumps(
                        {
                            "success": True,
                            "test_case_id": test_case_id,
                            "message": f"Category '{term}={value}' already present — no change needed.",
                        }
                    )
                new_cat = f'<ns2:category href="{category_href}" term="{esc_term}" value="{esc_value}"/>'
                if not root_close_re.search(xml_text):
                    return json.dumps({"error": "Could not locate closing </ns2:testcase> tag."})
                xml_text = root_close_re.sub(new_cat + r"\1", xml_text)

            # ------------------------------------------------------------------
            # REMOVE
            # ------------------------------------------------------------------
            elif action == "remove":
                xml_text, count = _remove_value(xml_text, esc_term, esc_value)
                if count == 0:
                    return json.dumps(
                        {
                            "success": False,
                            "test_case_id": test_case_id,
                            "message": f"Category '{term}={value}' not found — nothing removed.",
                        }
                    )

            # ------------------------------------------------------------------
            # REPLACE  (remove old_value, add value — single round-trip)
            # ------------------------------------------------------------------
            elif action == "replace":
                esc_old = escape(old_value or "")
                xml_text, count = _remove_value(xml_text, esc_term, esc_old)
                if count == 0:
                    return json.dumps(
                        {
                            "success": False,
                            "test_case_id": test_case_id,
                            "message": f"Category '{term}={old_value}' not found — replace aborted.",
                        }
                    )
                # After removal the href is gone for this term if it was the only value;
                # re-resolve from the (now possibly empty) xml_text or the feed.
                category_href = _resolve_href()
                if not category_href:
                    return json.dumps(
                        {
                            "error": f"Cannot find categoryType href for term '{term}' after removal. "
                            "The feed lookup also failed."
                        }
                    )
                new_cat = f'<ns2:category href="{category_href}" term="{esc_term}" value="{esc_value}"/>'
                if not root_close_re.search(xml_text):
                    return json.dumps({"error": "Could not locate closing </ns2:testcase> tag."})
                xml_text = root_close_re.sub(new_cat + r"\1", xml_text)

            # ------------------------------------------------------------------
            # SET  (single-select: clear all existing values, assign exactly one)
            # ------------------------------------------------------------------
            elif action == "set":
                # Resolve href before removing (so it's still in the XML)
                category_href = _resolve_href()
                xml_text = _remove_all_values(xml_text, esc_term)
                if not category_href:
                    return json.dumps(
                        {
                            "error": f"Cannot find categoryType href for term '{term}'. "
                            "The feed lookup also failed — is '{term}' a valid category?"
                        }
                    )
                new_cat = f'<ns2:category href="{category_href}" term="{esc_term}" value="{esc_value}"/>'
                if not root_close_re.search(xml_text):
                    return json.dumps({"error": "Could not locate closing </ns2:testcase> tag."})
                xml_text = root_close_re.sub(new_cat + r"\1", xml_text)

            logger.info(f"Updating category on testcase {test_case_id}: {action} {term}={value}")
            make_request(
                endpoint,
                method="PUT",
                data=xml_text.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/xml",
                timeout=60,
                configuration_context=configuration_context,
            )

            detail = f"'{term}': '{old_value}' → '{value}'" if action == "replace" else f"'{term}={value}'"
            return json.dumps(
                {
                    "success": True,
                    "test_case_id": test_case_id,
                    "term": term,
                    "value": value,
                    "old_value": old_value if action == "replace" else None,
                    "action": action,
                    "message": f"Category {detail} updated successfully (action={action})",
                }
            )
        except Exception as e:
            return handle_error("update_test_case_category", e)

    # ----------------------------------------------------------------------------
    # AI-GENERATED (GitHub Copilot / Claude Sonnet 4.6) — 2026-03-11
    # New read-only MCP tool to inspect all category assignments of a test case.
    # Derived from the Task-1 logic in do_category_changes.py: iterates over every
    # <ns2:category> element in the raw XML and groups values by term, also
    # indicating whether the term behaves as single- or multi-select.
    # ----------------------------------------------------------------------------

    def get_test_case_categories(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3599953'), NOT a slug identifier.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Read all category assignments (term/value pairs) for a test case.

        AI-generated tool (GitHub Copilot / Claude Sonnet 4.6 — 2026-03-11).
        Derived from the category-inspection logic in do_category_changes.py.

        Fetches the raw XML for the test case and parses every
        ``<ns2:category term="..." value="..."/>`` element, grouping values by
        term name.  Each entry in the result also indicates whether the term
        currently has a single value or multiple values assigned.

        Returns a JSON object with:
        - ``test_case_id``: the requested ID
        - ``categories``: list of ``{term, values, mode}`` dicts
            - ``term``: the category type name (e.g., "Variant", "Test Level")
            - ``values``: list of currently assigned values
            - ``mode``: ``"single-select"`` if one value, ``"multi-select"`` if many"""
        try:
            if not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)

            # AI-generated: GET raw XML — avoid ElementTree to preserve rich HTML
            response = make_request(endpoint, accept_type="application/xml")
            xml_text = response.text

            # AI-generated: parse every <ns2:category .../> with regex so that
            # attribute order (term/value/href) does not matter
            cats: dict[str, list[str]] = defaultdict(list)
            for el_m in re.finditer(r"<ns2:category\b[^/]*/>", xml_text):
                el = el_m.group()
                term_m = re.search(r'\bterm="([^"]+)"', el)
                value_m = re.search(r'\bvalue="([^"]+)"', el)
                if term_m and value_m:
                    cats[term_m.group(1)].append(value_m.group(1))

            # AI-generated: build structured result for the MCP caller
            categories = [
                {
                    "term": term,
                    "values": vals,
                    "mode": "multi-select" if len(vals) > 1 else "single-select",
                }
                for term, vals in sorted(cats.items())
            ]

            return json.dumps(
                {
                    "test_case_id": test_case_id,
                    "categories": categories,
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_test_case_categories", e)

    # ----------------------------------------------------------------------------
    # AI-GENERATED (GitHub Copilot / Claude Sonnet 4.6) — 2026-03-05
    # The two MCP tools below were added to expose custom attribute read/write
    # capabilities through the MCP interface. They rely on the helper functions
    # _find_custom_attribute_element() and _update_custom_attribute_in_xml().
    # ----------------------------------------------------------------------------

    def get_test_case_custom_attributes(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3500617'), NOT a slug identifier.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get all custom attributes of a test case as a JSON list."""
        try:
            if not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)
            response = make_request(endpoint, accept_type="application/xml")

            root = ET.fromstring(response.text)
            ns = {"ns2": ETM_NAMESPACE}

            attributes = []
            for custom_attr in root.findall(".//ns2:customAttributes/ns2:customAttribute", ns):
                name_elem = custom_attr.find("ns2:name", ns)
                value_elem = custom_attr.find("ns2:value", ns)
                value_text = value_elem.text if value_elem is not None else None
                if name_elem is not None and name_elem.text and value_text and value_text.strip():
                    attributes.append(
                        {
                            "name": name_elem.text,
                            "value": value_text,
                        }
                    )

            return json.dumps(
                {
                    "test_case_id": test_case_id,
                    "custom_attributes": attributes,
                    "count": len(attributes),
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_test_case_custom_attributes", e)

    def update_test_case_custom_attribute(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3500617'), NOT a slug identifier.")],
        attribute_name: Annotated[str, Field(description="Exact custom attribute name (e.g., 'Honda_Test_Case_ID').")],
        value: Annotated[str, Field(description="Value to set or append.")],
        append: Annotated[
            bool, Field(description="True to append with '; ' separator, False to replace. Default False.")
        ] = False,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Update a single custom attribute on a test case.

        Can either SET a new value (replacing any existing one) or APPEND to the
        existing value with '; ' as separator.

        If the attribute does not yet exist on the test case, it will be created."""
        try:
            if not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})
            if not attribute_name.strip():
                return json.dumps({"error": "attribute_name is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)

            # Step 1: GET current XML
            response = make_request(endpoint, accept_type="application/xml")

            # Step 2: Modify the custom attribute in the XML tree
            updated_xml = update_custom_attribute_in_xml(response.text, attribute_name, value, append=append)

            # Step 3: PUT the updated XML back
            logger.info(
                f"Updating custom attribute '{attribute_name}' on testcase {test_case_id} "
                f"({'append' if append else 'set'} → '{value}')"
            )
            make_request(
                endpoint,
                method="PUT",
                data=updated_xml,
                accept_type="application/xml",
                content_type="application/xml",
                timeout=60,
            )

            return json.dumps(
                {
                    "success": True,
                    "test_case_id": test_case_id,
                    "attribute_name": attribute_name,
                    "value": value,
                    "action": "append" if append else "set",
                    "message": f"Custom attribute '{attribute_name}' updated successfully",
                }
            )
        except Exception as e:
            return handle_error("update_test_case_custom_attribute", e)

    # ----------------------------------------------------------------------------
    # MCP tool to get and update architecture element links on test cases.
    # Uses string manipulation to avoid corrupting rich-text HTML content.
    # ----------------------------------------------------------------------------

    def get_architecture_element_links(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3435411'), NOT a slug identifier.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get architecture element links from a test case.

        Returns all <architectureelement> href links associated with the test case."""
        try:
            if not test_case_id or not test_case_id.strip():
                return invalid_id_error("test_case_id", test_case_id or "")

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)
            response = make_request(
                endpoint, accept_type="application/xml", configuration_context=configuration_context
            )

            root = ET.fromstring(response.text)
            ns = {"ns2": ETM_NAMESPACE}

            architecture_links: list[dict[str, str]] = []
            for elem in root.findall(".//ns2:architectureelement", ns):
                href = elem.get("href", "")
                if href:
                    link_data: dict[str, str] = {"href": href}
                    summary = elem.get("summary", "")
                    if summary:
                        link_data["summary"] = summary
                    architecture_links.append(link_data)

            return json.dumps(
                {
                    "test_case_id": test_case_id,
                    "architecture_element_links": architecture_links,
                    "count": len(architecture_links),
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_architecture_element_links", e)

    def update_architecture_element_links(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3435411'), NOT a slug identifier.")],
        action: Annotated[
            str,
            Field(
                description=(
                    "Action to perform: 'add' to add links, 'remove' to remove links, "
                    "'set' to replace all existing links with the provided list."
                )
            ),
        ],
        hrefs: Annotated[
            list[str],
            Field(
                description=(
                    "List of architecture element URLs (hrefs) to add, remove, or set. "
                    "These are full URLs pointing to architecture resources "
                    "(e.g., DNG/AM artifacts like 'https://server/am/resource/...')."
                )
            ),
        ],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Add, remove, or set architecture element links on a test case.

        Actions:
          - add: Append new architecture element links (skips duplicates)
          - remove: Remove architecture element links matching the given hrefs
          - set: Replace ALL existing architecture element links with the provided list
        """
        try:
            if not test_case_id or not test_case_id.strip():
                return invalid_id_error("test_case_id", test_case_id or "")
            if action not in ("add", "remove", "set"):
                return json.dumps({"error": "action must be 'add', 'remove', or 'set'"})
            if not hrefs:
                return json.dumps({"error": "hrefs list is required and cannot be empty"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)

            # Step 1: GET current XML
            response = make_request(
                endpoint, accept_type="application/xml", configuration_context=configuration_context
            )
            xml_text = response.text
            etag = response.headers.get("ETag")
            put_headers = {"If-Match": etag} if etag else None

            # Step 2: Manipulate architecture element links using string/regex
            # Pattern matches <ns2:architectureelement .../> or <ns2:architectureelement ...>...</ns2:architectureelement>
            arch_elem_self_closing_re = re.compile(
                r'<(?:\w+:)?architectureelement\b[^>]*href="([^"]*)"[^>]*/>', re.DOTALL
            )
            arch_elem_open_close_re = re.compile(
                r'<(?:\w+:)?architectureelement\b[^>]*href="([^"]*)"[^>]*>.*?</(?:\w+:)?architectureelement>',
                re.DOTALL,
            )

            # Collect existing hrefs
            existing_hrefs: list[str] = []
            for m in arch_elem_self_closing_re.finditer(xml_text):
                existing_hrefs.append(m.group(1))
            for m in arch_elem_open_close_re.finditer(xml_text):
                existing_hrefs.append(m.group(1))

            if action == "add":
                # Add new links that don't already exist
                new_hrefs = [h for h in hrefs if h not in existing_hrefs]
                if not new_hrefs:
                    return json.dumps(
                        {
                            "test_case_id": test_case_id,
                            "action": "add",
                            "added": 0,
                            "message": "All provided links already exist on the test case",
                        }
                    )
                # Insert before root closing tag
                _quote_map = {'"': "&quot;", "'": "&apos;"}
                new_elements = ""
                for href in new_hrefs:
                    new_elements += f'\n    <ns2:architectureelement href="{escape(href, _quote_map)}"/>'
                root_close_re = re.compile(r"(</(?:ns2|qm):\w+>)\s*$")
                xml_text = root_close_re.sub(new_elements + r"\n\g<1>", xml_text)
                added_count = len(new_hrefs)
                removed_count = 0

            elif action == "remove":
                # Remove links matching provided hrefs
                removed_count = 0
                for href in hrefs:
                    escaped_href = re.escape(href)
                    # Try self-closing first
                    pattern_sc = re.compile(
                        r'\s*<(?:\w+:)?architectureelement\b[^>]*href="' + escaped_href + r'"[^>]*/>\s*',
                        re.DOTALL,
                    )
                    xml_text, n = pattern_sc.subn("", xml_text)
                    removed_count += n
                    # Try open-close
                    pattern_oc = re.compile(
                        r"\s*<(?:\w+:)?architectureelement\b[^>]*href=\""
                        + escaped_href
                        + r"\"[^>]*>.*?</(?:\w+:)?architectureelement>\s*",
                        re.DOTALL,
                    )
                    xml_text, n = pattern_oc.subn("", xml_text)
                    removed_count += n
                added_count = 0

            else:  # action == "set"
                # Remove ALL existing architecture element links
                xml_text = arch_elem_self_closing_re.sub("", xml_text)
                xml_text = arch_elem_open_close_re.sub("", xml_text)
                # Add all provided hrefs
                _quote_map = {'"': "&quot;", "'": "&apos;"}
                new_elements = ""
                for href in hrefs:
                    new_elements += f'\n    <ns2:architectureelement href="{escape(href, _quote_map)}"/>'
                root_close_re = re.compile(r"(</(?:ns2|qm):\w+>)\s*$")
                xml_text = root_close_re.sub(new_elements + r"\n\g<1>", xml_text)
                added_count = len(hrefs)
                removed_count = len(existing_hrefs)

            # Step 3: PUT updated XML
            logger.info(
                f"Updating architecture element links on testcase {test_case_id}: "
                f"action={action}, added={added_count}, removed={removed_count}"
            )
            make_request(
                endpoint,
                method="PUT",
                data=xml_text.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                extra_headers=put_headers,
                configuration_context=configuration_context,
            )

            return json.dumps(
                {
                    "success": True,
                    "test_case_id": test_case_id,
                    "action": action,
                    "added": added_count,
                    "removed": removed_count,
                    "message": f"Architecture element links updated successfully ({action})",
                }
            )
        except Exception as e:
            return handle_error("update_architecture_element_links", e)

    # ----------------------------------------------------------------------------
    # AI-CHANGED (GitHub Copilot / Claude Opus 4.6) — 2026-03-11
    # MCP tool to detect and repair XML corruption caused by ElementTree
    # re-serialization. Can run in dry-run mode (detect only) or apply fixes.
    # ----------------------------------------------------------------------------

    # AI-constructed: entire tool below was written by AI (GitHub Copilot / Claude Opus 4.6)
    # to expose the _fix_et_corruption helper as an MCP tool for on-demand detection and repair.
    def fix_test_case_xml(
        self,
        test_case_id: Annotated[str, Field(description="Numeric webId (e.g., '3599953'), NOT a slug identifier.")],
        dry_run: Annotated[
            bool, Field(description="True (default) = detect only. False = detect and apply fixes.")
        ] = True,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Detect and fix XML corruption in a test case caused by ElementTree re-serialization.

        AI-constructed tool (GitHub Copilot / Claude Opus 4.6 — 2026-03-11).

        ElementTree re-serialization corrupts rich HTML sections (testCaseDesign,
        Review Criteria, etc.) by rewriting namespace prefixes, injecting xmlns:html
        declarations, stripping MS Office namespaces, and adding extra div wrappers.

        This tool scans the test case XML for all four corruption patterns and
        reports what it finds. Set dry_run=False to apply the fixes."""
        try:
            if not test_case_id.strip():
                return json.dumps({"error": "test_case_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase", test_case_id)

            # AI-constructed: GET current XML for corruption analysis
            response = make_request(endpoint, accept_type="application/xml")
            original_xml = response.text

            # AI-constructed: delegate detection and repair to fix_et_corruption
            fixed_xml, fixes = fix_et_corruption(original_xml)

            if not fixes:
                return json.dumps(
                    {
                        "test_case_id": test_case_id,
                        "corrupted": False,
                        "message": "No ET re-serialization corruption detected",
                    }
                )

            # AI-constructed: dry_run mode — report findings without modifying
            if dry_run:
                return json.dumps(
                    {
                        "test_case_id": test_case_id,
                        "corrupted": True,
                        "dry_run": True,
                        "fixes_available": fixes,
                        "message": "Corruption detected. Set dry_run=False to apply fixes.",
                    },
                    indent=2,
                )

            # AI-constructed: apply mode — PUT the fixed XML back to ETM
            logger.info(f"Applying ET corruption fix to testcase {test_case_id}: {fixes}")
            make_request(
                endpoint,
                method="PUT",
                data=fixed_xml.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/xml",
                timeout=60,
            )

            return json.dumps(
                {
                    "success": True,
                    "test_case_id": test_case_id,
                    "corrupted": True,
                    "dry_run": False,
                    "fixes_applied": fixes,
                    "message": "Test case XML corruption repaired successfully",
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("fix_test_case_xml", e)
