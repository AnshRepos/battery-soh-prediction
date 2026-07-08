"""Tests for services/etm_client.py — URL builders, make_request, generic CRUD."""

import json
from unittest.mock import MagicMock, patch

import pytest
from services.etm_client import (
    build_category_href,
    build_resource_href,
    build_resource_url,
    extract_resource_id,
    generic_create,
    generic_delete,
    generic_get,
    generic_list,
    generic_update,
    handle_error,
    make_request,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def ok_response():
    """A mock 200 response with default headers."""
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"ETag": '"etag-abc"'}
    resp.text = "<root><qm:webId xmlns:qm='http://jazz.net/xmlns/alm/qm/v0.1/'>999</qm:webId></root>"
    resp.url = "https://etm.example.com/resource"
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture
def auth_required_then_ok(ok_response):
    """Two responses: first triggers re-auth, second succeeds."""
    expired = MagicMock()
    expired.status_code = 200
    expired.headers = {"X-com-ibm-team-repository-web-auth-msg": "authrequired"}
    expired.url = "https://etm.example.com/resource"
    expired.raise_for_status = MagicMock()
    return [expired, ok_response]


# ── URL builders ──────────────────────────────────────────────────────────


class TestBuildResourceUrl:
    """Tests for build_resource_url()."""

    def test_basic_url(self):
        url = build_resource_url("MyProject (qm)", "testcase")
        assert "/testcase" in url
        assert "MyProject" in url

    def test_with_numeric_resource_id(self):
        url = build_resource_url("Proj", "testcase", "12345")
        # Colons are percent-encoded by quote().
        assert "urn%3Acom.ibm.rqm%3Atestcase%3A12345" in url

    def test_with_urn_prefix(self):
        urn = "urn:com.ibm.rqm:testcase:99"
        url = build_resource_url("Proj", "testcase", urn)
        assert "urn" in url
        # Should not double-wrap the urn.
        assert url.count("urn") == 1 or "urn%3A" in url

    def test_with_te_prefixed_id(self):
        """TE-prefixed config IDs (e.g. TE3023) must not be URN-wrapped."""
        url = build_resource_url("CC-DA ESM Sandbox", "configuration", "TE3023")
        assert "TE3023" in url
        assert "urn" not in url

    def test_with_slug_id(self):
        """Slug IDs returned by ETM after creation must not be URN-wrapped."""
        url = build_resource_url("CC-DA ESM Sandbox", "executionworkitem", "slug__RWg3wDImEfGUXsclYdfLIw")
        assert "slug__RWg3wDImEfGUXsclYdfLIw" in url
        assert "urn" not in url


class TestBuildResourceHref:
    """Tests for build_resource_href()."""

    @patch("services.etm_client.ETM_BASE_URL", "https://etm.example.com")
    def test_normal_id(self):
        href = build_resource_href("Proj", "testplan", "555")
        assert href.startswith("https://etm.example.com")
        assert "urn:com.ibm.rqm:testplan:555" in href

    @patch("services.etm_client.ETM_BASE_URL", "https://etm.example.com")
    def test_urn_id(self):
        href = build_resource_href("Proj", "testcase", "urn:com.ibm.rqm:testcase:1")
        assert "urn:com.ibm.rqm:testcase:1" in href

    @patch("services.etm_client.ETM_BASE_URL", "https://etm.example.com")
    def test_te_prefixed_id(self):
        """TE-prefixed IDs (e.g. TE3023) must not be URN-wrapped in href."""
        href = build_resource_href("CC-DA ESM Sandbox", "configuration", "TE3023")
        assert href.startswith("https://etm.example.com")
        assert "TE3023" in href
        assert "urn" not in href

    @patch("services.etm_client.ETM_BASE_URL", "https://etm.example.com")
    def test_slug_id(self):
        """Slug IDs returned by ETM must not be URN-wrapped in href."""
        href = build_resource_href("CC-DA ESM Sandbox", "executionworkitem", "slug__RWg3wDImEfGUXsclYdfLIw")
        assert href.startswith("https://etm.example.com")
        assert "slug__RWg3wDImEfGUXsclYdfLIw" in href
        assert "urn" not in href


class TestBuildCategoryHref:
    """Tests for build_category_href()."""

    @patch("services.etm_client.ETM_BASE_URL", "https://etm.example.com")
    def test_encodes_special_chars(self):
        href = build_category_href("My Project", "Test Level", "Unit Test")
        assert "category" in href
        assert "Test%20Level" in href or "Test+Level" in href


