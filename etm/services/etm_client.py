"""
ETM HTTP Client Service

Provides HTTP request helpers, URL builders, and generic CRUD operations
for the ETM REST API.
"""

import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Optional
from urllib.parse import quote, urlparse

import requests
from core.config import (
    ETM_BASE_URL,
    ETM_NAMESPACE,
    ETM_PROJECT_AREA,
    ETM_SERVICE_PATH,
    ETM_VERIFY_SSL,
)
from services.auth import authenticate, reset_authentication
from services.xml_helpers import (
    create_xml_resource,
    extract_entries_from_feed,
    parse_resource_to_json,
    strip_invalid_weight_fields,
    update_xml_resource,
)

logger = logging.getLogger(__name__)


def _get_headers(accept_type: str = "application/xml") -> dict[str, str]:
    """Generate standard headers for ETM API requests."""
    return {
        "Accept": accept_type,
        "OSLC-Core-Version": "2.0",
        "X-Jazz-CSRF-Prevent": "true",
    }


def build_resource_url(project: str, resource_type: str, resource_id: Optional[str] = None) -> str:
    """Build the ETM resource URL.

    Args:
        project: Project area name
        resource_type: Type of resource (testcase, testplan, etc.)
        resource_id: Optional resource ID

    Returns:
        Formatted resource URL path
    """
    encoded_project = quote(project, safe="")
    base = f"{ETM_SERVICE_PATH}/{encoded_project}/{resource_type}"
    if resource_id:
        if resource_id.startswith("urn:"):
            return f"{base}/{quote(resource_id, safe='')}"
        if resource_id.isdigit():
            urn = f"urn:com.ibm.rqm:{resource_type}:{resource_id}"
            return f"{base}/{quote(urn, safe='')}"
        # Non-numeric IDs (e.g. TE-prefixed configuration IDs, slug__ draft IDs)
        # are used directly as URL path segments, not wrapped in URN format.
        return f"{base}/{quote(resource_id, safe='')}"
    return base


def build_resource_href(project: str, resource_type: str, resource_id: str) -> str:
    """Build a complete resource href URL for ETM references.

    Args:
        project: Project area name
        resource_type: Type of resource
        resource_id: Resource ID

    Returns:
        Complete href URL
    """
    encoded_project = quote(project, safe="")
    if resource_id.startswith("urn:"):
        url = f"{ETM_SERVICE_PATH}/{encoded_project}/{resource_type}/{resource_id}"
    elif resource_id.isdigit():
        url = f"{ETM_SERVICE_PATH}/{encoded_project}/{resource_type}/urn:com.ibm.rqm:{resource_type}:{resource_id}"
    else:
        # Non-numeric IDs (slug__, TE-prefixed, etc.) are used directly in path.
        url = f"{ETM_SERVICE_PATH}/{encoded_project}/{resource_type}/{resource_id}"
    return f"{ETM_BASE_URL}{url}"


def build_category_href(project: str, category_type: str, category_value: str) -> str:
    """Build the ETM category resource href URL."""
    encoded_project = quote(project, safe="")
    encoded_type = quote(category_type, safe="")
    encoded_value = quote(category_value, safe="")
    return f"{ETM_BASE_URL}{ETM_SERVICE_PATH}/{encoded_project}/category/{encoded_type}/{encoded_value}"


def make_request(
    endpoint: str,
    method: str = "GET",
    params: Optional[dict[str, Any]] = None,
    accept_type: str = "application/xml",
    timeout: int = 30,
    data: Optional[bytes | str] = None,
    content_type: Optional[str] = None,
    extra_headers: Optional[dict[str, str]] = None,
    configuration_context: Optional[str] = None,
) -> requests.Response:
    """Make an HTTP request to the ETM API using the authenticated session.

    Automatically handles authentication and re-authentication on session expiry.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, PUT, DELETE)
        params: Query parameters
        accept_type: Accept header value (default: application/xml)
        timeout: Request timeout in seconds
        data: Request body data
        content_type: Content-Type header value
        extra_headers: Optional additional HTTP headers
        configuration_context: Optional configuration context URI for CM-enabled projects.

    Returns:
        Response object
    """
    from services.auth import _session

    authenticate()

    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        url = endpoint
    else:
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        url = f"{ETM_BASE_URL}{endpoint}"

    headers = _get_headers(accept_type)
    if data:
        headers["Content-Type"] = content_type or "application/rdf+xml"
    if configuration_context:
        headers["Configuration-Context"] = configuration_context
    if extra_headers:
        headers.update(extra_headers)

    try:
        response = _session.request(
            method,
            url,
            headers=headers,
            params=params,
            data=data,
            timeout=timeout,
            verify=ETM_VERIFY_SSL,
        )

        auth_msg = response.headers.get("X-com-ibm-team-repository-web-auth-msg", "")
        if auth_msg == "authrequired":
            logger.info("Session expired, re-authenticating...")
            reset_authentication()
            authenticate()
            response = _session.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                timeout=timeout,
                verify=ETM_VERIFY_SSL,
            )

        logger.info(f"{method} {response.url} - Status: {response.status_code}")
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException:
        raise


