"""
ETM XML Helper Functions

Provides XML parsing, building, and manipulation utilities for ETM resources.
Uses string/regex manipulation instead of ElementTree re-serialization to
preserve rich HTML content in ETM sections.
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Optional
from xml.sax.saxutils import escape

from core.config import (
    ALM_NAMESPACE,
    ETM_NAMESPACE,
    ETM_NAMESPACES,
    OSLC_QM_NAMESPACE,
)


def create_xml_resource(
    resource_type: str,
    title: str,
    description: str,
    categories: Optional[list[dict[str, str]]] = None,
    **extra_fields: Any,
) -> str:
    """Generate XML payload for creating ETM resources."""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<qm:{resource_type} xmlns:qm="{ETM_NAMESPACE}" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{escape(title)}</dc:title>
    <dc:description>{escape(description)}</dc:description>"""

    if categories:
        for cat in categories:
            term = escape(cat.get("term", ""))
            value = escape(cat.get("value", ""))
            href = cat.get("href", "")
            if href:
                xml += f'\n    <qm:category term="{term}" value="{value}" href="{href}"/>'
            else:
                xml += f'\n    <qm:category term="{term}" value="{value}"/>'

    for field, value in extra_fields.items():
        if value:
            if field.startswith("href_"):
                ref_type = field[5:]
                xml += f'\n    <qm:{ref_type} href="{value}"/>'
            else:
                xml += f"\n    <qm:{field}>{escape(str(value))}</qm:{field}>"

    xml += f"\n</qm:{resource_type}>"
    return xml


# ---------------------------------------------------------------------------
# AI-CHANGED (GitHub Copilot / Claude Opus 4.6) — 2026-03-11
# Replaced ElementTree-based _update_xml_resource with string/regex approach.
# Root cause: ET.fromstring() + ET.tostring() re-serializes the ENTIRE XML
# document, rewriting namespace prefixes and injecting spurious xmlns:html
# declarations into rich-text XHTML sections.
# ---------------------------------------------------------------------------
_RICH_TEXT_SECTION_MAP: dict[str, str] = {
    "precondition": "com.ibm.rqm.planning.editor.section.testCasePreCondition",
    "postcondition": "com.ibm.rqm.planning.editor.section.testCasePostCondition",
    "expected_results": "com.ibm.rqm.planning.editor.section.testCaseExpectedResults",
    "test_case_design": "com.ibm.rqm.planning.editor.section.testCaseDesign",
}


def _wrap_xhtml(text: str) -> str:
    """Wrap plain text in XHTML div suitable for ETM rich text sections."""
    return f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{escape(text)}</p></div>'


def _wrap_xhtml_raw(html_content: str) -> str:
    """Wrap raw HTML in XHTML div suitable for ETM rich text sections.
    
    Does NOT escape the content - use for pre-formatted HTML like tables or lists.
    If content already has xmlns declaration, use as-is.
    """
    if 'xmlns="http://www.w3.org/1999/xhtml"' in html_content:
        return html_content
    return f'<div xmlns="http://www.w3.org/1999/xhtml">{html_content}</div>'


def _is_html_content(text: str) -> bool:
    """Check if text contains HTML tags (indicating it's pre-formatted HTML)."""
    html_tags = ['<p', '<div', '<table', '<ol', '<ul', '<h1', '<h2', '<h3', '<br', '<span']
    text_lower = text.lower()
    return any(tag in text_lower for tag in html_tags)


