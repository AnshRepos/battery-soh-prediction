"""ETM Traceability Tools -- MCP tools for test plan trees, timelines, requirement mapping, and orphan detection."""

import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Annotated, Any, Optional

from core.config import CONFIG_CONTEXT_DESC, ETM_NAMESPACE, ETM_PROJECT_AREA, PROJECT_AREA_DESC
from pydantic import Field
from services.etm_client import (
    build_resource_url,
    collect_paginated_entries,
    fetch_all_pages,
    handle_error,
    make_request,
    project_area_required_error,
)

logger = logging.getLogger(__name__)


class TraceabilityTools:
    """ETM Traceability tools methods."""

    def get_test_plan_tree(
        self,
        test_plan_id: Annotated[str, Field(description="Numeric webId of the test plan.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get complete test plan hierarchy: child plans, suites, cases, and scripts."""
        try:
            if not test_plan_id:
                return json.dumps({"error": "test_plan_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            # Get test plan details
            plan_response = make_request(
                build_resource_url(project, "testplan", test_plan_id),
                accept_type="application/xml",
                configuration_context=configuration_context,
            )
            plan_root = ET.fromstring(plan_response.text)

            ns = {"qm": ETM_NAMESPACE, "dc": "http://purl.org/dc/elements/1.1/"}

            title_elem = plan_root.find(".//dc:title", ns)
            plan_title = title_elem.text if title_elem is not None else "Unknown"

            tree: dict[str, Any] = {
                "test_plan": {
                    "id": test_plan_id,
                    "title": plan_title,
                    "child_plans": [],
                    "test_suites": [],
                    "direct_test_cases": [],
                }
            }

            # Process child test plans (from <qm:childplan> elements)
            for childplan_elem in plan_root.findall(".//qm:childplan", ns):
                child_href = childplan_elem.get("href", "")
                if not child_href:
                    continue

                child_id = child_href.split(":")[-1] if ":" in child_href else child_href.split("/")[-1]
                try:
                    child_response = make_request(
                        build_resource_url(project, "testplan", child_id),
                        accept_type="application/xml",
                        configuration_context=configuration_context,
                    )
                    child_root = ET.fromstring(child_response.text)

                    child_title_elem = child_root.find(".//dc:title", ns)
                    child_webid_elem = child_root.find(f".//{{{ETM_NAMESPACE}}}webId")
                    child_data: dict[str, Any] = {
                        "id": child_webid_elem.text if child_webid_elem is not None else child_id,
                        "title": child_title_elem.text if child_title_elem is not None else "Unknown",
                        "href": child_href,
                    }
                    tree["test_plan"]["child_plans"].append(child_data)
                except Exception as child_err:
                    logger.warning(f"Could not fetch child plan {child_id}: {child_err}")
                    tree["test_plan"]["child_plans"].append(
                        {"id": child_id, "title": "Unknown (fetch failed)", "href": child_href}
                    )

            # Process test suites
            for testsuite_elem in plan_root.findall(".//qm:testsuite", ns):
                suite_href = testsuite_elem.get("href", "")
                if not suite_href:
                    continue

                suite_id = suite_href.split(":")[-1] if ":" in suite_href else suite_href.split("/")[-1]
                suite_response = make_request(
                    build_resource_url(project, "testsuite", suite_id),
                    accept_type="application/xml",
                    configuration_context=configuration_context,
                )
                suite_root = ET.fromstring(suite_response.text)

                suite_title_elem = suite_root.find(".//dc:title", ns)
                suite_data: dict[str, Any] = {
                    "id": suite_id,
                    "title": suite_title_elem.text if suite_title_elem is not None else "Unknown",
                    "test_cases": [],
                }

                # Process test cases in suite
                for testcase_elem in suite_root.findall(".//qm:testcase", ns):
                    case_href = testcase_elem.get("href", "")
                    if not case_href:
                        continue

                    case_id = case_href.split(":")[-1] if ":" in case_href else case_href.split("/")[-1]
                    case_response = make_request(
                        build_resource_url(project, "testcase", case_id),
                        accept_type="application/xml",
                        configuration_context=configuration_context,
                    )
                    case_root = ET.fromstring(case_response.text)

                    case_title_elem = case_root.find(".//dc:title", ns)
                    case_data = {
                        "id": case_id,
                        "title": case_title_elem.text if case_title_elem is not None else "Unknown",
                        "test_scripts": [
                            {"id": script_elem.get("href", "").split(":")[-1]}
                            for script_elem in case_root.findall(".//qm:testscript", ns)
                            if script_elem.get("href")
                        ],
                    }

                    suite_data["test_cases"].append(case_data)

                tree["test_plan"]["test_suites"].append(suite_data)

            # Process test cases directly linked to the test plan (not through suites)
            for testcase_elem in plan_root.findall(".//qm:testcase", ns):
                case_href = testcase_elem.get("href", "")
                if not case_href:
                    continue

                case_id = case_href.split(":")[-1] if ":" in case_href else case_href.split("/")[-1]
                case_response = make_request(
                    build_resource_url(project, "testcase", case_id),
                    accept_type="application/xml",
                    configuration_context=configuration_context,
                )
                case_root = ET.fromstring(case_response.text)

                case_title_elem = case_root.find(".//dc:title", ns)
                case_data = {
                    "id": case_id,
                    "title": case_title_elem.text if case_title_elem is not None else "Unknown",
                    "test_scripts": [
                        {"id": script_elem.get("href", "").split(":")[-1]}
                        for script_elem in case_root.findall(".//qm:testscript", ns)
                        if script_elem.get("href")
                    ],
                }

                tree["test_plan"]["direct_test_cases"].append(case_data)

            # Calculate statistics
            total_child_plans = len(tree["test_plan"]["child_plans"])
            total_suites = len(tree["test_plan"]["test_suites"])
            suite_cases = sum(len(suite["test_cases"]) for suite in tree["test_plan"]["test_suites"])
            direct_cases = len(tree["test_plan"]["direct_test_cases"])
            suite_scripts = sum(
                len(case["test_scripts"]) for suite in tree["test_plan"]["test_suites"] for case in suite["test_cases"]
            )
            direct_scripts = sum(len(case["test_scripts"]) for case in tree["test_plan"]["direct_test_cases"])

            tree["statistics"] = {
                "total_child_plans": total_child_plans,
                "total_suites": total_suites,
                "total_cases_in_suites": suite_cases,
                "total_direct_test_cases": direct_cases,
                "total_cases": suite_cases + direct_cases,
                "total_scripts": suite_scripts + direct_scripts,
            }

            return json.dumps(tree, indent=2)
        except Exception as e:
            return handle_error("get_test_plan_tree", e)

    def get_execution_timeline(
        self,
        test_plan_id: Annotated[str, Field(description="Numeric webId of the test plan.")],
        days_back: Annotated[
            int, Field(description="Number of days back for trend analysis (1-365).", ge=1, le=365)
        ] = 30,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get execution results over time for trend analysis."""
        try:
            if not test_plan_id:
                return json.dumps({"error": "test_plan_id is required"})
            if not (1 <= days_back <= 365):
                return json.dumps({"error": "days_back must be between 1 and 365"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime("%Y-%m-%d")

            # Get execution results via paginated Atom feed
            endpoint = build_resource_url(project, "executionresult")
            root = fetch_all_pages(endpoint, {"abbreviate": "false"}, page_size=200, timeout=300)

            ns = {"atom": "http://www.w3.org/2005/Atom", "ns2": ETM_NAMESPACE}

            daily_stats = {}

            for entry in root.findall(".//atom:entry", ns):
                exec_result = entry.find(".//ns2:executionresult", ns)
                if exec_result is None:
                    continue

                # Filter by test plan
                tp_elem = exec_result.find(".//ns2:testplan", ns)
                if tp_elem is None or test_plan_id not in tp_elem.get("href", ""):
                    continue

                # Get execution date
                updated_elem = exec_result.find(".//ns2:updated", ns)
                if updated_elem is None or not updated_elem.text:
                    continue

                exec_date = updated_elem.text.split("T")[0]
                if exec_date < start_date_str:
                    continue

                # Initialize stats for date
                if exec_date not in daily_stats:
                    daily_stats[exec_date] = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "blocked": 0,
                        "incomplete": 0,
                    }

                daily_stats[exec_date]["total"] += 1

                # Categorize by state
                state_elem = exec_result.find(".//ns2:state", ns)
                if state_elem is not None:
                    state = (state_elem.text or "").lower()
                    if "passed" in state:
                        daily_stats[exec_date]["passed"] += 1
                    elif "failed" in state:
                        daily_stats[exec_date]["failed"] += 1
                    elif "blocked" in state:
                        daily_stats[exec_date]["blocked"] += 1
                    else:
                        daily_stats[exec_date]["incomplete"] += 1

            # Build timeline with missing days filled
            timeline = []
            current_date = start_date
            total_executions = total_passed = 0

            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")

                if date_str in daily_stats:
                    day_data = daily_stats[date_str]
                    pass_rate = (day_data["passed"] / day_data["total"] * 100) if day_data["total"] > 0 else 0
                else:
                    day_data = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "blocked": 0,
                        "incomplete": 0,
                    }
                    pass_rate = 0

                timeline.append(
                    {
                        "date": date_str,
                        "executions": day_data["total"],
                        "passed": day_data["passed"],
                        "failed": day_data["failed"],
                        "blocked": day_data["blocked"],
                        "incomplete": day_data["incomplete"],
                        "pass_rate": round(pass_rate, 2),
                    }
                )

                total_executions += day_data["total"]
                total_passed += day_data["passed"]
                current_date += timedelta(days=1)

            overall_pass_rate = (total_passed / total_executions * 100) if total_executions > 0 else 0

            return json.dumps(
                {
                    "success": True,
                    "test_plan_id": test_plan_id,
                    "period": f"{days_back} days",
                    "summary": {
                        "total_executions": total_executions,
                        "overall_pass_rate": round(overall_pass_rate, 2),
                    },
                    "timeline": timeline,
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_execution_timeline", e)

    def get_requirement_to_test_mapping(
        self,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get complete requirements → test cases traceability matrix."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "testcase")
            entries = collect_paginated_entries(
                endpoint,
                "testcase",
                params={"abbreviate": "false"},
                timeout=180,
                configuration_context=configuration_context,
            )

            requirement_mapping: dict[str, dict[str, Any]] = {}
            orphaned_test_cases = []

            for entry in entries:
                tc_id = str(entry.get("identifier") or entry.get("webId") or "unknown")
                tc_title = str(entry.get("title") or "Unknown")

                test_case_data = {"id": tc_id, "title": tc_title}

                # Find requirement links
                validates = entry.get("validates")
                if isinstance(validates, list):
                    requirement_links = [str(v) for v in validates if v]
                elif validates:
                    requirement_links = [str(validates)]
                else:
                    requirement_links = []

                if requirement_links:
                    for req_href in requirement_links:
                        req_id = req_href.split("/")[-1] if "/" in req_href else req_href
                        if req_id not in requirement_mapping:
                            requirement_mapping[req_id] = {
                                "requirement_id": req_id,
                                "test_cases": [],
                                "coverage_count": 0,
                            }

                        requirement_mapping[req_id]["test_cases"].append(test_case_data)
                        requirement_mapping[req_id]["coverage_count"] += 1
                else:
                    orphaned_test_cases.append(test_case_data)

            requirements = sorted(requirement_mapping.values(), key=lambda x: x["coverage_count"], reverse=True)

            coverage_analysis = {
                "total_requirements": len(requirements),
                "orphaned_test_cases": len(orphaned_test_cases),
                "over_tested_requirements": len([req for req in requirements if req["coverage_count"] > 3]),
            }

            return json.dumps(
                {
                    "success": True,
                    "project_area": project,
                    "coverage_analysis": coverage_analysis,
                    "requirements": requirements[:20],
                    "orphaned_test_cases": orphaned_test_cases[:10],
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("get_requirement_to_test_mapping", e)

    def find_orphaned_test_cases(
        self,
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Find test cases not linked to any requirements or test plans."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            testcase_entries = collect_paginated_entries(
                build_resource_url(project, "testcase"),
                "testcase",
                params={"abbreviate": "false"},
                timeout=180,
                configuration_context=configuration_context,
            )
            testplan_entries = collect_paginated_entries(
                build_resource_url(project, "testplan"),
                "testplan",
                params={"abbreviate": "false"},
                timeout=180,
                configuration_context=configuration_context,
            )

            all_test_cases = {}

            for entry in testcase_entries:
                tc_id = entry.get("identifier") or entry.get("webId")
                if not tc_id:
                    continue

                title = str(entry.get("title") or "Unknown")
                has_requirements = bool(entry.get("validates"))

                all_test_cases[tc_id] = {
                    "id": tc_id,
                    "title": title,
                    "has_requirements": has_requirements,
                    "in_test_plans": [],
                }

            # Check test plan references
            for entry in testplan_entries:
                testcase_refs = entry.get("testcase")
                refs: list[str] = []
                if isinstance(testcase_refs, list):
                    refs = [str(ref) for ref in testcase_refs if ref]
                elif testcase_refs:
                    refs = [str(testcase_refs)]

                for href in refs:
                    referenced_tc_id = href.split(":")[-1] if ":" in href else href.split("/")[-1]
                    if referenced_tc_id in all_test_cases:
                        all_test_cases[referenced_tc_id]["in_test_plans"].append({"href": href})

            # Categorize orphans
            orphaned_categories: dict[str, list[Any]] = {
                "no_requirements": [],
                "no_test_plans": [],
                "completely_isolated": [],
            }

            for tc_data in all_test_cases.values():
                if not tc_data["has_requirements"]:
                    orphaned_categories["no_requirements"].append(tc_data)
                if not tc_data["in_test_plans"]:
                    orphaned_categories["no_test_plans"].append(tc_data)
                if not tc_data["has_requirements"] and not tc_data["in_test_plans"]:
                    orphaned_categories["completely_isolated"].append(tc_data)

            statistics = {
                "total_test_cases": len(all_test_cases),
                "no_requirements_count": len(orphaned_categories["no_requirements"]),
                "no_test_plans_count": len(orphaned_categories["no_test_plans"]),
                "completely_isolated_count": len(orphaned_categories["completely_isolated"]),
                "orphan_percentage": (
                    round((len(orphaned_categories["completely_isolated"]) / len(all_test_cases) * 100), 2)
                    if all_test_cases
                    else 0
                ),
            }

            return json.dumps(
                {
                    "success": True,
                    "project_area": project,
                    "statistics": statistics,
                    "orphaned_categories": {
                        "completely_isolated": orphaned_categories["completely_isolated"][:10],  # Most critical
                        "no_requirements": orphaned_categories["no_requirements"][:15],
                        "no_test_plans": orphaned_categories["no_test_plans"][:15],
                    },
                    "recommendations": {
                        "high_priority": "Review completely isolated test cases - they may be obsolete",
                        "medium_priority": "Add requirement traceability to test cases without links",
                        "low_priority": "Organize test cases into appropriate test plans",
                    },
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("find_orphaned_test_cases", e)

    def get_execution_results_by_test_plan(
        self,
        test_plan_id: str,
        project_area: Optional[str] = None,
        configuration_context: Optional[str] = None,
    ) -> str:
        """Get all execution results for a specific test plan."""
        try:
            if not test_plan_id:
                return json.dumps({"error": "test_plan_id is required"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            endpoint = build_resource_url(project, "executionresult")

            # Fetch all execution results via paginated feed; filter by test plan client-side
            root = fetch_all_pages(endpoint, {"abbreviate": "false"}, page_size=200, timeout=300)
            ns = {"atom": "http://www.w3.org/2005/Atom", "ns2": ETM_NAMESPACE}

            # Remove entries that don't match the test plan
            entries = root.findall(".//atom:entry", ns)
            matched_entries = []

            for entry in entries:
                exec_result = entry.find(".//ns2:executionresult", ns)
                if exec_result is None:
                    continue

                # Check if belongs to test plan
                tp_elem = exec_result.find(".//ns2:testplan", ns)
                if tp_elem is not None:
                    href = tp_elem.get("href", "")
                    if test_plan_id in href:
                        matched_entries.append(entry)

            # Remove all entries and add only matched ones
            for entry in entries:
                root.remove(entry)
            for entry in matched_entries:
                root.append(entry)

            # Update count
            total_results = root.find(".//atom:totalResults", ns)
            if total_results is not None:
                total_results.text = str(len(matched_entries))

            filtered_xml = ET.tostring(root, encoding="unicode")
            return filtered_xml

        except Exception as e:
            return handle_error("get_execution_results_by_test_plan", e)