# ── make_request ──────────────────────────────────────────────────────────


class TestMakeRequest:
    """Tests for make_request() — headers, auth, re-auth, config context."""

    @patch("services.etm_client.authenticate")
    @patch("services.etm_client.reset_authentication")
    def test_basic_get(self, _mock_reset, _mock_auth, ok_response):
        with patch("services.auth._session") as mock_session:
            mock_session.request.return_value = ok_response
            # Patch the local import inside make_request.
            with patch("services.etm_client.authenticate"):
                with patch.dict("sys.modules", {}):
                    pass
            # Direct approach: patch the module-level _session import.
            with patch("services.etm_client._session", mock_session, create=True):
                pass

        # Simpler: patch at the import site inside make_request.
        with patch("services.auth._session") as mock_session:
            mock_session.request.return_value = ok_response
            make_request("/api/resource")
            mock_session.request.assert_called_once()
            call_args = mock_session.request.call_args
            assert call_args[0][0] == "GET"
            assert "Accept" in call_args[1]["headers"]

    @patch("services.etm_client.authenticate")
    @patch("services.etm_client.reset_authentication")
    def test_reauth_on_session_expiry(self, mock_reset, mock_auth, auth_required_then_ok):
        with patch("services.auth._session") as mock_session:
            mock_session.request.side_effect = auth_required_then_ok
            make_request("/api/resource")
            mock_reset.assert_called_once()
            assert mock_session.request.call_count == 2

    @patch("services.etm_client.authenticate")
    def test_configuration_context_header(self, _mock_auth, ok_response):
        with patch("services.auth._session") as mock_session:
            mock_session.request.return_value = ok_response
            make_request("/api/resource", configuration_context="https://config/ctx")
            headers = mock_session.request.call_args[1]["headers"]
            assert headers["Configuration-Context"] == "https://config/ctx"

    @patch("services.etm_client.authenticate")
    def test_post_with_data(self, _mock_auth, ok_response):
        with patch("services.auth._session") as mock_session:
            mock_session.request.return_value = ok_response
            make_request("/api/resource", method="POST", data=b"<xml/>", content_type="application/rdf+xml")
            call_kwargs = mock_session.request.call_args[1]
            assert call_kwargs["data"] == b"<xml/>"
            assert call_kwargs["headers"]["Content-Type"] == "application/rdf+xml"


# ── extract_resource_id ───────────────────────────────────────────────────


class TestExtractResourceId:
    """Tests for extract_resource_id()."""

    def test_from_xml_web_id(self):
        resp = MagicMock()
        resp.text = "<r><qm:webId xmlns:qm='http://jazz.net/xmlns/alm/qm/v0.1/'>42</qm:webId></r>"
        resp.headers = {}
        assert extract_resource_id(resp, "testcase") == "42"

    def test_from_location_header(self):
        resp = MagicMock()
        resp.text = "<r/>"
        resp.headers = {"Location": "https://etm.example.com/resource/urn:com.ibm.rqm:testcase:77"}
        assert extract_resource_id(resp, "testcase") == "77"

    def test_from_location_header_plain_id(self):
        resp = MagicMock()
        resp.text = "<r/>"
        resp.headers = {"Location": "https://etm.example.com/resource/slug__abc123"}
        result = extract_resource_id(resp, "testcase")
        assert result == "slug__abc123"

    def test_returns_none_when_not_found(self):
        resp = MagicMock()
        resp.text = "<r/>"
        resp.headers = {}
        assert extract_resource_id(resp, "testcase") is None


# ── handle_error ──────────────────────────────────────────────────────────


class TestHandleError:
    """Tests for handle_error()."""

    def test_returns_json_with_error_and_function(self):
        result = json.loads(handle_error("create_testcase", ValueError("bad input")))
        assert result["error"] == "bad input"
        assert result["function"] == "create_testcase"


# ── Generic CRUD ──────────────────────────────────────────────────────────


