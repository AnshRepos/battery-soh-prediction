"""
ETM MCP Server Configuration

Centralized configuration, constants, namespace definitions,
logging setup, and environment variable handling for ETM MCP Server.
"""

import logging
import os
import sys
import xml.etree.ElementTree as ET
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = SCRIPT_DIR / "logs"


def _ensure_directory(path: Path, label: str) -> None:
    """Best-effort creation of a directory at import time."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning(
            "Unable to create %s directory '%s': %s",
            label,
            path,
            exc,
        )


_ensure_directory(LOG_DIR, "log")

LOG_FILE = LOG_DIR / "etm_mcp.log"

# ---------------------------------------------------------------------------
# ETM connection details from environment
# ---------------------------------------------------------------------------
ETM_BASE_URL: str = os.getenv("ETM_BASE_URL", "").rstrip("/")
ETM_USERNAME: str | None = os.getenv("ETM_USERNAME")
ETM_PASSWORD: str | None = os.getenv("ETM_PASSWORD")
ETM_PROJECT_AREA: str | None = os.getenv("ETM_PROJECT_AREA")
# Jira / change-tracker credentials.
# When ETM returns WWW-Authenticate: DownstreamAuth on the /proxy endpoint
# (meaning no active OSLC friendship with the tracker), link_defect_to_execution_result
# falls back to the Jira Remote Link REST API using a Bearer PAT.
# JIRA_PAT: personal access token issued by Jira (Profile → Personal Access Tokens).
# JIRA_USERNAME / JIRA_PASSWORD: only needed if falling back to Basic auth; typically
#   left unset and ETM_USERNAME/ETM_PASSWORD are forwarded as DownstreamAuth instead.
JIRA_PAT: str | None = os.getenv("JIRA_PAT")
JIRA_USERNAME: str | None = os.getenv("JIRA_USERNAME") or os.getenv("ETM_USERNAME")
JIRA_PASSWORD: str | None = os.getenv("JIRA_PASSWORD")
# SSL Verification Configuration
# CERTIFICATE_PATH controls SSL verification:
#   - File path (e.g., /etc/ssl/certs/ca-certificates.crt) → Uses that certificate
#   - "false" / "disable" / "off" / "no" → Disables SSL verification
#   - Not set / empty → Auto-detects mounted cert, falls back to certifi bundle
# Legacy: ETM_VERIFY_SSL=false also disables SSL verification (backward compat)
_SSL_DISABLE_VALUES = {"false", "0", "no", "off", "disable"}

_legacy_ssl = os.getenv("ETM_VERIFY_SSL", "").lower()
CERTIFICATE_PATH = os.getenv("CERTIFICATE_PATH", "")

ETM_VERIFY_SSL: bool | str
if _legacy_ssl in _SSL_DISABLE_VALUES:
    ETM_VERIFY_SSL = False
elif CERTIFICATE_PATH and CERTIFICATE_PATH.lower() in _SSL_DISABLE_VALUES:
    ETM_VERIFY_SSL = False
elif CERTIFICATE_PATH:
    if os.path.isfile(CERTIFICATE_PATH):
        ETM_VERIFY_SSL = CERTIFICATE_PATH
    else:
        logger.warning("CERTIFICATE_PATH %r not found; falling back to default CA bundle", CERTIFICATE_PATH)
        ETM_VERIFY_SSL = True
else:
    if os.path.exists("/etc/ssl/certs/ca-certificates.crt"):
        ETM_VERIFY_SSL = "/etc/ssl/certs/ca-certificates.crt"
    else:
        ETM_VERIFY_SSL = True

# ---------------------------------------------------------------------------
# Shared Field description constants (used across tool parameters)
# ---------------------------------------------------------------------------
PROJECT_AREA_DESC = "Project area NAME (e.g., 'My Project (qm)'). Gets from User input in prompt or Defaults to ETM_PROJECT_AREA env var."
CONFIG_CONTEXT_DESC = (
    "CM stream URI for CM-enabled projects. Get from list_cm_configurations(). Omit if project doesn't use CM."
)
LIMIT_DESC = "Maximum number of results to return (1-200)."

# ---------------------------------------------------------------------------
# XML Namespace constants
# ---------------------------------------------------------------------------
ETM_NAMESPACE = "http://jazz.net/xmlns/alm/qm/v0.1/"
ALM_NAMESPACE = "http://jazz.net/xmlns/alm/v0.1/"
EXECRESULT_NAMESPACE = "http://jazz.net/xmlns/alm/qm/v0.1/executionresult/v0.1"
OSLC_QM_NAMESPACE = "http://open-services.net/ns/qm#"
JAZZ_RQM_NAMESPACE = "http://jazz.net/ns/qm/rqm#"
ETM_SERVICE_PATH = "/service/com.ibm.rqm.integration.service.IIntegrationService/resources"

# Execution result state URIs used by create and update operations
EXECUTION_STATE_MAP: dict[str, str] = {
    "passed": "com.ibm.rqm.execution.common.state.passed",
    "failed": "com.ibm.rqm.execution.common.state.failed",
    "incomplete": "com.ibm.rqm.execution.common.state.incomplete",
    "blocked": "com.ibm.rqm.execution.common.state.blocked",
    "notrun": "com.ibm.rqm.execution.common.state.notrun",
    "deferred": "com.ibm.rqm.execution.common.state.deferred",
    "perm_failed": "com.ibm.rqm.execution.common.state.perm_failed",
    "inconclusive": "com.ibm.rqm.execution.common.state.inconclusive",
    "partially_blocked": "com.ibm.rqm.execution.common.state.part_blocked",
    "error": "com.ibm.rqm.execution.common.state.error",
}

# Standard namespaces for XML parsing
ETM_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "qm": ETM_NAMESPACE,
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "rqm": "http://schema.ibm.com/rqm/2007#executionresult",
    "oslc": "http://open-services.net/ns/core#",
    "oslc_qm": OSLC_QM_NAMESPACE,
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "jp": "http://jazz.net/xmlns/prod/jazz/process/0.6/",
}

# OSLC QM resource type URIs
OSLC_QM_RESOURCE_TYPES: dict[str, list[str]] = {
    "testplan": [f"{OSLC_QM_NAMESPACE}TestPlan", f"{OSLC_QM_NAMESPACE}TestPlanQuery"],
    "testcase": [f"{OSLC_QM_NAMESPACE}TestCase", f"{OSLC_QM_NAMESPACE}TestCaseQuery"],
    "testscript": [f"{OSLC_QM_NAMESPACE}TestScript", f"{OSLC_QM_NAMESPACE}TestScriptQuery"],
    "executionresult": [f"{OSLC_QM_NAMESPACE}TestResult", f"{OSLC_QM_NAMESPACE}TestResultQuery"],
    "executionworkitem": [f"{OSLC_QM_NAMESPACE}TestExecutionRecord", f"{OSLC_QM_NAMESPACE}TestExecutionRecordQuery"],
    "testsuite": [f"{JAZZ_RQM_NAMESPACE}TestSuite", f"{JAZZ_RQM_NAMESPACE}TestSuiteQuery"],
    "testphase": [f"{JAZZ_RQM_NAMESPACE}TestPhase", f"{JAZZ_RQM_NAMESPACE}TestPhaseQuery"],
    "testsuiteexecutionrecord": [
        f"{JAZZ_RQM_NAMESPACE}TestSuiteExecutionRecord",
        f"{JAZZ_RQM_NAMESPACE}TestSuiteExecutionRecordQuery",
    ],
}

# Supported resource types for generic list/get operations
LISTABLE_RESOURCE_TYPES = {
    "testplan",
    "testcase",
    "testsuite",
    "testscript",
    "testphase",
    "executionresult",
    "executionworkitem",
    "attachment",
    "template",
    "buildrecord",
    "configuration",
}

# ---------------------------------------------------------------------------
# Configure SSL verification
# ---------------------------------------------------------------------------
if ETM_VERIFY_SSL is False:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.warning("SSL certificate verification is disabled.")

# ---------------------------------------------------------------------------
# Register XML namespaces to prevent ns0/ns1 prefix issues
# ---------------------------------------------------------------------------
ET.register_namespace("qm", ETM_NAMESPACE)
ET.register_namespace("alm", ALM_NAMESPACE)
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("dcterms", "http://purl.org/dc/terms/")
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
ET.register_namespace("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ET.register_namespace("oslc", "http://open-services.net/ns/core#")
ET.register_namespace("oslc_qm", OSLC_QM_NAMESPACE)
ET.register_namespace("execresult", EXECRESULT_NAMESPACE)


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
def setup_logging(transport: str = "") -> None:
    """Configure the root logger with a rotating file handler and a stderr
    console handler.

    For stdio transport, logging output is written to stderr so it does not
    interfere with the MCP JSON-RPC stream on stdout.
    """
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    handlers: list[logging.Handler] = [file_handler]

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        force=True,
    )


def get_mcp_init_vars() -> tuple[str, str, int]:
    """Return ``(transport, host, port)`` from environment variables.

    Defaults to ``stdio`` transport if ``TRANSPORT`` is unset or blank.
    """
    transport = os.getenv("TRANSPORT") or "stdio"
    if transport in ("stdio", "<TRANSPORT>", None, "", "-", "null"):
        logger.info("MCP init: transport=stdio")
        return ("stdio", "", 0)

    host = os.getenv("HOST") or "127.0.0.1"
    port_str = os.getenv("HOST_PORT") or "8000"

    if host == "<HOST>":
        host = "127.0.0.1"
    if port_str == "<HOST_PORT>":
        port_str = "8000"

    try:
        port = int(port_str)
    except ValueError:
        raise ValueError(f"Invalid PORT env variable: '{port_str}' - must be a valid integer")

    logger.info(f"MCP init: transport={transport}, host={host}, port={port}")
    return (transport, host, port)