def extract_resource_id(response: requests.Response, resource_type: str) -> Optional[str]:
    """Extract resource ID from API response.

    Attempts to extract the resource ID from the response body (XML) or headers.
    Tries webId first (numeric, usable in GET/UPDATE), then fallbacks.
    """
    try:
        root = ET.fromstring(response.text)
        ns = {
            "dcterms": "http://purl.org/dc/terms/",
            "rqm": "http://schema.ibm.com/rqm/2007#executionresult",
            "qm": ETM_NAMESPACE,
        }

        for xpath in [".//qm:webId", ".//rqm:resultId", ".//dcterms:identifier"]:
            elem = root.find(xpath, ns)
            if elem is not None and elem.text:
                logger.info(f"Extracted {resource_type} ID from XML: {elem.text}")
                return elem.text
    except ET.ParseError as e:
        logger.debug(f"Could not parse XML response for {resource_type}: {e}")

    for header in ["Location", "location", "Content-Location", "content-location"]:
        location = response.headers.get(header)
        if location:
            parsed = urlparse(location)
            path = parsed.path
            candidate = path.rstrip("/").split("/")[-1]

            if candidate.startswith("urn:com.ibm.rqm:"):
                resource_id = candidate.split(":")[-1]
            else:
                resource_id = candidate

            logger.info(f"Extracted {resource_type} ID from header {header}: {resource_id}")
            return resource_id

    logger.warning(f"Could not extract {resource_type} ID")
    return None


def resolve_to_web_id(
    response: requests.Response,
    resource_type: str,
    candidate_id: str,
    configuration_context: Optional[str] = None,
) -> str:
    """Resolve a slug/draft ID to a numeric webId by fetching the created resource.

    When ETM returns a slug-style ID (e.g. ``slug__...``) for a newly-created
    resource instead of a numeric webId, that slug cannot be used as a reliable
    href reference in subsequent resource creation calls (ETM expects URN-style
    references built from the numeric webId).  This function GET-s the resource
    via the ``Location`` or ``Content-Location`` response header and extracts the
    ``<qm:webId>`` element.

    Args:
        response: The POST response from an ETM resource creation request.
        resource_type: Resource type label used only for log messages.
        candidate_id: The ID already extracted from the response (may be a slug).
        configuration_context: Optional CM configuration context URI.

    Returns:
        Resolved numeric webId string, or ``candidate_id`` unchanged when
        resolution is not needed (already numeric) or fails.
    """
    if candidate_id.isdigit():
        return candidate_id

    for header in ("Location", "Content-Location"):
        location = response.headers.get(header, "")
        if location:
            try:
                get_resp = make_request(
                    location,
                    accept_type="application/xml",
                    configuration_context=configuration_context,
                )
                web_id_elem = ET.fromstring(get_resp.text).find(f".//{{{ETM_NAMESPACE}}}webId")
                if web_id_elem is not None and web_id_elem.text:
                    logger.info(f"Resolved {resource_type} slug → webId: {web_id_elem.text}")
                    return web_id_elem.text
            except Exception as e:
                logger.warning(f"Could not resolve {resource_type} slug to webId: {e}")
            break

    return candidate_id


def handle_error(func_name: str, e: Exception) -> str:
    """Standardized error handling for tool functions."""
    error_msg = str(e)
    logger.error(f"Error in {func_name}: {error_msg}", exc_info=True)
    return json.dumps({"error": error_msg, "function": func_name})


# ---------------------------------------------------------------------------
# Reusable validation error helpers — produce actionable JSON messages
# that guide all models toward recovery, regardless of model capability.
# ---------------------------------------------------------------------------


def project_area_required_error() -> str:
    """Return a standardized actionable error when project_area is missing."""
    return json.dumps(
        {
            "error": "project_area is required.",
            "hint": "Pass the project area name as a string (e.g., 'My Project (qm)'), "
            "or set the ETM_PROJECT_AREA environment variable. "
            "Call list_project_areas() to discover available project names.",
        }
    )


