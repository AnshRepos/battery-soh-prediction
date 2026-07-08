"""ETM Misc Tools -- MCP tools for scripts, build records, configurations, and execution records."""

from typing import Annotated, Any, Optional
from xml.sax.saxutils import escape

from core.config import CONFIG_CONTEXT_DESC, LIMIT_DESC, PROJECT_AREA_DESC
from pydantic import Field
from services.etm_client import generic_create, generic_get, generic_list


class MiscTools:
    """ETM Misc tools methods."""

    def list_test_scripts(
        self,
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        limit: Annotated[int, Field(description=LIMIT_DESC, ge=1, le=200)] = 50,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """List test scripts (manual or automated step definitions)."""
        return generic_list("testscript", project_area, limit, configuration_context=configuration_context)

    def get_test_script(
        self,
        test_script_id: Annotated[str, Field(description="Numeric test script ID.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get detailed information about a specific test script."""
        return generic_get("testscript", test_script_id, project_area, configuration_context=configuration_context)

    def create_test_script(
        self,
        title: Annotated[str, Field(description="Title of the test script.")],
        description: Annotated[str, Field(description="Description of the test script.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        steps: Annotated[
            Optional[str],
            Field(description="Optional test steps as plain text."),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Create a new manual test script."""
        extra: dict[str, Any] = {"scripttype": "com.ibm.rqm.planning.common.scripttype.manual"}
        if steps:
            extra["steps"] = f"<div xmlns='http://www.w3.org/1999/xhtml'>{escape(str(steps))}</div>"
        return generic_create(
            "testscript",
            title,
            description,
            project_area,
            configuration_context=configuration_context,
            **extra,
        )

    def list_build_records(
        self,
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        limit: Annotated[int, Field(description=LIMIT_DESC, ge=1, le=200)] = 50,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """List build records."""
        return generic_list("buildrecord", project_area, limit, configuration_context=configuration_context)

    def get_build_record(
        self,
        build_id: Annotated[str, Field(description="Numeric build record ID.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get build record information."""
        return generic_get("buildrecord", build_id, project_area, configuration_context=configuration_context)

    def list_test_execution_records(
        self,
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        limit: Annotated[int, Field(description=LIMIT_DESC, ge=1, le=200)] = 50,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """List Test Case Execution Records (TCERs). Not execution results (pass/fail)."""
        return generic_list("executionworkitem", project_area, limit, configuration_context=configuration_context)

    def get_test_execution_record(
        self,
        test_record_id: Annotated[str, Field(description="Numeric Test Case Execution Record (TCER) ID.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Get details of a specific Test Case Execution Record (TCER). Not an execution result."""
        return generic_get(
            "executionworkitem", test_record_id, project_area, configuration_context=configuration_context
        )