def update_xml_resource(xml_text: str, **updates: Any) -> bytes:
    """Update XML resource with new field values using string manipulation.

    IMPORTANT: Does NOT use ElementTree re-serialization to avoid corrupting
    rich HTML content in ETM sections (testCaseDesign, Review Criteria, etc.).
    
    Automatically detects HTML content in rich text fields and preserves it without escaping.
    """
    result = xml_text

    for field, value in updates.items():
        if not value:
            continue

        if field in _RICH_TEXT_SECTION_MAP:
            section_tag = _RICH_TEXT_SECTION_MAP[field]
            # Check if content is already HTML (contains HTML tags)
            value_str = str(value)
            if _is_html_content(value_str):
                xhtml_content = _wrap_xhtml_raw(value_str)
            else:
                xhtml_content = _wrap_xhtml(value_str)
            # Match with any namespace prefix (ns2:, qm:, etc.) or unprefixed
            tag_re = re.compile(
                r"(<(?:\w+:)?" + re.escape(section_tag) + r"(?:\s[^>]*)?>)(.*?)"
                r"(</(?:\w+:)?" + re.escape(section_tag) + r">)",
                re.DOTALL,
            )
            m = tag_re.search(result)
            if m:
                result = result[: m.start()] + m.group(1) + xhtml_content + m.group(3) + result[m.end() :]
            else:
                # Section does not exist yet — insert before root closing tag
                new_elem = f"<ns2:{section_tag}>{xhtml_content}</ns2:{section_tag}>"
                root_close_re = re.compile(r"(</(?:ns2|qm):\w+>)\s*$")
                result = root_close_re.sub(new_elem + r"\g<1>", result)
        elif field in ["title", "description"]:
            escaped_value = escape(str(value))
            tag_re = re.compile(
                r"(<\w+:" + re.escape(field) + r"(?:\s[^>]*)?>)(.*?)(</\w+:" + re.escape(field) + r">)",
                re.DOTALL,
            )
            m = tag_re.search(result)
            if m:
                result = result[: m.start()] + m.group(1) + escaped_value + m.group(3) + result[m.end() :]
            else:
                dc_ns_re = re.compile(r'\sxmlns:(\w+)="http://purl\.org/dc/elements/1\.1/"')
                dc_match = dc_ns_re.search(result)
                if dc_match:
                    dc_prefix = dc_match.group(1)
                    new_elem = f"<{dc_prefix}:{field}>{escaped_value}</{dc_prefix}:{field}>"
                else:
                    new_elem = f'<dc:{field} xmlns:dc="http://purl.org/dc/elements/1.1/">{escaped_value}</dc:{field}>'
                root_close_re = re.compile(r"(</ns2:\w+>)\s*$")
                result = root_close_re.sub(new_elem + r"\g<1>", result)
        else:
            escaped_value = escape(str(value))
            tag_re = re.compile(
                r"(<ns2:" + re.escape(field) + r"(?:\s[^>]*)?>)(.*?)(</ns2:" + re.escape(field) + r">)",
                re.DOTALL,
            )
            m = tag_re.search(result)
            if m:
                result = result[: m.start()] + m.group(1) + escaped_value + m.group(3) + result[m.end() :]
            else:
                root_close_re = re.compile(r"(</ns2:\w+>)\s*$")
                result = root_close_re.sub(f"<ns2:{field}>{escaped_value}</ns2:{field}>" + r"\g<1>", result)

    return result.encode("utf-8")


# ----------------------------------------------------------------------------
# AI-CHANGED (GitHub Copilot / Claude Sonnet 4.6) — 2026-03-13
# Strips weight elements that ETM rejects on PUT.
# ----------------------------------------------------------------------------
def strip_invalid_weight_fields(xml_text: str) -> str:
    """Strip weight elements that ETM rejects on PUT.

    Some test cases contain two weight elements: a prefixed <ns2:weight>100</ns2:weight>
    and an unprefixed extension <weight xmlns="..." extensionDisplayName="weight">...</weight>.
    When PUT back, ETM returns 400 "Property 'Weight' is invalid." for both forms.
    """
    result = re.sub(r"<\w+:weight[^>]*>.*?</\w+:weight>", "", xml_text, flags=re.DOTALL)
    result = re.sub(r"<weight[^>]*>.*?</weight>", "", result, flags=re.DOTALL)
    return result


def fix_xml_raw(xml_text: str) -> str:
    """Strip ETM weight extension element and repair html: XHTML prefix corruption.

    Apply to r.text BEFORE PUT. Do NOT use ET.fromstring() / ET.tostring() on TC
    XML — use raw-string regex for all field changes. See etm-put-safety skill.
    """
    # Remove block weight extension element (with open+close tags and optional body)
    xml_text = re.sub(
        r'<(\w+(?::\w+)?)(?:\s[^>]*)?\sextensionDisplayName=["\']weight["\'][^>]*>.*?</\1>',
        "",
        xml_text,
        flags=re.DOTALL,
    )
    # Remove self-closing weight extension element
    xml_text = re.sub(
        r'<\w+(?::\w+)?(?:\s[^>]*)?\sextensionDisplayName=["\']weight["\'][^>]*/\s*>',
        "",
        xml_text,
    )
    # Repair html: namespace prefix that ET.tostring() re-adds to XHTML inline content
    # e.g.  <html:div> → <div>   </html:p> → </p>
    xml_text = re.sub(r"<(html:)([A-Za-z])", r"<\2", xml_text)
    xml_text = re.sub(r"</(html:)([A-Za-z])", r"</\2", xml_text)
    return xml_text


