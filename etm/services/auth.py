"""
ETM Authentication Service

Handles authentication with IBM Jazz/ETM server using persistent HTTP sessions.
"""

import logging
import os

import requests
from core.config import ETM_BASE_URL, ETM_PASSWORD, ETM_USERNAME, ETM_VERIFY_SSL
from core.custom_exceptions import AuthenticationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Persistent HTTP session — reuses TCP connections and Jazz session cookies.
# ---------------------------------------------------------------------------
_session = requests.Session()
_session.verify = ETM_VERIFY_SSL
_session_authenticated = False
_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
if _proxy:
    _session.proxies = {"http": _proxy, "https": _proxy}


def _validate_required_env_vars() -> None:
    """Validate required ETM environment variables at runtime."""
    missing_vars = [
        name
        for name, value in {
            "ETM_BASE_URL": ETM_BASE_URL,
            "ETM_USERNAME": ETM_USERNAME,
            "ETM_PASSWORD": ETM_PASSWORD,
        }.items()
        if not value
    ]
    if missing_vars:
        raise ValueError(f"Missing required environment variable(s): {', '.join(missing_vars)}")


def _get_headers(accept_type: str = "application/xml") -> dict[str, str]:
    """Generate standard headers for ETM API requests."""
    return {
        "Accept": accept_type,
        "OSLC-Core-Version": "2.0",
        "X-Jazz-CSRF-Prevent": "true",
    }


def authenticate() -> None:
    """Authenticate with IBM Jazz/ETM server.

    Handles both HTTP Basic Auth and Jazz form-based authentication.
    Uses the persistent _session to maintain cookies across requests.
    """
    global _session_authenticated
    _validate_required_env_vars()
    if _session_authenticated:
        return

    _session.auth = (ETM_USERNAME or "", ETM_PASSWORD or "")

    try:
        auth_check_url = f"{ETM_BASE_URL}/authenticated/identity"
        response = _session.get(
            auth_check_url,
            headers=_get_headers("application/xml"),
            allow_redirects=True,
            timeout=30,
            verify=ETM_VERIFY_SSL,
        )

        auth_msg = response.headers.get("X-com-ibm-team-repository-web-auth-msg", "")
        if auth_msg == "authrequired":
            login_url = f"{ETM_BASE_URL}/j_security_check"
            login_response = _session.post(
                login_url,
                data={"j_username": ETM_USERNAME, "j_password": ETM_PASSWORD},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                allow_redirects=True,
                timeout=30,
                verify=ETM_VERIFY_SSL,
            )

            auth_result = login_response.headers.get("X-com-ibm-team-repository-web-auth-msg", "")
            if auth_result == "authfailed":
                raise AuthenticationError("Authentication failed. Check ETM_USERNAME and ETM_PASSWORD credentials.")

            verify_response = _session.get(
                auth_check_url,
                headers=_get_headers("application/xml"),
                allow_redirects=True,
                timeout=30,
                verify=ETM_VERIFY_SSL,
            )
            verify_msg = verify_response.headers.get("X-com-ibm-team-repository-web-auth-msg", "")
            if verify_msg == "authrequired":
                raise AuthenticationError("Authentication verification failed after form-based login.")

            logger.info("Jazz form-based authentication successful")
        elif response.status_code == 200:
            logger.info("Authentication successful (basic auth accepted)")
        else:
            response.raise_for_status()

        _session_authenticated = True

    except requests.exceptions.RequestException as e:
        raise AuthenticationError(f"ETM authentication failed: {e}") from e


def get_authenticated_session() -> requests.Session:
    """Return the authenticated session, authenticating first if needed."""
    authenticate()
    return _session


def reset_authentication() -> None:
    """Reset authentication state, forcing re-authentication on next request."""
    global _session_authenticated
    _session_authenticated = False


def is_authenticated() -> bool:
    """Check if the session is currently authenticated."""
    return _session_authenticated
