"""
ETM Connection & Utility Tools

MCP tools for testing connections, listing project areas,
querying resources via OSLC, and generic resource access.
"""

import json
import xml.etree.ElementTree as ET
from typing import Annotated, Optional

from core.config import (
    CONFIG_CONTEXT_DESC,
    LISTABLE_RESOURCE_TYPES,
    OSLC_QM_RESOURCE_TYPES,
    PROJECT_AREA_DESC,
)
from pydantic import Field
from services.etm_client import (
    build_resource_url,
    generic_get,
    handle_error,
    make_request,
    project_area_required_error,
)
from services.oslc import (
    discover_component_configurations,
    discover_components_via_feed,
    oslc_query,
)


class ConnectionTools:
    """ETM Connection tools methods."""

    def test_project_connection(
        self,
        project_area: Annotated[
            str,
            Field(
                description="Project area NAME to test (e.g., 'My Project (qm)'). Use list_project_areas() to discover names."
            ),
        ],
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Test connection to a specific ETM project area."""
        try:
            if not project_area.strip():
                return project_area_required_error()

            endpoint = build_resource_url(project_area, "testplan")
            make_request(endpoint, params={"abbreviate": "false"}, configuration_context=configuration_context)

            return json.dumps(
                {
                    "success": True,
                    "project_area": project_area,
                    "message": f"✓ Successfully connected to project '{project_area}'",
                }
            )
        except Exception as e:
            return handle_error("test_project_connection", e)

    def list_project_areas(
        self,
        configuration_context: Annotated[
            Optional[str],
            Field(
                description="CM stream URI for CM-enabled projects. Usually not needed for this tool. Omit unless you already have one."
            ),
        ] = None,
    ) -> str:
        """List all available ETM project areas. START HERE to discover projects."""
        try:
            response = make_request(
                "/process/project-areas",
                accept_type="application/xml",
                configuration_context=configuration_context,
            )
            root = ET.fromstring(response.text)

            ns = {"jp06": "http://jazz.net/xmlns/prod/jazz/process/0.6/"}
            project_areas: list[dict[str, str]] = []

            for pa in root.findall(".//jp06:project-area", ns):
                name = pa.get(f"{{{ns['jp06']}}}name", "")
                url_elem = pa.find("jp06:url", ns)

                entry: dict[str, str] = {"name": name}
                if url_elem is not None and url_elem.text and url_elem.text.strip():
                    entry["url"] = url_elem.text.strip()
                    # Derive project_area_uri from the URL
                    pa_url = url_elem.text.strip()
                    if "/process/project-areas/" in pa_url:
                        entry["project_area_uri"] = pa_url
                project_areas.append(entry)

            return json.dumps(
                {
                    "count": len(project_areas),
                    "project_areas": project_areas,
                    "next_step": (
                        "Use a project's 'name' as the project_area parameter in tools like "
                        "oslc_query_resources(), list_test_cases(), create_test_case(), etc. "
                        "For CM-enabled projects, use 'project_area_uri' with "
                        "list_project_components() -> list_cm_configurations() to get a configuration_context."
                    ),
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("list_project_areas", e)

    def list_project_components(
        self,
        project_area_uri: Annotated[
            str,
            Field(
                description="Project area URI from list_project_areas() (e.g., 'https://server/qm/process/project-areas/<uuid>'). NOT a project name."
            ),
        ],
    ) -> str:
        """List CM components in a project area. Next step: list_cm_configurations()."""
        if not project_area_uri or not project_area_uri.strip():
            return json.dumps({"error": "project_area_uri is required. Call list_project_areas() first."})

        project_area_uri = project_area_uri.strip()
        if "/process/project-areas/" not in project_area_uri:
            return json.dumps(
                {
                    "error": f"Invalid project_area_uri format: '{project_area_uri}'. "
                    "Expected: https://server/qm/process/project-areas/<uuid>. "
                    "Call list_project_areas() to get the correct URI."
                }
            )

        try:
            components = discover_components_via_feed(project_area_uri)

            if not components:
                return json.dumps(
                    {
                        "project_area_uri": project_area_uri,
                        "total_components": 0,
                        "components": [],
                        "info": "No CM components found. This project may not use "
                        "Configuration Management, so configuration_context is not needed.",
                    },
                    indent=2,
                )

            result: dict = {
                "project_area_uri": project_area_uri,
                "total_components": len(components),
                "components": components,
                "next_step": (
                    "Use list_cm_configurations(project_area_uri=...) to discover "
                    "all streams across components, or "
                    "list_cm_configurations(component_uri=...) for a specific component. "
                    "Then use a stream's configuration_context in get_test_case_details(), etc."
                ),
            }

            return json.dumps(result, indent=2)
        except Exception as e:
            return handle_error("list_project_components", e)

    def list_cm_configurations(
        self,
        component_uri: Annotated[
            Optional[str],
            Field(
                description="Component URI from list_project_components(). Lists configs for this component only. Provide this OR project_area_uri."
            ),
        ] = None,
        project_area_uri: Annotated[
            Optional[str],
            Field(
                description="Project area URI from list_project_areas(). Lists configs for ALL components. Provide this OR component_uri."
            ),
        ] = None,
    ) -> str:
        """List CM streams and baselines."""
        try:
            configurations = discover_component_configurations(
                component_uri=component_uri.strip() if component_uri else None,
                project_area_uri=project_area_uri.strip() if project_area_uri else None,
            )

            if not configurations:
                return json.dumps(
                    {
                        "component_uri": component_uri,
                        "project_area_uri": project_area_uri,
                        "total_configurations": 0,
                        "configurations": [],
                        "info": "No configurations found. The project may not use "
                        "Configuration Management, so configuration_context is not needed.",
                    },
                    indent=2,
                )

            streams = [c for c in configurations if c.get("type") == "stream"]
            baselines = [c for c in configurations if c.get("type") == "baseline"]

            return json.dumps(
                {
                    "component_uri": component_uri,
                    "project_area_uri": project_area_uri,
                    "total_configurations": len(configurations),
                    "streams": len(streams),
                    "baselines": len(baselines),
                    "configurations": configurations,
                    "next_step": (
                        "Use a stream's configuration_context value as the "
                        "configuration_context parameter in get_test_case_details(), "
                        "oslc_query_resources(), list_test_cases(), etc."
                    ),
                },
                indent=2,
            )
        except Exception as e:
            return handle_error("list_cm_configurations", e)

    def oslc_query_resources(
        self,
        resource_type: Annotated[
            str,
            Field(
                description="Type of resource to query. One of: testcase, testplan, testsuite, testscript, executionresult, executionworkitem."
            ),
        ],
        project_area: Annotated[
            str,
            Field(
                description="Project area NAME (e.g., 'My Project (qm)'). Use list_project_areas() to discover names."
            ),
        ],
        where: Annotated[
            Optional[str],
            Field(
                description=(
                    'OSLC where clause. Use oslc:shortId="28931" for ID lookup (NOT dcterms:identifier). '
                    'dcterms:title="Exact Title" for title search. String values MUST be in double quotes.'
                )
            ),
        ] = None,
        select: Annotated[
            Optional[str],
            Field(
                description="Comma-separated properties to return (e.g., 'dcterms:title,dcterms:identifier,dcterms:modified')."
            ),
        ] = None,
        limit: Annotated[int, Field(description="Maximum results (1-500, default 50).", ge=1, le=500)] = 50,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Query ETM resources using OSLC QM with server-side filtering. Preferred for finding resources by name/ID/date."""
        valid_types = list(OSLC_QM_RESOURCE_TYPES.keys())
        if resource_type not in valid_types:
            return json.dumps({"error": f"resource_type must be one of: {', '.join(valid_types)}"})
        if not (1 <= limit <= 500):
            return json.dumps({"error": "limit must be between 1 and 500"})

        return oslc_query(
            resource_type=resource_type,
            project_area=project_area,
            where=where,
            select=select,
            limit=limit,
            configuration_context=configuration_context,
        )

    def get_resource(
        self,
        resource_type: Annotated[
            str,
            Field(
                description="Type of resource. One of: testplan, testcase, testsuite, testscript, testphase, executionresult, executionworkitem, attachment, template, buildrecord, configuration."
            ),
        ],
        resource_id: Annotated[str, Field(description="Numeric webId (e.g., '3435411'), NOT a slug identifier.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get full details of any ETM resource by type and numeric webId.

        For testcase details, prefer get_test_case_details() instead (richer parsed output).
        """
        if resource_type not in LISTABLE_RESOURCE_TYPES:
            return json.dumps({"error": f"resource_type must be one of: {', '.join(sorted(LISTABLE_RESOURCE_TYPES))}"})
        return generic_get(resource_type, resource_id, project_area, configuration_context=configuration_context)
