"""Integration tests for the MCPServerRunner and main() entry point.

Verifies that MCPServerRunner initialises FastMCP, registers all tools,
and that main() is callable without starting a real server.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from etmmcpserver import MCPServerRunner, main  # noqa: E402
    from fastmcp import FastMCP  # noqa: E402
    from tools import ETMToolsManager  # noqa: E402

    _HAS_FASTMCP = True
except ImportError:
    _HAS_FASTMCP = False

pytestmark = pytest.mark.skipif(not _HAS_FASTMCP, reason="fastmcp not installed")

# Number of tools registered in _register_tools (count from etmmcpserver.py).
EXPECTED_REGISTERED_TOOL_COUNT = 55


# ── Helpers ────────────────────────────────────────────────────────────────


def _create_runner(**kwargs) -> MCPServerRunner:
    """Create an MCPServerRunner with signal and logging patched out."""
    with patch("etmmcpserver.signal.signal"), patch("etmmcpserver.setup_logging"):
        return MCPServerRunner(**kwargs)


# ── Tests: MCPServerRunner initialisation ──────────────────────────────────


class TestMCPServerRunnerInit:
    """Verify MCPServerRunner construction."""

    @patch("etmmcpserver.signal.signal")
    @patch("etmmcpserver.setup_logging")
    def test_init_creates_runner(self, mock_logging: MagicMock, mock_signal: MagicMock) -> None:
        runner = MCPServerRunner(transport="stdio")
        assert runner is not None

    @patch("etmmcpserver.signal.signal")
    @patch("etmmcpserver.setup_logging")
    def test_init_calls_setup_logging(self, mock_logging: MagicMock, mock_signal: MagicMock) -> None:
        MCPServerRunner(transport="stdio")
        mock_logging.assert_called_once_with(transport="stdio")

    @patch("etmmcpserver.signal.signal")
    @patch("etmmcpserver.setup_logging")
    def test_init_sets_up_signal_handlers(self, mock_logging: MagicMock, mock_signal: MagicMock) -> None:
        MCPServerRunner(transport="stdio")
        assert mock_signal.call_count >= 2  # SIGINT + SIGTERM


class TestMCPServerRunnerAttributes:
    """Verify attributes on an initialised MCPServerRunner."""

    def test_mcp_is_fastmcp_instance(self) -> None:
        runner = _create_runner(transport="stdio")
        assert isinstance(runner.mcp, FastMCP)

    def test_tools_manager_is_etm_tools_manager(self) -> None:
        runner = _create_runner(transport="stdio")
        assert isinstance(runner.tools_manager, ETMToolsManager)

    def test_tools_manager_is_not_none(self) -> None:
        runner = _create_runner(transport="stdio")
        assert runner.tools_manager is not None


class TestMCPServerRunnerToolRegistration:
    """Verify that _register_tools registers the expected tools with FastMCP."""

    def test_tools_registered_count(self) -> None:
        runner = _create_runner(transport="stdio")
        registered = asyncio.run(runner.mcp.list_tools())
        assert len(registered) == EXPECTED_REGISTERED_TOOL_COUNT, (
            f"Expected {EXPECTED_REGISTERED_TOOL_COUNT} registered tools, "
            f"got {len(registered)}. Registered: {sorted(tool.name for tool in registered)}"
        )

    def test_all_registered_tool_names(self) -> None:
        """Spot-check that well-known tools are present in the registry."""
        runner = _create_runner(transport="stdio")
        registered_names = {tool.name for tool in asyncio.run(runner.mcp.list_tools())}

        expected_subset = {
            "test_project_connection",
            "list_project_areas",
            "create_test_plan",
            "list_test_cases",
            "create_test_suite",
            "create_execution_record",
            "link_testcase_to_testplan",
            "get_test_plan_tree",
            "bulk_create_test_cases",
            "list_test_scripts",
        }
        missing = expected_subset - registered_names
        assert not missing, f"Missing registered tools: {missing}"

    def test_each_registered_tool_has_name(self) -> None:
        runner = _create_runner(transport="stdio")
        for tool in asyncio.run(runner.mcp.list_tools()):
            assert tool.name, "Registered tool has an empty name"


# ── Tests: MCPServerRunner.run() ───────────────────────────────────────────


class TestMCPServerRunnerRun:
    """Verify run() delegates to FastMCP.run() without actually starting."""

    @patch.object(FastMCP, "run")
    def test_run_stdio(self, mock_run: MagicMock) -> None:
        runner = _create_runner(transport="stdio")
        runner.run(transport="stdio")
        mock_run.assert_called_once_with(transport="stdio")

    @patch.object(FastMCP, "run")
    def test_run_sse(self, mock_run: MagicMock) -> None:
        runner = _create_runner(transport="stdio")
        runner.run(transport="sse", host="0.0.0.0", port=8080)
        mock_run.assert_called_once_with(transport="sse", host="0.0.0.0", port=8080)


# ── Tests: main() entry point ─────────────────────────────────────────────


class TestMainFunction:
    """Verify the module-level main() function."""

    def test_main_exists_and_is_callable(self) -> None:
        assert callable(main)

    @patch("etmmcpserver.MCPServerRunner")
    @patch("etmmcpserver.get_mcp_init_vars", return_value=("stdio", "", 0))
    def test_main_creates_runner_and_runs(
        self,
        mock_init_vars: MagicMock,
        mock_runner_cls: MagicMock,
    ) -> None:
        main()
        mock_runner_cls.assert_called_once_with(transport="stdio")
        mock_runner_cls.return_value.run.assert_called_once_with(
            transport="stdio",
            host="",
            port=0,
        )