# AI-constructed: entire function below was written by AI (GitHub Copilot / Claude Opus 4.6)
def fix_et_corruption(xml_text: str) -> tuple[str, list[str]]:
    """Detect and fix ET re-serialization corruption in ETM test case XML.

    Scans for the four known corruption patterns caused by
    xml.etree.ElementTree and applies targeted string/regex fixes.
    """
    fixes: list[str] = []
    result = xml_text

    # --- Pattern 1: html:-prefixed XHTML tags ---
    html_prefixed_count = len(re.findall(r"<html:\w+", result)) + len(re.findall(r"</html:\w+>", result))
    if html_prefixed_count > 0:
        wrapper_re = re.compile(r'<html:div\s+xmlns:html="http://www\.w3\.org/1999/xhtml"[^>]*>')
        wrapper_count = len(wrapper_re.findall(result))
        result = wrapper_re.sub("", result)

        for _ in range(wrapper_count):
            result = re.sub(
                r"</html:div>\s*(</com\.ibm\.rqm\.)",
                r"\1",
                result,
                count=1,
            )

        open_count = len(re.findall(r"<html:\w+", result))
        close_count = len(re.findall(r"</html:\w+>", result))
        result = re.sub(r"<html:(\w+)", r"<\1", result)
        result = re.sub(r"</html:(\w+)>", r"</\1>", result)
        fixes.append(
            f"Removed {wrapper_count} ET-injected wrapper(s), "
            f"converted {open_count + close_count} html:-prefixed tags to plain"
        )

    # --- Pattern 2: Leaked internal namespace declarations ---
    content_div_re = re.compile(r'(<div\s+xmlns="http://www\.w3\.org/1999/xhtml")([^>]*>)')
    leaked_total = 0

    def _clean_leaked_ns(m: re.Match) -> str:
        nonlocal leaked_total
        prefix = m.group(1)
        rest = m.group(2)
        cleaned = re.sub(r'\s+xmlns:(?:ns\d+|dc|rdf)="[^"]*"', "", rest)
        leaked_total += len(rest) - len(cleaned)
        return prefix + cleaned

    result = content_div_re.sub(_clean_leaked_ns, result)
    if leaked_total > 0:
        fixes.append("Removed leaked internal namespace declarations from content divs")

    # --- Pattern 3: Missing MS Office namespace declarations ---
    office_ns_str = (
        ' xmlns:o="urn:schemas-microsoft-com:office:office"'
        ' xmlns:st1="urn:schemas-microsoft-com:office:smarttags"'
        ' xmlns:v="urn:schemas-microsoft-com:vml"'
        ' xmlns:w="urn:schemas-microsoft-com:office:word"'
    )
    outer_div_re = re.compile(r'<div\s+xmlns="http://www\.w3\.org/1999/xhtml"(?:\s+xmlns:\w+="[^"]*")*\s*>')
    ns_fixed = 0

    def _restore_office_ns(m: re.Match) -> str:
        nonlocal ns_fixed
        tag = m.group(0)
        if "xmlns:o=" not in tag:
            ns_fixed += 1
            return tag[:-1] + office_ns_str + ">"
        return tag

    result = outer_div_re.sub(_restore_office_ns, result)
    if ns_fixed > 0:
        fixes.append(f"Restored MS Office namespace declarations on {ns_fixed} outer div(s)")

    return result, fixes


def find_custom_attribute_element(root: ET.Element, attribute_name: str) -> Optional[ET.Element]:
    """Find a custom attribute element by name in an ETM XML tree."""
    ns = {"ns2": ETM_NAMESPACE}
    for custom_attr in root.findall(".//ns2:customAttributes/ns2:customAttribute", ns):
        name_elem = custom_attr.find("ns2:name", ns)
        if name_elem is not None and name_elem.text == attribute_name:
            return custom_attr
    return None


