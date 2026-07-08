"""Tests for services/auth.py — authentication lifecycle."""

import importlib
from unittest.mock import MagicMock, patch

import pytest


def _reload_auth_stack(monkeypatch=None):
    """Reload core.config then services.auth so module-level globals pick up env vars.

    core.config captures ETM_BASE_URL/ETM_USERNAME/ETM_PASSWORD via os.getenv()
    at import time.  A simple ``importlib.reload(auth)`` re-imports those stale
    values unless core.config is reloaded first.
    """
    import core.config as cfg_mod
    import services.auth as auth_mod

    importlib.reload(cfg_mod)
    importlib.reload(auth_mod)
    return auth_mod


class TestValidateRequiredEnvVars:
    """Tests for _validate_required_env_vars()."""

    def test_raises_when_base_url_missing(self, monkeypatch):
        monkeypatch.setenv("ETM_BASE_URL", "")
        auth_mod = _reload_auth_stack()
        with pytest.raises(ValueError, match="Missing required"):
            auth_mod._validate_required_env_vars()

    def test_raises_when_username_missing(self, monkeypatch):
        monkeypatch.delenv("ETM_USERNAME", raising=False)
        auth_mod = _reload_auth_stack()
        with pytest.raises(ValueError, match="ETM_USERNAME"):
            auth_mod._validate_required_env_vars()

    def test_passes_when_all_vars_set(self):
        """No exception when all required env vars are present (conftest sets them)."""
        auth_mod = _reload_auth_stack()
        auth_mod._validate_required_env_vars()  # should not raise


class TestAuthenticate:
    """Tests for authenticate() — basic auth, form-based auth, skip-if-done."""

    def test_basic_auth_success(self):
        auth_mod = _reload_auth_stack()
        auth_mod._session_authenticated = False

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}

        with patch.object(auth_mod._session, "get", return_value=mock_resp):
            auth_mod.authenticate()

        assert auth_mod._session_authenticated is True

    def test_form_based_auth_success(self):
        auth_mod = _reload_auth_stack()
        auth_mod._session_authenticated = False

        initial_resp = MagicMock()
        initial_resp.status_code = 200
        initial_resp.headers = {"X-com-ibm-team-repository-web-auth-msg": "authrequired"}

        login_resp = MagicMock()
        login_resp.headers = {}

        verify_resp = MagicMock()
        verify_resp.headers = {}

        with (
            patch.object(auth_mod._session, "get", side_effect=[initial_resp, verify_resp]),
            patch.object(auth_mod._session, "post", return_value=login_resp),
        ):
            auth_mod.authenticate()

        assert auth_mod._session_authenticated is True

    def test_skips_if_already_authenticated(self):
        auth_mod = _reload_auth_stack()
        auth_mod._session_authenticated = True

        with patch.object(auth_mod._session, "get") as mock_get:
            auth_mod.authenticate()
            mock_get.assert_not_called()

    def test_form_auth_failure_raises(self):
        auth_mod = _reload_auth_stack()
        auth_mod._session_authenticated = False

        initial_resp = MagicMock()
        initial_resp.status_code = 200
        initial_resp.headers = {"X-com-ibm-team-repository-web-auth-msg": "authrequired"}

        login_resp = MagicMock()
        login_resp.headers = {"X-com-ibm-team-repository-web-auth-msg": "authfailed"}

        with (
            patch.object(auth_mod._session, "get", return_value=initial_resp),
            patch.object(auth_mod._session, "post", return_value=login_resp),
        ):
            with pytest.raises(Exception, match="Authentication failed"):
                auth_mod.authenticate()


class TestSessionHelpers:
    """Tests for get_authenticated_session, reset_authentication, is_authenticated."""

    def test_get_authenticated_session_calls_authenticate(self):
        auth_mod = _reload_auth_stack()
        with patch.object(auth_mod, "authenticate") as mock_auth:
            session = auth_mod.get_authenticated_session()
            mock_auth.assert_called_once()
            assert session is auth_mod._session

    def test_reset_authentication_clears_flag(self):
        auth_mod = _reload_auth_stack()
        auth_mod._session_authenticated = True
        auth_mod.reset_authentication()
        assert auth_mod._session_authenticated is False

    def test_is_authenticated_returns_correct_state(self):
        auth_mod = _reload_auth_stack()
        auth_mod._session_authenticated = False
        assert auth_mod.is_authenticated() is False
        auth_mod._session_authenticated = True
        assert auth_mod.is_authenticated() is True
