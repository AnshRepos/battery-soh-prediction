"""Unit tests for tools.connection_tools.ConnectionTools.

All service-layer calls are mocked so no network I/O occurs.
Every tool method returns a JSON string; we parse with json.loads()
and assert on the resulting dict.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from tools.connection_tools import ConnectionTools


@pytest.fixture
def tools() -> ConnectionTools:
    """Return a fresh ConnectionTools instance for each test."""
    return ConnectionTools()


# ── test_project_connection ────────────────────────────────────────────────


class TestProjectConnection:
    """Tests for ConnectionTools.test_project_connection."""

    @patch("tools.connection_tools.make_request")
    @patch("tools.connection_tools.build_resource_url", return_value="/mocked/endpoint")
    def test_success(self, mock_build_url: MagicMock, mock_request: MagicMock, tools: ConnectionTools) -> None:
        """Successful connection returns success=True and the project_area."""
        mock_request.return_value = MagicMock(status_code=200)

        result = json.loads(tools.test_project_connection("MyProject"))

        assert result["success"] is True
        assert result["project_area"] == "MyProject"
        mock_build_url.assert_called_once_with("MyProject", "testplan")
        mock_request.assert_called_once()

    def test_empty_project_area_returns_error(self, tools: ConnectionTools) -> None:
        """An empty (whitespace-only) project_area produces an error."""
        result = json.loads(tools.test_project_connection("   "))

        assert "error" in result
        assert "required" in result["error"].lower()

    @patch("tools.connection_tools.make_request", side_effect=ConnectionError("timeout"))
    @patch("tools.connection_tools.build_resource_url", return_value="/endpoint")
    @patch(
        "tools.connection_tools.handle_error",
        return_value='{"error": "timeout", "function": "test_project_connection"}',
    )
    def test_exception_handled(
        self,
        mock_handle: MagicMock,
        mock_build_url: MagicMock,
        mock_request: MagicMock,
        tools: ConnectionTools,
    ) -> None:
        """Exceptions from make_request are forwarded to handle_error."""
        result = json.loads(tools.test_project_connection("Proj"))

        assert result["error"] == "timeout"
        mock_handle.assert_called_once()


# ── list_project_areas ─────────────────────────────────────────────────────


_PROJECT_AREAS_XML = (
    '<root xmlns:jp06="http://jazz.net/xmlns/prod/jazz/process/0.6/">'
    '  <jp06:project-area jp06:name="Project1">'
    "    <jp06:url>https://example.com/p1</jp06:url>"
    "  </jp06:project-area>"
    '  <jp06:project-area jp06:name="Project2">'
    "    <jp06:url>https://example.com/p2</jp06:url>"
    "  </jp06:project-area>"
    "</root>"
)


class TestListProjectAreas:
    """Tests for ConnectionTools.list_project_areas."""

    @patch("tools.connection_tools.make_request")
    def test_success_returns_two_projects(self, mock_request: MagicMock, tools: ConnectionTools) -> None:
        """Parses XML and returns correct count and names."""
        response = MagicMock()
        response.text = _PROJECT_AREAS_XML
        mock_request.return_value = response

        result = json.loads(tools.list_project_areas())

        assert result["count"] == 2
        names = [pa["name"] for pa in result["project_areas"]]
        assert names == ["Project1", "Project2"]
        assert result["project_areas"][0]["url"] == "https://example.com/p1"

    @patch("tools.connection_tools.make_request")
    def test_empty_feed_returns_zero(self, mock_request: MagicMock, tools: ConnectionTools) -> None:
        """An XML response with no project-area elements yields count 0."""
        response = MagicMock()
        response.text = '<root xmlns:jp06="http://jazz.net/xmlns/prod/jazz/process/0.6/"></root>'
        mock_request.return_value = response

        result = json.loads(tools.list_project_areas())

        assert result["count"] == 0
        assert result["project_areas"] == []

    @patch("tools.connection_tools.make_request", side_effect=RuntimeError("network"))
    @patch(
        "tools.connection_tools.handle_error",
        return_value='{"error": "network", "function": "list_project_areas"}',
    )
    def test_exception_handled(self, mock_handle: MagicMock, mock_request: MagicMock, tools: ConnectionTools) -> None:
        """Exceptions are forwarded to handle_error."""
        result = json.loads(tools.list_project_areas())

        assert result["error"] == "network"
        mock_handle.assert_called_once()


# ── oslc_query_resources ───────────────────────────────────────────────────


class TestOslcQueryResources:
    """Tests for ConnectionTools.oslc_query_resources."""

    def test_invalid_resource_type_returns_error(self, tools: ConnectionTools) -> None:
        """An unrecognised resource_type yields an error without calling oslc_query."""
        result = json.loads(tools.oslc_query_resources("bogus_type", "Proj"))

        assert "error" in result
        assert "resource_type" in result["error"]

    @pytest.mark.parametrize("bad_limit", [0, 501, -1])
    def test_invalid_limit_returns_error(self, bad_limit: int, tools: ConnectionTools) -> None:
        """Limits outside 1..500 produce a validation error."""
        result = json.loads(tools.oslc_query_resources("testcase", "Proj", limit=bad_limit))

        assert "error" in result
        assert "limit" in result["error"].lower()

    @patch("tools.connection_tools.oslc_query", return_value='{"results": []}')
    def test_valid_call_delegates_to_oslc_query(self, mock_oslc: MagicMock, tools: ConnectionTools) -> None:
        """A valid invocation delegates to the oslc_query service function."""
        result = json.loads(
            tools.oslc_query_resources(
                resource_type="testplan",
                project_area="MyProj",
                where='dcterms:title="Plan A"',
                select="dcterms:title",
                limit=10,
            )
        )

        assert result == {"results": []}
        mock_oslc.assert_called_once_with(
            resource_type="testplan",
            project_area="MyProj",
            where='dcterms:title="Plan A"',
            select="dcterms:title",
            limit=10,
            configuration_context=None,
        )

    @patch("tools.connection_tools.oslc_query", return_value='{"results": []}')
    def test_configuration_context_forwarded(self, mock_oslc: MagicMock, tools: ConnectionTools) -> None:
        """configuration_context is passed through to oslc_query."""
        tools.oslc_query_resources(
            resource_type="testcase",
            project_area="Proj",
            configuration_context="https://example.com/ctx",
        )

        _, kwargs = mock_oslc.call_args
        assert kwargs["configuration_context"] == "https://example.com/ctx"


# ── get_resource ───────────────────────────────────────────────────────────


class TestGetResource:
    """Tests for ConnectionTools.get_resource."""

    def test_invalid_resource_type_returns_error(self, tools: ConnectionTools) -> None:
        """An unsupported resource_type yields an error."""
        result = json.loads(tools.get_resource("invalid_type", "999"))

        assert "error" in result
        assert "resource_type" in result["error"]

    @patch("tools.connection_tools.generic_get", return_value='{"webId": "123", "title": "Plan"}')
    def test_valid_type_delegates_to_generic_get(self, mock_get: MagicMock, tools: ConnectionTools) -> None:
        """A supported type delegates to generic_get."""
        result = json.loads(tools.get_resource("testplan", "123", project_area="Proj"))

        assert result["webId"] == "123"
        mock_get.assert_called_once_with("testplan", "123", "Proj", configuration_context=None)

    @patch("tools.connection_tools.generic_get", return_value='{"webId": "55"}')
    def test_configuration_context_forwarded(self, mock_get: MagicMock, tools: ConnectionTools) -> None:
        """configuration_context is passed through to generic_get."""
        tools.get_resource("testcase", "55", configuration_context="https://example.com/ctx")

        _, kwargs = mock_get.call_args
        assert kwargs["configuration_context"] == "https://example.com/ctx"