def invalid_id_error(param_name: str, value: str) -> str:
    """Return a standardized error when a resource ID is invalid or empty."""
    return json.dumps(
        {
            "error": f"{param_name} is required and must be a numeric webId.",
            "hint": f"Received: '{value}'. Use oslc_query_resources() to search for the resource and obtain its numeric webId.",
        }
    )


def collect_paginated_entries(
    endpoint: str,
    resource_type: str,
    params: Optional[dict[str, str]] = None,
    timeout: int = 120,
    max_items: int = 5000,
    configuration_context: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Collect entries across paginated ETM Atom feeds."""
    request_params = dict(params or {})
    request_params.setdefault("pageSize", "200")

    all_entries: list[dict[str, Any]] = []
    current_endpoint = endpoint
    current_params: Optional[dict[str, str]] = request_params
    max_pages = max(2, (max_items // 200) + 2)

    for _ in range(max_pages):
        response = make_request(
            current_endpoint,
            params=current_params,
            timeout=timeout,
            configuration_context=configuration_context,
        )
        entries, next_url = extract_entries_from_feed(response.text, resource_type)
        all_entries.extend(entries)

        if len(all_entries) >= max_items or not next_url:
            break

        current_endpoint = next_url
        current_params = None

    return all_entries[:max_items]


def fetch_all_pages(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
    page_size: int = 200,
    timeout: int = 180,
    max_pages: int = 100,
    configuration_context: Optional[str] = None,
) -> ET.Element:
    """Fetch ALL pages of an ETM Atom feed by following rel=next links."""
    ns_atom = "http://www.w3.org/2005/Atom"
    fetch_params: dict[str, Any] = dict(params or {})
    if "pageSize" not in fetch_params:
        fetch_params["pageSize"] = str(page_size)

    response = make_request(
        endpoint,
        params=fetch_params,
        accept_type="application/xml",
        timeout=timeout,
        configuration_context=configuration_context,
    )
    root = ET.fromstring(response.text)

    current = root
    pages_fetched = 1

    while pages_fetched < max_pages:
        next_url: Optional[str] = None
        for link in current.findall(f"{{{ns_atom}}}link"):
            if link.get("rel") == "next":
                next_url = link.get("href")
                break

        if not next_url:
            break

        next_response = make_request(
            next_url,
            accept_type="application/xml",
            timeout=timeout,
            configuration_context=configuration_context,
        )
        current = ET.fromstring(next_response.text)
        pages_fetched += 1

        for entry in current.findall(f"{{{ns_atom}}}entry"):
            root.append(entry)

    if pages_fetched >= max_pages:
        logger.warning(
            "fetch_all_pages: reached max_pages=%d limit — results may be incomplete for %s",
            max_pages,
            endpoint,
        )

    return root


# ============================================================================
# GENERIC CRUD OPERATIONS
# ============================================================================


def generic_list(
    resource_type: str,
    project_area: Optional[str] = None,
    limit: int = 50,
    page: int = 0,
    configuration_context: Optional[str] = None,
) -> str:
    """Generic list function for any ETM resource. Returns parsed JSON."""
    try:
        if not (1 <= limit <= 200):
            return json.dumps(
                {"error": "limit must be between 1 and 200", "hint": "Pass an integer between 1 and 200."}
            )

        project = (project_area or ETM_PROJECT_AREA or "").strip()
        if not project:
            return project_area_required_error()
        endpoint = build_resource_url(project, resource_type)
        params = {
            "abbreviate": "true",
            "pageSize": str(limit),
            "page": str(page),
        }
        response = make_request(endpoint, params=params, configuration_context=configuration_context)
        entries, next_url = extract_entries_from_feed(response.text, resource_type)
        result: dict[str, Any] = {
            "count": len(entries),
            "page": page,
            "page_size": limit,
            "entries": entries,
        }
        if next_url:
            result["has_more"] = True
        return json.dumps(result, indent=2)
    except Exception as e:
        return handle_error(f"list_{resource_type}", e)


def generic_get(
    resource_type: str,
    resource_id: str,
    project_area: Optional[str] = None,
    configuration_context: Optional[str] = None,
) -> str:
    """Generic get function for any ETM resource.

    IMPORTANT: resource_id must be the numeric webId (e.g., '3435411'), NOT the slug__ identifier.
    """
    try:
        if not resource_id.strip():
            return json.dumps({"error": f"{resource_type}_id is required"})

        project = (project_area or ETM_PROJECT_AREA or "").strip()
        if not project:
            return json.dumps({"error": "project_area is required"})
        endpoint = build_resource_url(project, resource_type, resource_id)
        response = make_request(endpoint, configuration_context=configuration_context)
        return parse_resource_to_json(response.text)
    except Exception as e:
        return handle_error(f"get_{resource_type}", e)


def generic_create(
    resource_type: str,
    title: str,
    description: str,
    project_area: Optional[str] = None,
    configuration_context: Optional[str] = None,
    **extra_fields: Any,
) -> str:
    """Generic create function for ETM resources.

    Returns JSON with resource_id. Resolves slug to numeric webId automatically.
    """
    try:
        project = (project_area or ETM_PROJECT_AREA or "").strip()
        if not project:
            return json.dumps({"error": "project_area is required"})
        endpoint = build_resource_url(project, resource_type)

        xml_payload = create_xml_resource(resource_type, title, description, **extra_fields)
        logger.info(f"Creating {resource_type}: '{title}'")

        response = make_request(
            endpoint,
            method="POST",
            data=xml_payload.encode("utf-8"),
            accept_type="application/xml",
            content_type="application/rdf+xml",
            timeout=60,
            configuration_context=configuration_context,
        )

        resource_id = extract_resource_id(response, resource_type)
        location = response.headers.get("Location", "")

        # If the extracted ID is a slug, do a follow-up GET to retrieve the
        # numeric webId that callers actually need for subsequent operations.
        web_id = resource_id
        if resource_id and ("slug__" in resource_id or resource_id.startswith("_")):
            logger.info(f"Got slug ID '{resource_id}', fetching numeric webId...")
            try:
                get_url = location or build_resource_url(project, resource_type, resource_id)
                get_resp = make_request(
                    get_url,
                    accept_type="application/xml",
                    configuration_context=configuration_context,
                )
                get_root = ET.fromstring(get_resp.text)
                web_id_elem = get_root.find(f".//{{{ETM_NAMESPACE}}}webId")
                if web_id_elem is not None and web_id_elem.text:
                    web_id = web_id_elem.text
                    logger.info(f"Resolved webId: {web_id}")
            except Exception as e:
                logger.warning(f"Could not resolve webId from slug '{resource_id}': {e}")

        result: dict[str, Any] = {
            "success": True,
            f"{resource_type}_id": web_id,
            "location": location,
            "message": f"{resource_type.title()} '{title}' created successfully",
        }
        if web_id != resource_id:
            result["slug_id"] = resource_id

        return json.dumps(result)
    except Exception as e:
        return handle_error(f"create_{resource_type}", e)


def generic_update(
    resource_type: str,
    resource_id: str,
    project_area: Optional[str] = None,
    configuration_context: Optional[str] = None,
    **updates: Any,
) -> str:
    """Generic update function for ETM resources.

    IMPORTANT: resource_id must be the numeric webId (e.g., '3435411'), NOT the slug__ identifier.
    """
    try:
        if not resource_id:
            return json.dumps({"error": f"{resource_type}_id is required"})

        project = (project_area or ETM_PROJECT_AREA or "").strip()
        if not project:
            return json.dumps({"error": "project_area is required"})
        endpoint = build_resource_url(project, resource_type, resource_id)

        response = make_request(endpoint, accept_type="application/xml", configuration_context=configuration_context)
        xml_text = strip_invalid_weight_fields(response.text)
        updated_xml = update_xml_resource(xml_text, **updates)

        etag = response.headers.get("ETag")
        put_headers = {"If-Match": etag} if etag else None

        logger.info(f"Updating {resource_type} {resource_id}")

        make_request(
            endpoint,
            method="PUT",
            data=updated_xml,
            accept_type="application/xml",
            content_type="application/rdf+xml",
            timeout=60,
            extra_headers=put_headers,
            configuration_context=configuration_context,
        )

        return json.dumps(
            {
                "success": True,
                f"{resource_type}_id": resource_id,
                "message": f"{resource_type.title()} updated successfully",
            }
        )
    except Exception as e:
        return handle_error(f"update_{resource_type}", e)


def generic_delete(
    resource_type: str,
    resource_id: str,
    project_area: Optional[str] = None,
    configuration_context: Optional[str] = None,
) -> str:
    """Generic delete function for ETM resources."""
    try:
        if not resource_id:
            return json.dumps({"error": f"{resource_type}_id is required"})

        project = (project_area or ETM_PROJECT_AREA or "").strip()
        if not project:
            return json.dumps({"error": "project_area is required"})
        endpoint = build_resource_url(project, resource_type, resource_id)
        make_request(endpoint, method="DELETE", timeout=60, configuration_context=configuration_context)

        return json.dumps(
            {
                "success": True,
                f"{resource_type}_id": resource_id,
                "message": f"{resource_type.title()} deleted successfully",
            }
        )
    except Exception as e:
        return handle_error(f"delete_{resource_type}", e)