def update_custom_attribute_in_xml(xml_text: str, attribute_name: str, value: str, append: bool = False) -> bytes:
    """Update (or create) a custom attribute value in ETM test case XML.

    Uses string/regex manipulation instead of ElementTree to preserve all
    namespace declarations and XML formatting.
    """
    escaped_value = escape(value)
    attr_name_re = re.escape(attribute_name)

    block_re = re.compile(r"(<ns2:customAttribute\b[^>]*>)(.*?)(</ns2:customAttribute>)", re.DOTALL)
    name_re = re.compile(r"<ns2:name>" + attr_name_re + r"</ns2:name>")
    value_re = re.compile(r"(<ns2:value>)(.*?)(</ns2:value>)", re.DOTALL)

    found = [False]

    def replace_block(m: re.Match) -> str:
        block_open, block_inner, block_close = m.group(1), m.group(2), m.group(3)
        if not name_re.search(block_inner):
            return m.group(0)
        found[0] = True

        vm = value_re.search(block_inner)
        if vm:
            if append and vm.group(2):
                new_raw = vm.group(2) + "; " + escaped_value
            else:
                new_raw = escaped_value
            new_inner = block_inner[: vm.start()] + vm.group(1) + new_raw + vm.group(3) + block_inner[vm.end() :]
        else:
            new_inner = name_re.sub(
                f"<ns2:name>{escape(attribute_name)}</ns2:name><ns2:value>{escaped_value}</ns2:value>",
                block_inner,
                count=1,
            )
        return block_open + new_inner + block_close

    result = block_re.sub(replace_block, xml_text)

    if not found[0]:
        new_block = (
            f"<ns2:customAttribute>"
            f"<ns2:name>{escape(attribute_name)}</ns2:name>"
            f"<ns2:value>{escaped_value}</ns2:value>"
            f"</ns2:customAttribute>"
        )
        closing_tag = "</ns2:customAttributes>"
        if closing_tag in result:
            result = result.replace(closing_tag, new_block + closing_tag, 1)
        else:
            raise ValueError(f"Cannot find </ns2:customAttributes> to insert new attribute '{attribute_name}'")

    return result.encode("utf-8")


def xml_element_to_dict(element: ET.Element) -> dict[str, Any]:
    """Convert an XML element and its children to a flat dictionary."""
    result: dict[str, Any] = {}

    for attr_name, attr_value in element.attrib.items():
        clean_name = attr_name.split("}")[-1] if "}" in attr_name else attr_name
        result[clean_name] = attr_value

    for child in element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if child.text and child.text.strip():
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child.text.strip())
            else:
                result[tag] = child.text.strip()
        elif child.attrib:
            href = child.get("href", "")
            if href:
                if tag in result:
                    if not isinstance(result[tag], list):
                        result[tag] = [result[tag]]
                    result[tag].append(href)
                else:
                    result[tag] = href
            else:
                child_dict = {k.split("}")[-1] if "}" in k else k: v for k, v in child.attrib.items()}
                result[tag] = child_dict
        elif len(child) > 0:
            result[tag] = xml_element_to_dict(child)

    return result


def extract_entries_from_feed(xml_text: str, resource_type: str) -> tuple[list[dict[str, Any]], Optional[str]]:
    """Parse an Atom feed and extract entries + next page URL."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], None

    next_url = None
    for link in root.findall("atom:link", ETM_NAMESPACES):
        if link.get("rel") == "next":
            next_url = link.get("href")
            break

    entries = root.findall(".//atom:entry", ETM_NAMESPACES)

    if not entries:
        resources = root.findall(f".//qm:{resource_type}", ETM_NAMESPACES)
        if resources:
            return [xml_element_to_dict(r) for r in resources], None
        root_data = xml_element_to_dict(root)
        if root_data:
            return [root_data], None
        return [], None

    parsed_entries = []
    for entry in entries:
        entry_data: dict[str, Any] = {}

        atom_id = entry.find("atom:id", ETM_NAMESPACES)
        if atom_id is not None and atom_id.text:
            entry_data["id"] = atom_id.text

        atom_title = entry.find("atom:title", ETM_NAMESPACES)
        if atom_title is not None and atom_title.text:
            entry_data["title"] = atom_title.text

        atom_updated = entry.find("atom:updated", ETM_NAMESPACES)
        if atom_updated is not None and atom_updated.text:
            entry_data["updated"] = atom_updated.text

        resource_elem = entry.find(f".//qm:{resource_type}", ETM_NAMESPACES)
        if resource_elem is None:
            content = entry.find("atom:content", ETM_NAMESPACES)
            if content is not None:
                resource_elem = content.find(f".//qm:{resource_type}", ETM_NAMESPACES)

        if resource_elem is not None:
            resource_data = xml_element_to_dict(resource_elem)
            entry_data.update(resource_data)

        if entry_data:
            parsed_entries.append(entry_data)

    return parsed_entries, next_url


def classify_execution_state(state_str: str) -> str:
    """Classify an ETM execution state string into a bucket."""
    state = state_str.lower()
    if "passed" in state:
        return "passed"
    if "failed" in state:
        return "failed"
    if "blocked" in state:
        return "blocked"
    return "incomplete"


def parse_resource_to_json(xml_text: str) -> str:
    """Parse a single resource XML response into structured JSON."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return json.dumps({"raw_response": xml_text[:2000], "parse_error": "Could not parse XML response"})

    resource_data = xml_element_to_dict(root)
    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    resource_data["_type"] = tag

    return json.dumps(resource_data, indent=2)


