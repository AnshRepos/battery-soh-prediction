"""
Services package for ETM MCP Server.

Provides authentication, HTTP client, XML helpers, and OSLC discovery.
"""

from .auth import get_authenticated_session  # noqa: F401
from .etm_client import (  # noqa: F401
    build_category_href,
    build_resource_href,
    build_resource_url,
    collect_paginated_entries,
    extract_resource_id,
    fetch_all_pages,
    generic_create,
    generic_delete,
    generic_get,
    generic_list,
    generic_update,
    handle_error,
    make_request,
)
from .xml_helpers import (  # noqa: F401
    classify_execution_state,
    create_xml_resource,
    extract_entries_from_feed,
    find_custom_attribute_element,
    fix_et_corruption,
    fix_xml_raw,
    parse_resource_to_json,
    parse_test_case_details,
    strip_invalid_weight_fields,
    update_custom_attribute_in_xml,
    update_xml_resource,
    xml_element_to_dict,
)
