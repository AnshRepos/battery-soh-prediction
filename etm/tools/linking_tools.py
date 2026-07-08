"""ETM Linking Tools -- MCP tools for linking test cases, suites, plans, and defects."""

import base64
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Annotated, Optional
from urllib.parse import quote, urlencode

import requests
from core.config import (
    CONFIG_CONTEXT_DESC,
    ETM_BASE_URL,
    ETM_NAMESPACE,
    ETM_PASSWORD,
    ETM_PROJECT_AREA,
    ETM_USERNAME,
    ETM_VERIFY_SSL,
    JIRA_PAT,
    OSLC_QM_NAMESPACE,
    PROJECT_AREA_DESC,
)
from pydantic import Field
from services.etm_client import (
    build_resource_href,
    build_resource_url,
    collect_paginated_entries,
    fetch_all_pages,
    handle_error,
    make_request,
    project_area_required_error,
)
from services.oslc import oslc_query
from services.xml_helpers import fix_xml_raw

logger = logging.getLogger(__name__)


# ============================================================================
# TOOLS - LINKING & SUITE OPERATIONS
# ============================================================================


class LinkingTools:
    """ETM Linking tools methods."""

    def add_test_cases_to_suite(
        self,
        test_suite_id: Annotated[str, Field(description="Numeric webId of the test suite.")],
        test_case_ids: Annotated[list[str], Field(description="List of test case numeric webIds to add.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Add test cases to an existing test suite."""
        try:
            if not test_suite_id or not test_case_ids:
                return json.dumps({"error": "test_suite_id and test_case_ids are required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testsuite", test_suite_id)

            response = make_request(
                endpoint,
                accept_type="application/xml",
                configuration_context=configuration_context,
            )
            # Strip weight element before parsing to prevent 400 on PUT
            root = ET.fromstring(fix_xml_raw(response.text))
            etag = response.headers.get("ETag")
            put_headers = {"If-Match": etag} if etag else None

            # Find or create the <suiteelements> container
            suite_elements = root.find(f"{{{ETM_NAMESPACE}}}suiteelements")
            if suite_elements is None:
                suite_elements = ET.SubElement(root, f"{{{ETM_NAMESPACE}}}suiteelements")

            # Determine the next index based on existing suite elements
            existing_indices = []
            for existing_elem in suite_elements.findall(f"{{{ETM_NAMESPACE}}}suiteelement"):
                idx_elem = existing_elem.find(f"{{{ETM_NAMESPACE}}}index")
                if idx_elem is not None and idx_elem.text is not None:
                    try:
                        existing_indices.append(int(idx_elem.text))
                    except ValueError:
                        pass
            next_index = max(existing_indices, default=-1) + 1

            # Add new test case references inside <suiteelements>
            for tc_id in test_case_ids:
                tc_href = build_resource_href(project, "testcase", tc_id)
                suite_elem = ET.SubElement(suite_elements, f"{{{ETM_NAMESPACE}}}suiteelement")
                tc_elem = ET.SubElement(suite_elem, f"{{{ETM_NAMESPACE}}}testcase")
                tc_elem.set("href", tc_href)
                idx_elem = ET.SubElement(suite_elem, f"{{{ETM_NAMESPACE}}}index")
                idx_elem.text = str(next_index)
                next_index += 1

            updated_xml = fix_xml_raw(ET.tostring(root, encoding="unicode"))
            logger.debug(f"Adding test cases to suite with XML:\n{updated_xml}")
            make_request(
                endpoint,
                method="PUT",
                data=updated_xml,
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                extra_headers=put_headers,
                configuration_context=configuration_context,
            )

            return json.dumps(
                {
                    "success": True,
                    "test_suite_id": test_suite_id,
                    "test_cases_added": len(test_case_ids),
                    "message": "Test cases added to suite successfully",
                }
            )
        except Exception as e:
            return handle_error("add_test_cases_to_suite", e)

    def link_testcase_to_testplan(
        self,
        test_plan_id: Annotated[str, Field(description="Numeric webId of the test plan.")],
        test_case_id: Annotated[str, Field(description="Numeric webId of the test case to link.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Link a test case to a test plan."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            # Get the test plan
            plan_endpoint = build_resource_url(project, "testplan", test_plan_id)
            plan_response = make_request(
                plan_endpoint, accept_type="application/xml", configuration_context=configuration_context
            )
            etag = plan_response.headers.get("ETag")
            put_headers = {"If-Match": etag} if etag else None

            root = ET.fromstring(fix_xml_raw(plan_response.text))

            # Build proper href using build_resource_href
            testcase_href = build_resource_href(project, "testcase", test_case_id)

            # Create new testcase element
            testcase_elem = ET.Element(f"{{{ETM_NAMESPACE}}}testcase")
            testcase_elem.set("href", testcase_href)
            root.append(testcase_elem)

            # Convert back to XML string; repair any html: prefixes ET.tostring() may have added
            _raw = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
            updated_xml = fix_xml_raw(_raw).encode("utf-8")

            logger.info(f"Linking test case {test_case_id} to plan {test_plan_id}")
            logger.debug(f"Linking test case to plan with XML:\n{updated_xml.decode('utf-8')}")

            # PUT the updated test plan
            make_request(
                plan_endpoint,
                method="PUT",
                data=updated_xml,
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                extra_headers=put_headers,
                configuration_context=configuration_context,
            )

            return json.dumps(
                {
                    "success": True,
                    "message": f"Test case {test_case_id} linked to test plan {test_plan_id}",
                }
            )
        except Exception as e:
            return handle_error("link_testcase_to_testplan", e)

    def link_test_suite_to_plan(
        self,
        test_suite_id: Annotated[str, Field(description="Numeric webId of the test suite.")],
        test_plan_id: Annotated[str, Field(description="Numeric webId of the test plan.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Link a test suite to a test plan."""
        try:
            if not test_suite_id or not test_plan_id:
                return json.dumps({"error": "test_suite_id and test_plan_id are required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testplan", test_plan_id)

            response = make_request(
                endpoint, accept_type="application/xml", configuration_context=configuration_context
            )
            etag = response.headers.get("ETag")
            put_headers = {"If-Match": etag} if etag else None
            root = ET.fromstring(fix_xml_raw(response.text))

            # Use build_resource_href for proper URL
            suite_href = build_resource_href(project, "testsuite", test_suite_id)
            suite_elem = ET.SubElement(root, f"{{{ETM_NAMESPACE}}}testsuite")
            suite_elem.set("href", suite_href)

            _raw = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
            updated_xml = fix_xml_raw(_raw).encode("utf-8")
            logger.info(f"Linking test suite {test_suite_id} to plan {test_plan_id}")
            logger.debug(f"Linking test suite to plan with XML:\n{updated_xml.decode('utf-8')}")

            make_request(
                endpoint,
                method="PUT",
                data=updated_xml,
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                extra_headers=put_headers,
                configuration_context=configuration_context,
            )

            return json.dumps(
                {
                    "success": True,
                    "test_suite_id": test_suite_id,
                    "test_plan_id": test_plan_id,
                    "message": "Test suite linked to plan successfully",
                }
            )
        except Exception as e:
            return handle_error("link_test_suite_to_plan", e)

    def get_test_cases_by_use_case(
        self,
        use_case_name: Annotated[str, Field(description="Use case name or identifier to search for.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get test cases associated with a specific use case (matches category, title, or description)."""
        try:
            if not use_case_name:
                return json.dumps({"error": "use_case_name is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase")

            # Fetch all test cases via paginated Atom feed
            root = fetch_all_pages(
                endpoint,
                {"abbreviate": "false"},
                page_size=200,
                timeout=300,
                configuration_context=configuration_context,
            )

            # Parse and filter
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "ns2": ETM_NAMESPACE,
                "dc": "http://purl.org/dc/elements/1.1/",
            }

            matching_cases = []

            for entry in root.findall(".//atom:entry", ns):
                testcase = entry.find(".//ns2:testcase", ns)
                if testcase is None:
                    continue

                # Check category
                category_match = False
                for cat_elem in testcase.findall(".//ns2:category", ns):
                    cat_value = cat_elem.get("value", "")
                    if use_case_name.lower() in cat_value.lower():
                        category_match = True
                        break

                # Check title
                title_elem = testcase.find(".//dc:title", ns)
                title_match = False
                if title_elem is not None and title_elem.text:
                    if use_case_name.lower() in title_elem.text.lower():
                        title_match = True

                # Check description
                desc_elem = testcase.find(".//dc:description", ns)
                desc_match = False
                if desc_elem is not None and desc_elem.text:
                    if use_case_name.lower() in desc_elem.text.lower():
                        desc_match = True

                # If any match, include
                if category_match or title_match or desc_match:
                    # Extract ID from child elements (dcterms:identifier or qm:webId)
                    id_elem = testcase.find("{http://purl.org/dc/terms/}identifier")
                    if id_elem is None or not id_elem.text:
                        id_elem = testcase.find(".//ns2:webId", ns)
                    tc_id = id_elem.text if id_elem is not None and id_elem.text else "unknown"
                    title = title_elem.text if title_elem is not None else "unknown"

                    matching_cases.append(
                        {
                            "test_case_id": tc_id,
                            "title": title,
                            "match_type": (
                                "category" if category_match else ("title" if title_match else "description")
                            ),
                        }
                    )

            return json.dumps(
                {
                    "success": True,
                    "use_case": use_case_name,
                    "count": len(matching_cases),
                    "test_cases": matching_cases,
                },
                indent=2,
            )

        except Exception as e:
            return handle_error("get_test_cases_by_use_case", e)

    def get_failed_executions_without_defects(
        self,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        test_plan_id: Annotated[
            Optional[str], Field(description="Optional: filter by test plan numeric webId.")
        ] = None,
        start_date: Annotated[
            Optional[str], Field(description="Optional: start date filter in YYYY-MM-DD format.")
        ] = None,
        end_date: Annotated[Optional[str], Field(description="Optional: end date filter in YYYY-MM-DD format.")] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get failed test executions that don't have defects linked."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "executionresult")
            entries = collect_paginated_entries(
                endpoint,
                "executionresult",
                params={"abbreviate": "false"},
                timeout=180,
                configuration_context=configuration_context,
            )

            failed_without_defects = []

            for entry in entries:
                state = str(entry.get("state", ""))
                if state != "com.ibm.rqm.execution.common.state.failed":
                    continue

                # Filter by test plan if specified
                if test_plan_id:
                    testplan_ref = entry.get("testplan", "")
                    if isinstance(testplan_ref, list):
                        if not any(test_plan_id in ref for ref in testplan_ref):
                            continue
                    else:
                        if test_plan_id not in str(testplan_ref):
                            continue

                # Filter by date range
                if start_date or end_date:
                    updated_str = str(entry.get("updated", "")).split("T")[0]
                    if start_date and updated_str < start_date:
                        continue
                    if end_date and updated_str > end_date:
                        continue

                # Check if defects are linked
                defect_refs = entry.get("relatedworkitem")
                if defect_refs:
                    continue  # Has defects, skip

                # Extract key info
                exec_id = str(entry.get("identifier") or entry.get("webId") or "unknown")
                testcase_ref = str(entry.get("testcase", ""))
                test_case = testcase_ref.split(":")[-1] if testcase_ref else "unknown"
                updated = str(entry.get("updated", "unknown"))

                failed_without_defects.append(
                    {
                        "execution_id": exec_id,
                        "test_case_id": test_case,
                        "updated": updated,
                    }
                )

            return json.dumps(
                {
                    "success": True,
                    "count": len(failed_without_defects),
                    "failed_without_defects": failed_without_defects,
                },
                indent=2,
            )

        except Exception as e:
            return handle_error("get_failed_executions_without_defects", e)

    # Enhanced to scan qm:relatedchangerequest and oslc_qm:affectedByChangeRequest
    # in addition to qm:relatedworkitem; adds OSLC query fallback for links stored
    # as RDF triples (invisible in native XML GET).
    def get_execution_defects(
        self,
        execution_result_id: Annotated[str, Field(description="Numeric execution result ID.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get defects linked to a specific execution result.

        Returns list of defect URLs (e.g., JIRA tickets) associated with
        this execution. Checks all known ETM defect element variants and falls
        back to an OSLC query for links created via ICmIntegrationRestService.
        """
        try:
            if not execution_result_id:
                return json.dumps({"error": "execution_result_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "executionresult", execution_result_id)

            response = make_request(
                endpoint, accept_type="application/xml", configuration_context=configuration_context
            )
            root = ET.fromstring(response.text)
            rdf_ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

            defects: list[str] = []
            # Primary: qm:relatedworkitem
            for wi in root.findall(f".//{{{ETM_NAMESPACE}}}relatedworkitem"):
                href = wi.get("href", "")
                if href:
                    defects.append(href)
            # Fallback: qm:relatedchangerequest
            for wi in root.findall(f".//{{{ETM_NAMESPACE}}}relatedchangerequest"):
                href = wi.get("href", "")
                if href and href not in defects:
                    defects.append(href)
            # Fallback: oslc_qm:affectedByChangeRequest with rdf:resource attribute
            for wi in root.findall(f".//{{{OSLC_QM_NAMESPACE}}}affectedByChangeRequest"):
                href = wi.get(f"{{{rdf_ns}}}resource", "") or wi.get("href", "")
                if href and href not in defects:
                    defects.append(href)

            # OSLC-layer fallback: links created via ICmIntegrationRestService/newLink are stored
            # as OSLC triples, not in the native XML. Query OSLC when native XML finds nothing.
            if not defects:
                try:
                    oslc_json = oslc_query(
                        resource_type="executionresult",
                        project_area=project,
                        where=f'oslc:shortId="{execution_result_id}"',
                        select="oslc_qm:affectedByChangeRequest",
                        limit=100,
                        configuration_context=configuration_context,
                    )
                    oslc_data = json.loads(oslc_json)
                    for item in oslc_data.get("executionresults", []):
                        for key in (f"{OSLC_QM_NAMESPACE}affectedByChangeRequest", "qm_affectedByChangeRequest"):
                            val = item.get(key, "")
                            if val and val not in defects:
                                defects.append(val)
                except Exception:
                    pass

            return json.dumps(
                {
                    "success": True,
                    "execution_result_id": execution_result_id,
                    "defect_count": len(defects),
                    "defects": defects,
                },
                indent=2,
            )

        except Exception as e:
            return handle_error("get_execution_defects", e)

    # Rewritten to use two-step OSLC pattern mirroring the ETM browser UI (F12-captured):
    #   Step 1 — PUT OSLC backlink on Jira via ETM proxy (requires OSLC friendship or DownstreamAuth).
    #            Falls back to Jira Remote Link REST API when OSLC proxy returns DownstreamAuth.
    #   Step 2 — POST to ICmIntegrationRestService/newLink to register the link on the ETM side.
    def link_defect_to_execution_result(
        self,
        execution_result_id: Annotated[str, Field(description="Numeric execution result ID.")],
        defect_url: Annotated[
            str, Field(description="Full URL to the defect (e.g., JIRA ticket URL or OSLC REST URL).")
        ],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Link a defect (JIRA ticket) to a test execution result.

        Uses a two-step approach mirroring the ETM browser UI (F12-captured):
        Step 1 — PUT OSLC backlink on Jira via ETM proxy (requires OSLC friendship or DownstreamAuth).
                 Falls back to Jira Remote Link REST API when OSLC proxy returns DownstreamAuth
                 and JIRA_PAT env var is set.
        Step 2 — POST to ICmIntegrationRestService/newLink to register the link on the ETM side.
        """
        try:
            if not execution_result_id or not defect_url:
                return json.dumps({"error": "execution_result_id and defect_url are required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            # Normalise Jira browser URL → OSLC REST URL
            oslc_defect_url = defect_url
            key_match = re.search(r"([A-Z][A-Z0-9_]+-\d+)", defect_url)
            if key_match and "/rest/oslc/" not in defect_url:
                issue_key = key_match.group(1)
                host_match = re.match(r"(https?://[^/]+/[^/]+)", defect_url)
                base = host_match.group(1) if host_match else "https://rb-tracker.bosch.com/tracker08"
                oslc_defect_url = f"{base}/rest/oslc/1.0/cm/issue/{issue_key}"
            issue_key = key_match.group(1) if key_match else oslc_defect_url

            # Step 1a: Resolve OSLC context UUIDs for the execution result.
            project_area_item_id: str = ""
            result_item_id: str = ""
            oslc_ctx_pattern = (
                r'oslc_qm/contexts/([^/"?\s]+)/resources/' r"com\.ibm\.rqm\.execution\.ExecutionResult/([^/\"?\s&]+)"
            )

            oslc_er_json = oslc_query(
                resource_type="executionresult",
                project_area=project,
                where=f'oslc:shortId="{execution_result_id}"',
                select="dcterms:title",
                limit=1,
                configuration_context=configuration_context,
            )
            oslc_er_list = json.loads(oslc_er_json).get("executionresults", [])
            if oslc_er_list:
                m = re.search(oslc_ctx_pattern, oslc_er_list[0].get("url", ""))
                if m:
                    project_area_item_id, result_item_id = m.group(1), m.group(2)

            if not project_area_item_id or not result_item_id:
                # Fallback: scan native XML for embedded OSLC URL
                r = make_request(
                    build_resource_url(project, "executionresult", execution_result_id),
                    accept_type="application/xml",
                    configuration_context=configuration_context,
                )
                m = re.search(oslc_ctx_pattern, r.text)
                if m:
                    project_area_item_id, result_item_id = m.group(1), m.group(2)

            if not project_area_item_id or not result_item_id:
                return json.dumps(
                    {
                        "error": "Could not extract OSLC context URL from execution result.",
                        "hint": "Open the execution result in ETM → Defects section → Link to Existing Defect",
                    }
                )

            result_oslc_url = (
                f"{ETM_BASE_URL}/oslc_qm/contexts/{project_area_item_id}"
                f"/resources/com.ibm.rqm.execution.ExecutionResult/{result_item_id}"
            )

            # Step 1b: PUT OSLC backlink via ETM proxy so Jira shows the ETM link.
            oslc_props = "oslc_cm%3AaffectsTestResult%2Coslc_cm%3ArelatedTestCase%2Coslc_cm%3ArelatedTestPlan"
            proxy_ep = (
                f"/proxy?uri={quote(oslc_defect_url, safe='')}"
                f"&oslc.properties={oslc_props}"
                f"&webContext.projectArea={quote(project_area_item_id, safe='')}"
            )
            proxy_updated = False
            _dbg: dict = {"proxy_endpoint": proxy_ep[:300]}

            # Build DownstreamAuth header (ETM forwards it to the tracker)
            downstream_hdr: dict[str, str] = {}
            if ETM_USERNAME and ETM_PASSWORD:
                _tok = base64.b64encode(f"{ETM_USERNAME}:{ETM_PASSWORD}".encode()).decode()
                downstream_hdr = {"Authorization": f"Basic {_tok}"}

            def _proxy_req(method: str, data: bytes | None = None, ct: str | None = None) -> requests.Response:
                kw: dict = {
                    "method": method,
                    "accept_type": "application/json",
                    "extra_headers": downstream_hdr or None,
                }
                if data is not None:
                    kw["data"] = data
                if ct is not None:
                    kw["content_type"] = ct
                try:
                    return make_request(proxy_ep, **kw)
                except requests.exceptions.HTTPError as e:
                    return e.response  # type: ignore[return-value]

            try:
                get_r = _proxy_req("GET")
                _dbg["get_status"] = get_r.status_code
                _dbg["get_www_auth"] = get_r.headers.get("WWW-Authenticate", "")
                existing: list = []
                if get_r.status_code == 200:
                    try:
                        af = json.loads(get_r.text).get("oslc_cm:affectsTestResult", [])
                        existing = af if isinstance(af, list) else [af]
                    except Exception:
                        pass
                new_entry = {
                    "dcterms:title": f"{execution_result_id}: Execution Result",
                    "rdf:resource": result_oslc_url,
                }
                if not any(e.get("rdf:resource") == result_oslc_url for e in existing):
                    existing.append(new_entry)
                put_payload = json.dumps(
                    {
                        "prefixes": {
                            "oslc_cm": "http://open-services.net/ns/cm#",
                            "dcterms": "http://purl.org/dc/terms/",
                            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                            "calm": "http://jazz.net/xmlns/prod/jazz/calm/1.0/",
                            "rtc_cm": "http://jazz.net/xmlns/prod/jazz/rtc/cm/1.0/",
                        },
                        "oslc_cm:affectsTestResult": existing,
                    }
                )
                put_r = _proxy_req("PUT", data=put_payload.encode("utf-8"), ct="application/json")
                _dbg["put_status"] = put_r.status_code
                if put_r.status_code in (200, 204):
                    proxy_updated = True
            except Exception as pe:
                _dbg["proxy_exception"] = str(pe)

            # Fallback: Jira Remote Link via Bearer PAT when ETM proxy has no OSLC friendship
            if not proxy_updated and _dbg.get("get_www_auth") == "DownstreamAuth" and JIRA_PAT:
                try:
                    host_m = re.match(r"(https?://[^/]+/[^/]+)", oslc_defect_url)
                    jira_base = host_m.group(1) if host_m else ""
                    etm_er_url = (
                        f"{ETM_BASE_URL}/web/console/{quote(project, safe='')}"
                        f"#action=com.ibm.rqm.planning.home.actionDispatcher"
                        f"&subAction=viewResult&resultItemId={result_item_id}"
                    )
                    rl_payload = {
                        "globalId": f"etm-er-{execution_result_id}",
                        "application": {"type": "com.ibm.rqm", "name": "IBM ETM"},
                        "relationship": "Test Execution Result",
                        "object": {
                            "url": etm_er_url,
                            "title": f"ETM ER {execution_result_id}",
                            "summary": f"Execution Result {execution_result_id} linked from ETM MCP",
                        },
                    }
                    rl_session = requests.Session()
                    rl_resp = rl_session.post(
                        f"{jira_base}/rest/api/2/issue/{issue_key}/remotelink",
                        headers={
                            "Authorization": f"Bearer {JIRA_PAT}",
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json=rl_payload,
                        verify=ETM_VERIFY_SSL,
                        timeout=30,
                    )
                    _dbg["remotelink_status"] = rl_resp.status_code
                    if rl_resp.status_code in (200, 201):
                        proxy_updated = True
                except Exception as rle:
                    _dbg["remotelink_exception"] = str(rle)

            # Step 2: POST to ICmIntegrationRestService/newLink (ETM UI F12-captured call).
            # Registers the defect link on the ETM side — does not require a live OSLC proxy.
            newlink_body = urlencode(
                {
                    "itemId": result_item_id,
                    "cmUri": oslc_defect_url,
                    "summary": issue_key,
                    "linkType": "com.ibm.rqm.execution.linktype.eresultrelatedtodefect",
                    "createRelatedLinks": "true",
                    "rqmProjectAreaItemId": project_area_item_id,
                    "projectAreaItemId": project_area_item_id,
                }
            )
            newlink_query = f"webContext.projectArea={quote(project_area_item_id, safe='')}"
            newlink_resp = make_request(
                f"/service/com.ibm.rqm.defects.service.internal.rest.ICmIntegrationRestService/newLink?{newlink_query}",
                method="POST",
                data=newlink_body.encode("utf-8"),
                accept_type="application/json",
                content_type="application/x-www-form-urlencoded",
            )
            logger.info("newLink response: %s %s", newlink_resp.status_code, newlink_resp.text[:200])

            return json.dumps(
                {
                    "success": True,
                    "execution_result_id": execution_result_id,
                    "defect_url": defect_url,
                    "oslc_defect_url": oslc_defect_url,
                    "proxy_backlink_updated": proxy_updated,
                    "message": "Defect linked to execution result successfully",
                    "_debug": _dbg,
                }
            )
        except Exception as e:
            return handle_error("link_defect_to_execution_result", e)