class TestGenericList:
    """Tests for generic_list()."""

    @patch("services.etm_client.make_request")
    def test_returns_response_text(self, mock_req):
        mock_req.return_value = MagicMock(text="<feed/>")
        result = json.loads(generic_list("testcase", project_area="Proj"))
        assert result["count"] == 0
        assert result["page"] == 0
        assert result["page_size"] == 50
        assert result["entries"] == []
        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args
        assert call_kwargs[1]["params"]["pageSize"] == "50"

    def test_invalid_limit_returns_error(self):
        result = json.loads(generic_list("testcase", limit=0))
        assert "error" in result

    def test_limit_too_high_returns_error(self):
        result = json.loads(generic_list("testcase", limit=999))
        assert "error" in result

    @patch("services.etm_client.make_request")
    def test_missing_project_returns_error(self, _mock_req, monkeypatch):
        monkeypatch.setenv("ETM_PROJECT_AREA", "")
        # Must reload config to pick up blank project area.
        import importlib

        import core.config

        importlib.reload(core.config)
        import services.etm_client

        importlib.reload(services.etm_client)
        from services.etm_client import generic_list as gl

        result = json.loads(gl("testcase", project_area=""))
        assert "error" in result


class TestGenericGet:
    """Tests for generic_get()."""

    @patch("services.etm_client.make_request")
    @patch("services.etm_client.parse_resource_to_json", return_value='{"title":"TC1"}')
    def test_returns_parsed_json(self, _mock_parse, mock_req):
        mock_req.return_value = MagicMock(text="<testcase/>")
        result = json.loads(generic_get("testcase", "123", project_area="Proj"))
        assert result["title"] == "TC1"

    def test_empty_id_returns_error(self):
        result = json.loads(generic_get("testcase", "  ", project_area="Proj"))
        assert "error" in result


class TestGenericCreate:
    """Tests for generic_create()."""

    @patch("services.etm_client.make_request")
    @patch("services.etm_client.extract_resource_id", return_value="555")
    @patch("services.etm_client.create_xml_resource", return_value="<xml/>")
    def test_returns_success_with_id(self, _mock_xml, _mock_extract, mock_req):
        resp = MagicMock()
        resp.headers = {"Location": "https://etm.example.com/testcase/555"}
        mock_req.return_value = resp
        result = json.loads(generic_create("testcase", "Title", "Desc", project_area="Proj"))
        assert result["success"] is True
        assert result["testcase_id"] == "555"

    @patch("services.etm_client.make_request")
    @patch("services.etm_client.extract_resource_id", return_value="slug__abc")
    @patch("services.etm_client.create_xml_resource", return_value="<xml/>")
    def test_slug_resolved_to_web_id(self, _mock_xml, _mock_extract, mock_req):
        """When create returns a slug ID, a follow-up GET resolves to webId."""
        create_resp = MagicMock()
        create_resp.headers = {"Location": "https://etm.example.com/testcase/slug__abc"}

        get_resp = MagicMock()
        get_resp.text = "<r><ns2:webId xmlns:ns2='http://jazz.net/xmlns/alm/qm/v0.1/'>789</ns2:webId></r>"

        mock_req.side_effect = [create_resp, get_resp]
        result = json.loads(generic_create("testcase", "T", "D", project_area="Proj"))
        assert result["testcase_id"] == "789"
        assert result.get("slug_id") == "slug__abc"


class TestGenericUpdate:
    """Tests for generic_update()."""

    @patch("services.etm_client.make_request")
    @patch("services.etm_client.update_xml_resource", return_value=b"<updated/>")
    @patch("services.etm_client.strip_invalid_weight_fields", side_effect=lambda x: x)
    def test_get_then_put(self, _mock_strip, _mock_update, mock_req):
        get_resp = MagicMock()
        get_resp.text = "<testcase/>"
        get_resp.headers = {"ETag": '"etag-1"'}
        put_resp = MagicMock()
        mock_req.side_effect = [get_resp, put_resp]

        result = json.loads(generic_update("testcase", "123", project_area="Proj", title="New"))
        assert result["success"] is True
        assert mock_req.call_count == 2
        # Second call should be PUT with If-Match header.
        put_call = mock_req.call_args_list[1]
        assert put_call[1]["method"] == "PUT"
        assert put_call[1]["extra_headers"]["If-Match"] == '"etag-1"'

    def test_empty_id_returns_error(self):
        result = json.loads(generic_update("testcase", "", project_area="Proj"))
        assert "error" in result


class TestGenericDelete:
    """Tests for generic_delete()."""

    @patch("services.etm_client.make_request")
    def test_delete_success(self, mock_req):
        mock_req.return_value = MagicMock()
        result = json.loads(generic_delete("testcase", "123", project_area="Proj"))
        assert result["success"] is True
        mock_req.assert_called_once()
        assert mock_req.call_args[1]["method"] == "DELETE"

    def test_empty_id_returns_error(self):
        result = json.loads(generic_delete("testcase", "", project_area="Proj"))
        assert "error" in result
