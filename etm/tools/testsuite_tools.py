"""ETM Test Suite Tools — MCP tools for test suite CRUD operations."""

from typing import Annotated, Optional

from core.config import CONFIG_CONTEXT_DESC, PROJECT_AREA_DESC
from pydantic import Field
from services.etm_client import generic_create, generic_delete, generic_update


class TestSuiteTools:
    """ETM TestSuite tools methods."""

    def create_test_suite(
        self,
        title: Annotated[str, Field(description="Title of the new test suite.")],
        description: Annotated[str, Field(description="Description of the new test suite.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Create a new test suite."""
        return generic_create(
            "testsuite", title, description, project_area, configuration_context=configuration_context
        )

    def update_test_suite(
        self,
        test_suite_id: Annotated[
            str, Field(description="Numeric webId of the test suite (e.g., '7423'), NOT a slug identifier.")
        ],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        title: Annotated[
            Optional[str], Field(description="New title for the test suite. Omit to keep unchanged.")
        ] = None,
        description: Annotated[
            Optional[str], Field(description="New description for the test suite. Omit to keep unchanged.")
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Update an existing test suite's title and/or description."""
        updates = {k: v for k, v in {"title": title, "description": description}.items() if v is not None}
        return generic_update(
            "testsuite",
            test_suite_id,
            project_area,
            configuration_context=configuration_context,
            **updates,
        )

    def delete_test_suite(
        self,
        test_suite_id: Annotated[str, Field(description="Numeric webId of the test suite to delete.")],
        project_area: Annotated[
            Optional[str],
            Field(description=PROJECT_AREA_DESC),
        ] = None,
        configuration_context: Annotated[
            Optional[str],
            Field(description=CONFIG_CONTEXT_DESC),
        ] = None,
    ) -> str:
        """Delete a test suite. DESTRUCTIVE — cannot be undone."""
        return generic_delete("testsuite", test_suite_id, project_area, configuration_context=configuration_context)
