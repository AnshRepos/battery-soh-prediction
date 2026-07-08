"""Tests for core/config.py — constants, get_mcp_init_vars, setup_logging."""

import logging

import pytest
from core.config import (
    ETM_NAMESPACE,
    EXECUTION_STATE_MAP,
    LISTABLE_RESOURCE_TYPES,
    OSLC_QM_RESOURCE_TYPES,
    get_mcp_init_vars,
    setup_logging,
)


class TestConstants:
    """Verify module-level constants exist and have correct types."""

    def test_etm_namespace_is_string(self):
        assert isinstance(ETM_NAMESPACE, str)
        assert "jazz.net" in ETM_NAMESPACE

    def test_execution_state_map_is_dict_with_known_keys(self):
        assert isinstance(EXECUTION_STATE_MAP, dict)
        expected_keys = {"passed", "failed", "incomplete", "blocked", "notrun", "deferred"}
        assert expected_keys.issubset(EXECUTION_STATE_MAP.keys())
        for value in EXECUTION_STATE_MAP.values():
            assert isinstance(value, str)

    def test_listable_resource_types_is_set(self):
        assert isinstance(LISTABLE_RESOURCE_TYPES, set)
        assert "testcase" in LISTABLE_RESOURCE_TYPES
        assert "testplan" in LISTABLE_RESOURCE_TYPES

    def test_oslc_qm_resource_types_has_expected_keys(self):
        assert isinstance(OSLC_QM_RESOURCE_TYPES, dict)
        for key in ("testplan", "testcase", "testscript", "executionresult"):
            assert key in OSLC_QM_RESOURCE_TYPES
            assert isinstance(OSLC_QM_RESOURCE_TYPES[key], list)
            assert len(OSLC_QM_RESOURCE_TYPES[key]) == 2


class TestGetMcpInitVars:
    """Tests for get_mcp_init_vars() environment-driven config."""

    def test_defaults_return_stdio(self, monkeypatch):
        monkeypatch.delenv("TRANSPORT", raising=False)
        monkeypatch.delenv("HOST", raising=False)
        monkeypatch.delenv("HOST_PORT", raising=False)
        assert get_mcp_init_vars() == ("stdio", "", 0)

    def test_sse_transport_with_host_and_port(self, monkeypatch):
        monkeypatch.setenv("TRANSPORT", "sse")
        monkeypatch.setenv("HOST", "0.0.0.0")
        monkeypatch.setenv("HOST_PORT", "9000")
        assert get_mcp_init_vars() == ("sse", "0.0.0.0", 9000)

    def test_invalid_port_raises_value_error(self, monkeypatch):
        monkeypatch.setenv("TRANSPORT", "sse")
        monkeypatch.setenv("HOST_PORT", "not_a_number")
        with pytest.raises(ValueError, match="Invalid PORT"):
            get_mcp_init_vars()

    def test_placeholder_transport_returns_stdio(self, monkeypatch):
        monkeypatch.setenv("TRANSPORT", "<TRANSPORT>")
        assert get_mcp_init_vars() == ("stdio", "", 0)

    def test_empty_transport_returns_stdio(self, monkeypatch):
        monkeypatch.setenv("TRANSPORT", "")
        assert get_mcp_init_vars() == ("stdio", "", 0)

    def test_placeholder_host_defaults(self, monkeypatch):
        monkeypatch.setenv("TRANSPORT", "sse")
        monkeypatch.setenv("HOST", "<HOST>")
        monkeypatch.setenv("HOST_PORT", "<HOST_PORT>")
        transport, host, port = get_mcp_init_vars()
        assert host == "127.0.0.1"
        assert port == 8000


class TestSetupLogging:
    """Verify setup_logging runs without errors and configures handlers."""

    def test_setup_logging_creates_handlers(self):
        setup_logging(transport="stdio")
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_with_empty_transport(self):
        setup_logging(transport="")
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
