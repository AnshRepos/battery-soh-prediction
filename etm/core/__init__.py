"""
Core package for ETM MCP Server.

Provides centralized configuration, logging setup, and custom exceptions.
"""

from .config import (  # noqa: F401
    ALM_NAMESPACE,
    ETM_BASE_URL,
    ETM_NAMESPACE,
    ETM_NAMESPACES,
    ETM_PASSWORD,
    ETM_PROJECT_AREA,
    ETM_SERVICE_PATH,
    ETM_USERNAME,
    ETM_VERIFY_SSL,
    EXECRESULT_NAMESPACE,
    JAZZ_RQM_NAMESPACE,
    OSLC_QM_NAMESPACE,
    OSLC_QM_RESOURCE_TYPES,
    get_mcp_init_vars,
    setup_logging,
)
