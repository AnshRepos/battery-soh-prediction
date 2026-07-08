"""ETM Test Plan Tools — MCP tools for test plan CRUD and statistics."""

import json
import logging
from datetime import datetime, timedelta
from typing import Annotated, Any, Optional

from core.config import CONFIG_CONTEXT_DESC, ETM_PROJECT_AREA, PROJECT_AREA_DESC
from pydantic import Field
from services.etm_client import (
    build_category_href,
    build_resource_url,
    collect_paginated_entries,
    extract_resource_id,
    generic_delete,
    generic_update,
    handle_error,
    make_request,
    project_area_required_error,
)
from services.xml_helpers import classify_execution_state, create_xml_resource

logger = logging.getLogger(__name__)


class TestPlanTools:
    """ETM TestPlan tools methods."""

    def create_test_plan(
        self,
        title: Annotated[str, Field(description="Name of the test plan.")],
        description: Annotated[str, Field(description="Description of the test plan.")],
        release: Annotated[
            str, Field(description="Release category value (e.g., 'Release 1.0'). Must match an existing value in ETM.")
        ],
        test_level: Annotated[
            str,
            Field(
                description="Test Level category value (e.g., 'Integration Test'). Must match an existing value in ETM."
            ),
        ],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        start_date: Annotated[
            Optional[str], Field(description="Start date in ISO format (e.g., '2024-06-01').")
        ] = None,
        end_date: Annotated[Optional[str], Field(description="End date in ISO format (e.g., '2024-12-31').")] = None,
        owner: Annotated[Optional[str], Field(description="Owner username.")] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Create a new test plan."""
        try:
            project = (project_area or ETM_PROJECT_AREA or "").strip()
            if not project:
                return project_area_required_error()

            categories: list[dict[str, str]] = [
                {
                    "term": "Release",
                    "value": release,
                    "href": build_category_href(project, "Release", release),
                },
                {
                    "term": "Test-Level",
                    "value": test_level,
                    "href": build_category_href(project, "Test Level", test_level),
                },
            ]

            endpoint = build_resource_url(project, "testplan")
            xml_payload = create_xml_resource(
                "testplan",
                title,
                description,
                categories=categories,
                startdate=start_date,
                enddate=end_date,
                owner=owner,
            )
            logger.info(f"Creating testplan: '{title}' with release='{release}', test_level='{test_level}'")

            response = make_request(
                endpoint,
                method="POST",
                data=xml_payload.encode("utf-8"),
                accept_type="application/xml",
                content_type="application/rdf+xml",
                timeout=60,
                configuration_context=configuration_context,
            )

            resource_id = extract_resource_id(response, "testplan")
            location = response.headers.get("Location", "")

            result: dict[str, Any] = {
                "success": True,
                "testplan_id": resource_id,
                "location": location,
                "message": (
                    f"Test plan '{title}' created successfully. "
                    "Use oslc_query_resources with "
                    f"where='dcterms:title=\"{title}\"' and "
                    "select='dcterms:title,oslc:shortId' to retrieve "
                    "the numeric webId."
                ),
            }

            return json.dumps(result)
        except Exception as e:
            return handle_error("create_test_plan", e)

    def update_test_plan(
        self,
        test_plan_id: Annotated[str, Field(description="Numeric webId (e.g., '105520'), NOT a slug identifier.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        title: Annotated[Optional[str], Field(description="New title. Omit to keep current.")] = None,
        description: Annotated[Optional[str], Field(description="New description. Omit to keep current.")] = None,
        start_date: Annotated[Optional[str], Field(description="New start date in ISO format.")] = None,
        end_date: Annotated[Optional[str], Field(description="New end date in ISO format.")] = None,
        owner: Annotated[Optional[str], Field(description="New owner username.")] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Update an existing test plan."""
        updates = {
            k: v
            for k, v in {
                "title": title,
                "description": description,
                "startdate": start_date,
                "enddate": end_date,
                "owner": owner,
            }.items()
            if v is not None
        }
        return generic_update(
            "testplan",
            test_plan_id,
            project_area,
            configuration_context=configuration_context,
            **updates,
        )

    def delete_test_plan(
        self,
        test_plan_id: Annotated[str, Field(description="Numeric webId of the test plan to delete.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Delete a test plan. DESTRUCTIVE — cannot be undone."""
        return generic_delete("testplan", test_plan_id, project_area, configuration_context=configuration_context)

    def get_test_plan_statistics(
        self,
        test_plan_id: Annotated[str, Field(description="Numeric webId of the test plan to analyze.")],
        project_area: Annotated[Optional[str], Field(description=PROJECT_AREA_DESC)] = None,
        mode: Annotated[
            str, Field(description="One of: 'statistics' (pass rate), 'timeline' (daily trend), 'raw' (full results).")
        ] = "statistics",
        days_back: Annotated[
            int, Field(description="Number of days back for timeline mode (1-365).", ge=1, le=365)
        ] = 30,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get execution analysis for a test plan."""
        try:
            if not test_plan_id:
                return json.dumps({"error": "test_plan_id is required"})
            if mode not in {"statistics", "timeline", "raw"}:
                return json.dumps({"error": "mode must be one of: statistics, timeline, raw"})
            if mode == "timeline" and not (1 <= days_back <= 365):
                return json.dumps({"error": "days_back must be between 1 and 365"})

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

            matched_entries: list[dict[str, Any]] = []
            for entry in entries:
                testplan_ref = entry.get("testplan", "")
                if isinstance(testplan_ref, list):
                    if any(test_plan_id in ref for ref in testplan_ref):
                        matched_entries.append(entry)
                elif test_plan_id in str(testplan_ref):
                    matched_entries.append(entry)

            if mode == "raw":
                return json.dumps({"count": len(matched_entries), "executionresults": matched_entries}, indent=2)

            if mode == "timeline":
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                start_date_str = start_date.strftime("%Y-%m-%d")

                daily_stats: dict[str, dict[str, int]] = {}

                for entry in matched_entries:
                    updated = str(entry.get("updated", ""))
                    if not updated:
                        continue

                    exec_date = updated.split("T")[0]
                    if exec_date < start_date_str:
                        continue

                    if exec_date not in daily_stats:
                        daily_stats[exec_date] = {"total": 0, "passed": 0, "failed": 0, "blocked": 0, "incomplete": 0}

                    daily_stats[exec_date]["total"] += 1
                    bucket = classify_execution_state(str(entry.get("state", "")))
                    daily_stats[exec_date][bucket] += 1

                timeline = []
                current_date = start_date
                total_executions = total_passed = 0

                while current_date <= end_date:
                    date_str = current_date.strftime("%Y-%m-%d")

                    if date_str in daily_stats:
                        day_data = daily_stats[date_str]
                        pass_rate = (day_data["passed"] / day_data["total"] * 100) if day_data["total"] > 0 else 0
                    else:
                        day_data = {"total": 0, "passed": 0, "failed": 0, "blocked": 0, "incomplete": 0}
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
                        "mode": "timeline",
                        "period": f"{days_back} days",
                        "summary": {
                            "total_executions": total_executions,
                            "overall_pass_rate": round(overall_pass_rate, 2),
                        },
                        "timeline": timeline,
                    },
                    indent=2,
                )

            stats: dict[str, int | float] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "blocked": 0,
                "incomplete": 0,
            }

            for entry in matched_entries:
                stats["total"] += 1
                bucket = classify_execution_state(str(entry.get("state", "")))
                stats[bucket] += 1

            pass_rate = round((stats["passed"] / stats["total"]) * 100, 2) if stats["total"] > 0 else 0.0
            stats["pass_rate"] = pass_rate

            return json.dumps(
                {"success": True, "test_plan_id": test_plan_id, "mode": "statistics", "statistics": stats},
                indent=2,
            )
        except Exception as e:
            return handle_error("get_test_plan_statistics", e)