def parse_test_case_details(root: ET.Element) -> dict[str, Any]:
    """Extract detailed test case fields from an ETM test case XML element."""
    ns = {
        "qm": ETM_NAMESPACE,
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
        "oslc_qm": OSLC_QM_NAMESPACE,
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "alm": ALM_NAMESPACE,
    }

    details: dict[str, Any] = {}

    # --- Basic text fields ---
    for tag, key in [
        (".//dc:title", "title"),
        (".//dc:description", "description"),
        (".//dcterms:identifier", "identifier"),
        (".//qm:webId", "webId"),
        (".//qm:creationDate", "creation_date"),
        (".//dcterms:created", "created"),
        (".//dcterms:modified", "modified"),
        (".//alm:updated", "updated"),
        (".//qm:weight", "weight"),
        (".//qm:locked", "locked"),
        (".//qm:suspect", "suspect"),
        (".//qm:testCaseExecutionRecordCount", "execution_record_count"),
        (".//qm:scriptStepCount", "script_step_count"),
    ]:
        elem = root.find(tag, ns)
        if elem is not None and elem.text and elem.text.strip():
            details[key] = elem.text.strip()

    # --- State ---
    state_elem = root.find(".//qm:state", ns) or root.find(".//alm:state", ns)
    if state_elem is not None:
        details["state"] = state_elem.text.strip() if state_elem.text else ""
        res = state_elem.get(f"{{{ns['rdf']}}}resource") or state_elem.get("href", "")
        if res:
            details["state_resource"] = res

    # --- Priority ---
    priority_elem = root.find(".//qm:priority", ns)
    if priority_elem is not None:
        details["priority"] = priority_elem.text.strip() if priority_elem.text else ""
        res = priority_elem.get(f"{{{ns['rdf']}}}resource") or priority_elem.get("href", "")
        if res:
            details["priority_resource"] = res

    # --- Creator ---
    creator_elem = root.find(".//dc:creator", ns) or root.find(".//dcterms:creator", ns)
    if creator_elem is not None:
        details["creator"] = creator_elem.text.strip() if creator_elem.text else ""
        name = creator_elem.get("name", "")
        if name:
            details["creator_name"] = name
        res = creator_elem.get(f"{{{ns['rdf']}}}resource") or creator_elem.get("href", "")
        if res:
            details["creator_resource"] = res

    # --- Owner ---
    owner_elem = root.find(".//alm:owner", ns) or root.find(".//qm:owner", ns)
    if owner_elem is not None:
        details["owner"] = owner_elem.text.strip() if owner_elem.text else ""
        name = owner_elem.get("name", "")
        if name:
            details["owner_name"] = name

    # --- Rich text sections ---
    _RQM_SECTION_MAP = {
        "com.ibm.rqm.planning.editor.section.testCaseDesign": "test_case_design",
        "com.ibm.rqm.planning.editor.section.testCasePreCondition": "precondition",
        "com.ibm.rqm.planning.editor.section.testCasePostCondition": "postcondition",
        "com.ibm.rqm.planning.editor.section.testCaseExpectedResults": "expected_results",
    }
    for elem in root.iter():
        local_tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local_tag in _RQM_SECTION_MAP:
            key = _RQM_SECTION_MAP[local_tag]
            inner = "".join(ET.tostring(child, encoding="unicode", method="html") for child in elem)
            text = inner.strip() if inner.strip() else (elem.text.strip() if elem.text else "")
            if text:
                details[key] = text

    # --- Requirement links ---
    requirement_links: list[dict[str, str]] = []
    for elem in root.findall(".//qm:validates", ns):
        href = elem.get("href", "")
        if href:
            requirement_links.append({"href": href, "type": "validates"})
    for elem in root.findall(f".//{{{OSLC_QM_NAMESPACE}}}validatesRequirement", ns):
        href = elem.get("href", "") or elem.get(f"{{{ns['rdf']}}}resource", "")
        if href:
            requirement_links.append({"href": href, "type": "validatesRequirement"})
    details["requirement_links"] = requirement_links

    # --- Development Items ---
    development_items: list[dict[str, str]] = []
    for tag in [".//qm:relatedchangerequest", ".//qm:relatedworkitem"]:
        for elem in root.findall(tag, ns):
            href = elem.get("href", "")
            if href:
                rel_type = tag.split(":")[-1]
                item: dict[str, str] = {"href": href, "type": rel_type}
                summary = elem.get("summary", "")
                if summary:
                    item["summary"] = summary
                development_items.append(item)
    for elem in root.findall(f".//{{{OSLC_QM_NAMESPACE}}}relatedChangeRequest"):
        href = elem.get("href", "") or elem.get(f"{{{ns['rdf']}}}resource", "")
        if href:
            item = {"href": href, "type": "relatedChangeRequest"}
            summary = elem.get("summary", "")
            if summary:
                item["summary"] = summary
            development_items.append(item)
    details["development_items"] = development_items

    # --- Architecture Element Links ---
    architecture_elements: list[dict[str, str]] = []
    for elem in root.findall(".//qm:architectureelement", ns):
        href = elem.get("href", "")
        if href:
            arch_item: dict[str, str] = {"href": href}
            summary = elem.get("summary", "")
            if summary:
                arch_item["summary"] = summary
            architecture_elements.append(arch_item)
    details["architecture_element_links"] = architecture_elements

    # --- Test Scripts ---
    test_scripts: list[dict[str, str]] = []
    for elem in root.findall(".//qm:testscript", ns):
        href = elem.get("href", "")
        if href:
            script_id = href.split(":")[-1] if ":" in href else href.split("/")[-1]
            test_scripts.append({"href": href, "id": script_id})
    details["test_scripts"] = test_scripts

    # --- Categories ---
    categories: list[dict[str, str]] = []
    for elem in root.findall(".//qm:category", ns):
        cat: dict[str, str] = {}
        term = elem.get("term", "")
        if term:
            cat["term"] = term
        value = elem.get("value", "")
        if value:
            cat["value"] = value
        href = elem.get("href", "")
        if href:
            cat["href"] = href
        if cat:
            categories.append(cat)
    details["categories"] = categories

    # --- Custom Attributes ---
    custom_attributes: list[dict[str, Any]] = []
    for ca in root.findall(".//qm:customAttribute", ns):
        attr_data: dict[str, Any] = {}
        for attr_name in ["type", "required", "href"]:
            val = ca.get(attr_name, "")
            if val:
                attr_data[attr_name] = val
        for child in ca:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child.text and child.text.strip():
                attr_data[child_tag] = child.text.strip()
        if attr_data:
            custom_attributes.append(attr_data)
    if custom_attributes:
        details["custom_attributes"] = custom_attributes

    # --- Attachments ---
    attachments: list[dict[str, str]] = []
    for elem in root.findall(".//qm:attachment", ns):
        href = elem.get("href", "")
        if href:
            att_id = href.split(":")[-1] if ":" in href else href.split("/")[-1]
            attachments.append({"href": href, "id": att_id})
    if attachments:
        details["attachments"] = attachments

    # --- Template ---
    template_elem = root.find(".//qm:template", ns)
    if template_elem is not None:
        href = template_elem.get("href", "")
        if href:
            details["template_href"] = href

    # --- Variables ---
    variables_elem = root.find(".//qm:variables", ns)
    if variables_elem is not None:
        inner = "".join(ET.tostring(child, encoding="unicode", method="html") for child in variables_elem)
        text = inner.strip() if inner.strip() else (variables_elem.text.strip() if variables_elem.text else "")
        if text:
            details["variables"] = text

    return details
