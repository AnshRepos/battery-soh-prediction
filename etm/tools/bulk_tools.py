"""ETM Bulk Tools -- MCP tools for batch test case creation and execution."""

import json
import logging
import time
from typing import Annotated, Any, Optional
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
    generic_create,
    handle_error,
    make_request,
    project_area_required_error,
    resolve_to_web_id,
)
from services.xml_helpers import create_xml_resource

logger = logging.getLogger(__name__)


def _create_single_execution_record(
    test_case_id: str,
    result: str,
    project: str,
    test_plan_id: Optional[str] = None,
    executed_by: Optional[str] = None,
    comments: Optional[str] = None,
    configuration_context: Optional[str] = None,
) -> str:
    """Create a single execution record (TCER + Execution Result).

    Replicates the logic of the create_execution_record tool for use in bulk
    operations without depending on the tool function directly.
    """
    try:
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
        return handle_error("_create_single_execution_record", e)


class BulkTools:
    """ETM Bulk tools methods."""

    def bulk_create_test_cases(
        self,
        test_cases_data: Annotated[
            list[dict[str, Any]],
            Field(description="List of dicts, each with at least 'title' key and optional 'description'."),
        ],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Create multiple test cases in batch."""
        try:
            if not test_cases_data or not isinstance(test_cases_data, list):
                return json.dumps({"error": "test_cases_data must be a non-empty list"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            results: dict[str, list[Any]] = {"success": [], "failed": []}

            for i, tc_data in enumerate(test_cases_data):
                try:
                    if "title" not in tc_data:
                        results["failed"].append({"index": i, "error": "Missing title"})
                        continue

                    title = tc_data["title"]
                    description = tc_data.get("description", "")

                    result = generic_create(
                        "testcase",
                        title,
                        description,
                        project,
                        configuration_context=configuration_context,
                    )
                    result_data = json.loads(result)

                    if result_data.get("success"):
                        results["success"].append(
                            {
                                "index": i,
                                "title": title,
                                "test_case_id": result_data.get("testcase_id"),
                            }
                        )
                    else:
                        results["failed"].append(
                            {
                                "index": i,
                                "title": title,
                                "error": result_data.get("error", "Unknown error"),
                            }
                        )

                except Exception as e:
                    results["failed"].append({"index": i, "error": str(e)})

            return json.dumps(
                {
                    "success": True,
                    "total_requested": len(test_cases_data),
                    "created": len(results["success"]),
                    "failed": len(results["failed"]),
                    "results": results,
                },
                indent=2,
            )

        except Exception as e:
            return handle_error("bulk_create_test_cases", e)

    def bulk_execute_tests(
        self,
        execution_requests: Annotated[
            list[dict[str, Any]],
            Field(
                description="List of dicts, each with 'test_case_id' and 'result'. Optional: 'test_plan_id', 'executed_by', 'comments'."
            ),
        ],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Execute multiple tests in batch."""
        try:
            if not execution_requests or not isinstance(execution_requests, list):
                return json.dumps({"error": "execution_requests must be a non-empty list"})

            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()
            results: dict[str, list[Any]] = {"success": [], "failed": []}

            for i, exec_data in enumerate(execution_requests):
                try:
                    if "test_case_id" not in exec_data or "result" not in exec_data:
                        results["failed"].append({"index": i, "error": "Missing test_case_id or result"})
                        continue

                    test_case_id = exec_data["test_case_id"]
                    result = exec_data["result"]
                    test_plan_id = exec_data.get("test_plan_id")
                    executed_by = exec_data.get("executed_by")
                    comments = exec_data.get("comments")

                    exec_result = _create_single_execution_record(
                        test_case_id,
                        result,
                        project,
                        test_plan_id,
                        executed_by,
                        comments,
                        configuration_context=configuration_context,
                    )
                    exec_result_data = json.loads(exec_result)

                    if exec_result_data.get("success"):
                        results["success"].append(
                            {
                                "index": i,
                                "test_case_id": test_case_id,
                                "result": result,
                                "execution_result_id": exec_result_data.get("execution_result_id"),
                            }
                        )
                    else:
                        results["failed"].append(
                            {
                                "index": i,
                                "test_case_id": test_case_id,
                                "error": exec_result_data.get("error", "Unknown error"),
                            }
                        )

                except Exception as e:
                    results["failed"].append({"index": i, "error": str(e)})

            return json.dumps(
                {
                    "success": True,
                    "total_requested": len(execution_requests),
                    "executed": len(results["success"]),
                    "failed": len(results["failed"]),
                    "results": results,
                },
                indent=2,
            )

        except Exception as e:
            return handle_error("bulk_execute_tests", e)
