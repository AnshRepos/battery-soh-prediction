"""Pytest configuration — ensure the ETM package root is on sys.path
so that imports like ``from core.config import ...`` resolve correctly
regardless of how pytest is invoked.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ETM package root: mcp/etm/
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# ── Environment variable fixtures ──────────────────────────────────────────


@pytest.fixture(autouse=True)
def _mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required ETM env vars for all tests to prevent import-time errors."""
    monkeypatch.setenv("ETM_BASE_URL", "https://etm.example.com")
    monkeypatch.setenv("ETM_USERNAME", "testuser")
    monkeypatch.setenv("ETM_PASSWORD", "testpass")
    monkeypatch.setenv("ETM_PROJECT_AREA", "TestProject (qm)")
    monkeypatch.setenv("ETM_VERIFY_SSL", "true")


# ── Common mock fixtures ───────────────────────────────────────────────────


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a mock requests.Session."""
    session = MagicMock()
    session.verify = True
    session.proxies = {}
    return session


@pytest.fixture
def mock_response() -> MagicMock:
    """Return a mock requests.Response with sensible defaults."""
    response = MagicMock()
    response.status_code = 200
    response.headers = {"ETag": '"etag-123"'}
    response.text = "<root/>"
    response.url = "https://etm.example.com/resource"
    return response


# ── XML sample fixtures ───────────────────────────────────────────────────

SAMPLE_TEST_CASE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:alm="http://jazz.net/xmlns/alm/v0.1/">
    <dc:title>Sample Test Case</dc:title>
    <dc:description>A test case for testing</dc:description>
    <ns2:webId>12345</ns2:webId>
    <ns2:weight>100</ns2:weight>
    <ns2:state>com.ibm.rqm.planning.common.new</ns2:state>
    <ns2:category term="Test-Level" value="Unit Test"
        href="https://etm.example.com/category/Test-Level/Unit%20Test"/>
    <ns2:category term="Regression Test" value="yes"
        href="https://etm.example.com/category/Regression%20Test/yes"/>
    <ns2:customAttributes>
        <ns2:customAttribute>
            <ns2:name>Honda_Test_Case_ID</ns2:name>
            <ns2:value>HTC-001</ns2:value>
        </ns2:customAttribute>
    </ns2:customAttributes>
</ns2:testcase>"""


SAMPLE_ATOM_FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:qm="http://jazz.net/xmlns/alm/qm/v0.1/">
    <title>Test Cases</title>
    <entry>
        <id>urn:com.ibm.rqm:testcase:12345</id>
        <title>Test Case 1</title>
        <updated>2026-01-01T00:00:00.000Z</updated>
        <content>
            <qm:testcase>
                <qm:webId>12345</qm:webId>
            </qm:testcase>
        </content>
    </entry>
    <entry>
        <id>urn:com.ibm.rqm:testcase:12346</id>
        <title>Test Case 2</title>
        <updated>2026-01-02T00:00:00.000Z</updated>
        <content>
            <qm:testcase>
                <qm:webId>12346</qm:webId>
            </qm:testcase>
        </content>
    </entry>
</feed>"""


SAMPLE_OSLC_CATALOG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:oslc="http://open-services.net/ns/core#"
         xmlns:dcterms="http://purl.org/dc/terms/">
    <oslc:ServiceProviderCatalog>
        <oslc:ServiceProvider rdf:about="https://etm.example.com/sp/TestProject">
            <dcterms:title>TestProject (qm)</dcterms:title>
        </oslc:ServiceProvider>
    </oslc:ServiceProviderCatalog>
</rdf:RDF>"""


@pytest.fixture
def sample_test_case_xml() -> str:
    return SAMPLE_TEST_CASE_XML


@pytest.fixture
def sample_atom_feed_xml() -> str:
    return SAMPLE_ATOM_FEED_XML


@pytest.fixture
def sample_oslc_catalog_xml() -> str:
    return SAMPLE_OSLC_CATALOG_XML
