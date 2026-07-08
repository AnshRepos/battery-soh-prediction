"""
ETM OSLC Discovery & Query Service

Provides OSLC Service Provider discovery, OSLC QM query capabilities,
and OSLC Configuration Management (CM) component/configuration discovery.
"""

import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Optional

from core.config import (
    ETM_BASE_URL,
    OSLC_QM_NAMESPACE,
    OSLC_QM_RESOURCE_TYPES,
)
from services.etm_client import handle_error, make_request

logger = logging.getLogger(__name__)

# Cache for OSLC query capabilities (project_area -> {resource_type -> query_base_url})
_oslc_query_cache: dict[str, dict[str, str]] = {}

# Cache for OSLC service provider URLs (project_area -> service_provider_url)
_oslc_service_provider_cache: dict[str, str] = {}


def discover_oslc_service_provider(project_area: str) -> str:
    """Discover the OSLC Service Provider URL for a given project area.

    Navigates the OSLC Service Provider Catalog to find the service provider
    for the specified project area. Results are cached.
    """
    if project_area in _oslc_service_provider_cache:
        return _oslc_service_provider_cache[project_area]

    root_services_url = f"{ETM_BASE_URL}/rootservices"
    response = make_request(root_services_url, accept_type="application/rdf+xml")
    root = ET.fromstring(response.text)

    catalog_url = None
    for elem in root.iter():
        href = elem.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
        if href and "serviceProviderCatalog" in elem.tag.lower():
            catalog_url = href
            break
        if "serviceProviderCatalog" in elem.tag:
            catalog_url = href or elem.get("href") or (elem.text.strip() if elem.text else None)
            if catalog_url:
                break

    if not catalog_url:
        catalog_url = f"{ETM_BASE_URL}/oslc_qm/catalog"

    logger.info(f"OSLC catalog URL: {catalog_url}")

    response = make_request(catalog_url, accept_type="application/rdf+xml")
    catalog_root = ET.fromstring(response.text)

    ns = {
        "oslc": "http://open-services.net/ns/core#",
        "dcterms": "http://purl.org/dc/terms/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }

    for sp in catalog_root.findall(".//oslc:ServiceProvider", ns):
        title_elem = sp.find("dcterms:title", ns)
        if title_elem is not None and title_elem.text:
            if title_elem.text.strip() == project_area:
                sp_url = sp.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
                if sp_url:
                    _oslc_service_provider_cache[project_area] = sp_url
                    logger.info(f"Found OSLC Service Provider for '{project_area}': {sp_url}")
                    return sp_url

    for entry in catalog_root.findall(".//{http://open-services.net/ns/core#}ServiceProvider", ns):
        title_elem = entry.find("{http://purl.org/dc/terms/}title")
        if title_elem is not None and title_elem.text and title_elem.text.strip() == project_area:
            sp_url = entry.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")
            if sp_url:
                _oslc_service_provider_cache[project_area] = sp_url
                return sp_url

    raise ValueError(
        f"Could not find OSLC Service Provider for project area '{project_area}'. "
        "Verify the project area name matches exactly."
    )


def discover_oslc_query_base(project_area: str, resource_type: str) -> str:
    """Discover the OSLC query base URL for a resource type in a project area."""
    cache_key = project_area
    if cache_key in _oslc_query_cache and resource_type in _oslc_query_cache[cache_key]:
        return _oslc_query_cache[cache_key][resource_type]

    sp_url = discover_oslc_service_provider(project_area)

    response = make_request(sp_url, accept_type="application/rdf+xml")
    sp_root = ET.fromstring(response.text)

    ns = {
        "oslc": "http://open-services.net/ns/core#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    }

    if resource_type not in OSLC_QM_RESOURCE_TYPES:
        raise ValueError(
            f"Unknown resource type '{resource_type}'. Valid types: {', '.join(OSLC_QM_RESOURCE_TYPES.keys())}"
        )

    uri_to_key: dict[str, str] = {}
    for rtype, ruris in OSLC_QM_RESOURCE_TYPES.items():
        for ruri in ruris:
            uri_to_key[ruri] = rtype

    if cache_key not in _oslc_query_cache:
        _oslc_query_cache[cache_key] = {}

    for qc in sp_root.iter("{http://open-services.net/ns/core#}QueryCapability"):
        rt_uris = []
        for rt_elem in qc.findall("oslc:resourceType", ns):
            rt_uri = rt_elem.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", "")
            if rt_uri:
                rt_uris.append(rt_uri)

        query_base_elem = qc.find("oslc:queryBase", ns)
        if query_base_elem is not None:
            qb_url = query_base_elem.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource", "")
            if not qb_url:
                qb_url = query_base_elem.text.strip() if query_base_elem.text else ""

            if qb_url:
                for rt_uri in rt_uris:
                    matched_key = uri_to_key.get(rt_uri)
                    if matched_key:
                        _oslc_query_cache[cache_key][matched_key] = qb_url
                        logger.info(f"Discovered OSLC query base for {matched_key}: {qb_url}")

    if resource_type in _oslc_query_cache.get(cache_key, {}):
        return _oslc_query_cache[cache_key][resource_type]

    raise ValueError(
        f"Could not find OSLC query capability for '{resource_type}' in project '{project_area}'. "
        "The server may not support OSLC QM queries for this resource type."
    )


def oslc_query(
    resource_type: str,
    project_area: str,
    where: Optional[str] = None,
    select: Optional[str] = None,
    limit: int = 50,
    order_by: Optional[str] = None,
    configuration_context: Optional[str] = None,
) -> str:
    """Execute an OSLC QM query with server-side filtering and pagination."""
    project = project_area.strip()

    try:
        query_base = discover_oslc_query_base(project, resource_type)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    params: dict[str, str] = {}
    page_size = min(limit, 200)
    params["oslc.pageSize"] = str(page_size)

    if where:
        params["oslc.where"] = where
    if select:
        params["oslc.select"] = select
    if order_by:
        params["oslc.orderBy"] = order_by
    if configuration_context:
        params["oslc_config.context"] = configuration_context

    all_entries: list[dict[str, Any]] = []
    oslc_total_count: Optional[int] = None
    current_url = query_base
    current_params: Optional[dict[str, str]] = params
    max_pages = (limit // page_size) + 2

    try:
        for page_num in range(max_pages):
            response = make_request(
                current_url,
                params=current_params,
                accept_type="application/rdf+xml",
                timeout=120,
                configuration_context=configuration_context,
            )

            try:
                root = ET.fromstring(response.text)
            except ET.ParseError:
                if not all_entries:
                    return json.dumps({"error": "Could not parse OSLC query response", "raw": response.text[:1000]})
                break

            ns_rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
            ns_rdfs = "http://www.w3.org/2000/01/rdf-schema#"
            ns_oslc = "http://open-services.net/ns/core#"
            ns_dcterms = "http://purl.org/dc/terms/"

            # Extract totalCount from OSLC ResponseInfo metadata
            tc_elem = root.find(f".//{{{ns_oslc}}}totalCount")
            if tc_elem is not None and tc_elem.text:
                try:
                    oslc_total_count = int(tc_elem.text.strip())
                except ValueError:
                    pass

            members = root.findall(f".//{{{ns_rdfs}}}member")
            if members:
                # rdfs:member may wrap rdf:Description — unwrap to actual resource
                resolved = []
                for m in members:
                    inner = m.find(f"{{{ns_rdf}}}Description")
                    if inner is not None:
                        resolved.append(inner)
                    else:
                        resolved.append(m)
                members = resolved
            if not members:
                members = root.findall(f".//{{{ns_oslc}}}results/{{{ns_rdf}}}Description")
            if not members:
                members = root.findall(f".//{{{ns_rdf}}}Description")

            # Filter out OSLC ResponseInfo / query container nodes
            def _is_container(elem: ET.Element) -> bool:
                for child in elem:
                    child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    child_ns = child.tag.split("}")[0].lstrip("{") if "}" in child.tag else ""
                    if child_ns == ns_oslc and child_tag == "totalCount":
                        return True
                for t in elem.findall(f"{{{ns_rdf}}}type"):
                    if "ResponseInfo" in t.get(f"{{{ns_rdf}}}resource", ""):
                        return True
                return False

            members = [m for m in members if not _is_container(m)]

            # Strip query params to get the bare collection URL for comparison
            query_base_clean = current_url.split("?")[0] if current_url else ""

            for member in members:
                entry_data: dict[str, Any] = {}

                about = member.get(f"{{{ns_rdf}}}about") or member.get(f"{{{ns_rdf}}}resource")

                # Skip the collection container node (its URL matches the query base)
                if about and about.split("?")[0] == query_base_clean:
                    continue

                if about:
                    entry_data["url"] = about
                    parts_list = about.rstrip("/").split("/")
                    if parts_list and parts_list[-1].replace("slug__", ""):
                        entry_data["identifier"] = parts_list[-1]

                for child in member:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    ns_prefix = child.tag.split("}")[0].lstrip("{") if "}" in child.tag else ""

                    value = None
                    href = child.get(f"{{{ns_rdf}}}resource")
                    if href:
                        value = href
                    elif child.text and child.text.strip():
                        value = child.text.strip()

                    if value:
                        if ns_prefix == ns_dcterms:
                            entry_data[tag] = value
                        elif ns_prefix == OSLC_QM_NAMESPACE:
                            entry_data[f"qm_{tag}"] = value
                        elif tag not in ("type", "member"):
                            entry_data[tag] = value

                if entry_data:
                    all_entries.append(entry_data)

            next_url = None
            for elem in root.iter(f"{{{ns_oslc}}}nextPage"):
                next_url = elem.get(f"{{{ns_rdf}}}resource") or elem.text
                break

            if len(all_entries) >= limit or not next_url:
                break

            current_url = next_url
            current_params = None

        all_entries = all_entries[:limit]

        result: dict[str, Any] = {
            "count": len(all_entries),
            f"{resource_type}s": all_entries,
            "limit": limit,
            "truncated": len(all_entries) == limit,
            "query": {"where": where, "select": select},
        }
        if oslc_total_count is not None:
            result["totalCount"] = oslc_total_count
        return json.dumps(result, indent=2)

    except Exception as e:
        return handle_error("oslc_query", e)


# ============================================================================
# OSLC Configuration Management (CM) — Component & Configuration Discovery
#
# ETM exposes CM via a dedicated OSLC service provider catalog declared in
# /qm/rootservices as  oslc_config:cmServiceProviders.
#
# A project can have multiple components, each with its own streams and
# baselines. A local ETM stream URI works directly as configuration_context.
#
# Discovery workflow:
#   1. list_project_areas()           → project_area_uri
#   2. discover_components_via_feed()  → list of components (via ATOM feed)
#   3. For each component, fetch its oslc_config:configurations LDP container
#      → list of streams/baselines
#   4. Use a stream's URI as configuration_context in ETM requests
#
# Component discovery
#  ETM ATOM feed: /resources/{project_uuid}/component (returns all components)
#
# Each local configuration carries:
#   - oslc_config:component   → component URI
#   - process:projectArea     → project area URI
#   - rdf:type                → oslc_config:Stream or oslc_config:Baseline
#   - dcterms:title           → human-readable name
# ============================================================================

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
NS_DCTERMS = "http://purl.org/dc/terms/"
NS_OSLC = "http://open-services.net/ns/core#"
NS_OSLC_CONFIG = "http://open-services.net/ns/config#"
NS_PROCESS = "http://jazz.net/ns/process#"


def _parse_cm_configurations(root: ET.Element) -> list[dict[str, str]]:
    """Parse configuration RDF/XML response into a list of configuration dicts.

    Each rdf:Description with rdf:type oslc_config:Configuration (or Stream/Baseline)
    is extracted.

    Args:
        root: Parsed XML root element.

    Returns:
        List of configuration dicts with keys like configuration_context, title,
        type, component_uri, project_area_uri, etc.
    """
    ns_rdf_resource = f"{{{NS_RDF}}}resource"
    ns_rdf_type = f"{{{NS_RDF}}}type"

    # Collect member URIs from ResponseInfo
    member_uris: set[str] = set()
    for member in root.iter(f"{{{NS_RDFS}}}member"):
        uri = member.get(ns_rdf_resource, "")
        if uri:
            member_uris.add(uri)

    configurations: list[dict[str, str]] = []

    for desc in root.iter(f"{{{NS_RDF}}}Description"):
        about = desc.get(f"{{{NS_RDF}}}about", "")

        # Skip ResponseInfo entries (they don't have rdf:about matching a config URI)
        if not about:
            continue

        # Determine if this is a Configuration type
        types: set[str] = set()
        for type_elem in desc.findall(ns_rdf_type):
            type_uri = type_elem.get(ns_rdf_resource, "")
            if type_uri:
                types.add(type_uri)

        is_configuration = (
            f"{NS_OSLC_CONFIG}Configuration" in types
            or f"{NS_OSLC_CONFIG}Stream" in types
            or f"{NS_OSLC_CONFIG}Baseline" in types
        )
        if not is_configuration:
            continue

        config_info: dict[str, str] = {"configuration_context": about}

        # Determine type
        if f"{NS_OSLC_CONFIG}Stream" in types:
            config_info["type"] = "stream"
        elif f"{NS_OSLC_CONFIG}Baseline" in types:
            config_info["type"] = "baseline"
        else:
            config_info["type"] = "configuration"

        # Title
        title_elem = desc.find(f"{{{NS_DCTERMS}}}title")
        if title_elem is not None and title_elem.text:
            config_info["title"] = title_elem.text.strip()

        # Component
        comp_elem = desc.find(f"{{{NS_OSLC_CONFIG}}}component")
        if comp_elem is not None:
            comp_uri = comp_elem.get(ns_rdf_resource, "")
            if comp_uri:
                config_info["component_uri"] = comp_uri

        # Project area
        pa_elem = desc.find(f"{{{NS_PROCESS}}}projectArea")
        if pa_elem is not None:
            pa_uri = pa_elem.get(ns_rdf_resource, "")
            if pa_uri:
                config_info["project_area_uri"] = pa_uri

        # Identifier
        id_elem = desc.find(f"{{{NS_DCTERMS}}}identifier")
        if id_elem is not None and id_elem.text:
            config_info["identifier"] = id_elem.text.strip()

        # Mutable flag
        mutable_elem = desc.find(f"{{{NS_OSLC_CONFIG}}}mutable")
        if mutable_elem is not None and mutable_elem.text:
            config_info["mutable"] = mutable_elem.text.strip()

        # Created / modified dates
        for date_prop in ("created", "modified"):
            date_elem = desc.find(f"{{{NS_DCTERMS}}}{date_prop}")
            if date_elem is not None and date_elem.text:
                config_info[date_prop] = date_elem.text.strip()

        configurations.append(config_info)

    return configurations


def _parse_cm_components(root: ET.Element) -> list[dict[str, str]]:
    """Parse component RDF/XML response into a list of component dicts.

    Args:
        root: Parsed XML root element.

    Returns:
        List of component dicts with keys like component_uri, title,
        project_area_uri, etc.
    """
    ns_rdf_resource = f"{{{NS_RDF}}}resource"
    ns_rdf_type = f"{{{NS_RDF}}}type"

    components: list[dict[str, str]] = []

    for desc in root.iter(f"{{{NS_RDF}}}Description"):
        about = desc.get(f"{{{NS_RDF}}}about", "")
        if not about:
            continue

        types: set[str] = set()
        for type_elem in desc.findall(ns_rdf_type):
            type_uri = type_elem.get(ns_rdf_resource, "")
            if type_uri:
                types.add(type_uri)

        if f"{NS_OSLC_CONFIG}Component" not in types:
            continue

        comp_info: dict[str, str] = {"component_uri": about}

        title_elem = desc.find(f"{{{NS_DCTERMS}}}title")
        if title_elem is not None and title_elem.text:
            comp_info["title"] = title_elem.text.strip()

        pa_elem = desc.find(f"{{{NS_PROCESS}}}projectArea")
        if pa_elem is not None:
            pa_uri = pa_elem.get(ns_rdf_resource, "")
            if pa_uri:
                comp_info["project_area_uri"] = pa_uri

        id_elem = desc.find(f"{{{NS_DCTERMS}}}identifier")
        if id_elem is not None and id_elem.text:
            comp_info["identifier"] = id_elem.text.strip()

        # Configurations URL (to fetch configurations for this component)
        configs_elem = desc.find(f"{{{NS_OSLC_CONFIG}}}configurations")
        if configs_elem is not None:
            configs_url = configs_elem.get(ns_rdf_resource, "")
            if configs_url:
                comp_info["configurations_url"] = configs_url

        components.append(comp_info)

    return components


def discover_components_via_feed(project_area_uri: str) -> list[dict[str, str]]:
    """Discover ALL components for a project via the ETM integration feed.

    Queries the ETM ATOM feed at
    /resources/{project_uuid}/component
    which returns all components in the project — not just the default.

    For each component found, fetches the CM component resource to get
    the OSLC config details (configurations URL, title, etc.).

    Args:
        project_area_uri: Project area URI.

    Returns:
        List of component dicts with component_uri, title, configurations_url.
    """
    ns_rdf_resource = f"{{{NS_RDF}}}resource"

    project_uuid = ""
    if "/process/project-areas/" in project_area_uri:
        project_uuid = project_area_uri.split("/process/project-areas/")[-1].strip("/")
    if not project_uuid:
        return []

    try:
        feed_url = (
            f"{ETM_BASE_URL}/service/com.ibm.rqm.integration.service.IIntegrationService"
            f"/resources/{project_uuid}/component"
        )
        response = make_request(feed_url, accept_type="application/xml", timeout=30)
        root = ET.fromstring(response.text)

        # Parse ATOM feed entries — each entry is a component
        ns_atom = "http://www.w3.org/2005/Atom"
        components: list[dict[str, str]] = []
        seen_uris: set[str] = set()

        for entry in root.iter(f"{{{ns_atom}}}entry"):
            comp_info: dict[str, str] = {}

            title_elem = entry.find(f"{{{ns_atom}}}title")
            if title_elem is not None and title_elem.text:
                comp_info["title"] = title_elem.text.strip()

            # The entry ID or content link points to the component
            id_elem = entry.find(f"{{{ns_atom}}}id")
            entry_id = id_elem.text.strip() if id_elem is not None and id_elem.text else ""

            # Look for the component UUID in the content or links
            content_elem = entry.find(f"{{{ns_atom}}}content")
            content_src = content_elem.get("src", "") if content_elem is not None else ""

            # Extract component UUID from the entry — the ATOM feed uses
            # /resources/{project}/component/{uuid} pattern
            comp_uuid = ""
            for candidate in (entry_id, content_src):
                if "/component/" in candidate:
                    comp_uuid = candidate.split("/component/")[-1].strip("/")
                    break

            if comp_uuid and comp_uuid not in seen_uris:
                seen_uris.add(comp_uuid)
                # Build the OSLC config component URI
                cm_comp_uri = f"{ETM_BASE_URL}/oslc_config/resources/com.ibm.team.vvc.Component/{comp_uuid}"
                comp_info["component_uri"] = cm_comp_uri

                # Fetch the CM component resource for configurations URL
                try:
                    comp_response = make_request(
                        cm_comp_uri,
                        accept_type="application/rdf+xml",
                        timeout=30,
                    )
                    comp_root = ET.fromstring(comp_response.text)

                    # Try standard oslc_config:Component parsing
                    parsed = _parse_cm_components(comp_root)
                    if parsed:
                        components.extend(parsed)
                        continue

                    # Fallback: parse rdf:Description
                    for desc in comp_root.iter(f"{{{NS_RDF}}}Description"):
                        about = desc.get(f"{{{NS_RDF}}}about", "")
                        if about and about == cm_comp_uri:
                            title_d = desc.find(f"{{{NS_DCTERMS}}}title")
                            if title_d is not None and title_d.text:
                                comp_info["title"] = title_d.text.strip()
                            pa_elem = desc.find(f"{{{NS_PROCESS}}}projectArea")
                            if pa_elem is not None:
                                comp_info["project_area_uri"] = pa_elem.get(
                                    ns_rdf_resource,
                                    "",
                                )
                            configs_elem = desc.find(
                                f"{{{NS_OSLC_CONFIG}}}configurations",
                            )
                            if configs_elem is not None:
                                comp_info["configurations_url"] = configs_elem.get(
                                    ns_rdf_resource,
                                    "",
                                )
                            break
                except Exception as e:
                    logger.warning("Could not fetch CM details for component %s: %s", comp_uuid, e)
                    comp_info["error"] = str(e)

                components.append(comp_info)

        if components:
            logger.info(
                "Discovered %d component(s) via ETM feed for %s",
                len(components),
                project_area_uri,
            )
        return components

    except Exception as e:
        logger.warning("ETM component feed discovery failed for %s: %s", project_area_uri, e)
        return []


def discover_component_configurations(
    component_uri: Optional[str] = None,
    project_area_uri: Optional[str] = None,
) -> list[dict[str, str]]:
    """List CM configurations (streams and baselines) for an ETM component.

    Args:
        component_uri: Optional component URI to filter configurations.
        project_area_uri: Optional project area URI to discover components first.
            When provided, discovers ALL components and lists their configs.

    Returns:
        List of configuration dicts sorted with streams first, then baselines.
    """
    configurations: list[dict[str, str]] = []

    # If we have a component_uri, try LDP container first
    if component_uri:
        configurations = _fetch_configurations_via_ldp(component_uri)

    # If no component_uri but project_area_uri, discover ALL components and
    # collect configurations from each one
    if not configurations and project_area_uri:
        components = discover_components_via_feed(project_area_uri)
        for comp in components:
            comp_uri = comp.get("component_uri", "")
            if comp_uri:
                comp_configs = _fetch_configurations_via_ldp(comp_uri)
                configurations.extend(comp_configs)

    # Client-side filter by project area if specified
    if project_area_uri and configurations:
        filtered = [c for c in configurations if c.get("project_area_uri", "") == project_area_uri]
        if filtered:
            configurations = filtered

    # Sort: streams first, then baselines
    streams = [c for c in configurations if c.get("type") == "stream"]
    baselines = [c for c in configurations if c.get("type") == "baseline"]
    others = [c for c in configurations if c.get("type") not in ("stream", "baseline")]

    return streams + baselines + others


def _fetch_configurations_via_ldp(component_uri: str) -> list[dict[str, str]]:
    """Fetch configurations from a component's LDP configurations container.

    Each ETM component has an oslc_config:configurations property pointing to
    an LDP BasicContainer that lists all local configurations (streams and
    baselines) as ldp:contains members.

    This approach bypasses the global Configuration query (which may return 403).

    Args:
        component_uri: Component URI.

    Returns:
        List of configuration dicts with full details.
    """
    ns_rdf_resource = f"{{{NS_RDF}}}resource"
    ns_ldp = "http://www.w3.org/ns/ldp#"

    # Step 1: Get the configurations URL from the component resource
    configs_url = None
    try:
        comp_response = make_request(component_uri, accept_type="application/rdf+xml", timeout=30)
        comp_root = ET.fromstring(comp_response.text)
        for desc in comp_root.iter(f"{{{NS_RDF}}}Description"):
            configs_elem = desc.find(f"{{{NS_OSLC_CONFIG}}}configurations")
            if configs_elem is not None:
                configs_url = configs_elem.get(ns_rdf_resource, "")
                if configs_url:
                    break
    except Exception as e:
        logger.warning("Failed to fetch component %s: %s", component_uri, e)
        return []

    if not configs_url:
        logger.warning("No configurations URL found for component %s", component_uri)
        return []

    # Step 2: Fetch the LDP container to get configuration member URIs
    try:
        ldp_response = make_request(configs_url, accept_type="application/rdf+xml", timeout=30)
        ldp_root = ET.fromstring(ldp_response.text)
    except Exception as e:
        logger.warning("Failed to fetch configurations container %s: %s", configs_url, e)
        return []

    config_uris: list[str] = []
    for contains in ldp_root.iter(f"{{{ns_ldp}}}contains"):
        uri = contains.get(ns_rdf_resource, "")
        if uri:
            config_uris.append(uri)

    # Step 3: Fetch each configuration resource for full details
    configurations: list[dict[str, str]] = []
    for cfg_uri in config_uris:
        try:
            cfg_response = make_request(cfg_uri, accept_type="application/rdf+xml", timeout=30)
            cfg_root = ET.fromstring(cfg_response.text)
            parsed = _parse_cm_configurations(cfg_root)
            if parsed:
                configurations.extend(parsed)
            else:
                # Manual extraction from rdf:Description
                for desc in cfg_root.iter(f"{{{NS_RDF}}}Description"):
                    about = desc.get(f"{{{NS_RDF}}}about", "")
                    if about != cfg_uri:
                        continue
                    config_info: dict[str, str] = {"configuration_context": about}
                    types: set[str] = set()
                    for t in desc.findall(f"{{{NS_RDF}}}type"):
                        types.add(t.get(ns_rdf_resource, ""))
                    if f"{NS_OSLC_CONFIG}Stream" in types:
                        config_info["type"] = "stream"
                    elif f"{NS_OSLC_CONFIG}Baseline" in types:
                        config_info["type"] = "baseline"
                    else:
                        config_info["type"] = "configuration"
                    title_elem = desc.find(f"{{{NS_DCTERMS}}}title")
                    if title_elem is not None and title_elem.text:
                        config_info["title"] = title_elem.text.strip()
                    comp_elem = desc.find(f"{{{NS_OSLC_CONFIG}}}component")
                    if comp_elem is not None:
                        config_info["component_uri"] = comp_elem.get(ns_rdf_resource, "")
                    pa_elem = desc.find(f"{{{NS_PROCESS}}}projectArea")
                    if pa_elem is not None:
                        config_info["project_area_uri"] = pa_elem.get(ns_rdf_resource, "")
                    id_elem = desc.find(f"{{{NS_DCTERMS}}}identifier")
                    if id_elem is not None and id_elem.text:
                        config_info["identifier"] = id_elem.text.strip()
                    configurations.append(config_info)
                    break
        except Exception as e:
            logger.warning("Failed to fetch configuration %s: %s", cfg_uri, e)
            configurations.append({"configuration_context": cfg_uri, "error": str(e)})

    logger.info("Fetched %d configuration(s) via LDP for component %s", len(configurations), component_uri)
    return configurations
