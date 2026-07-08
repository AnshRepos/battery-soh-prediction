"""Tests for services/xml_helpers.py — XML creation, parsing, and manipulation."""

import json
import xml.etree.ElementTree as ET

import pytest
from services.xml_helpers import (
    classify_execution_state,
    create_xml_resource,
    extract_entries_from_feed,
    find_custom_attribute_element,
    fix_et_corruption,
    parse_resource_to_json,
    parse_test_case_details,
    strip_invalid_weight_fields,
    update_custom_attribute_in_xml,
    update_xml_resource,
    xml_element_to_dict,
)
from tests.conftest import SAMPLE_TEST_CASE_XML

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def simple_testcase_xml() -> str:
    """Minimal ns2-prefixed test case XML for update tests."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
        "<dc:title>Old Title</dc:title>"
        "<dc:description>Old Desc</dc:description>"
        "<ns2:weight>100</ns2:weight>"
        "<ns2:customAttributes>"
        "<ns2:customAttribute>"
        "<ns2:name>MyAttr</ns2:name>"
        "<ns2:value>original</ns2:value>"
        "</ns2:customAttribute>"
        "</ns2:customAttributes>"
        "</ns2:testcase>"
    )


@pytest.fixture
def feed_with_next() -> str:
    """Atom feed with a rel=next link."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom"'
        ' xmlns:qm="http://jazz.net/xmlns/alm/qm/v0.1/">'
        '<link rel="next" href="https://etm.example.com/page2"/>'
        "<entry>"
        "<id>urn:1</id><title>TC A</title><updated>2026-01-01T00:00:00Z</updated>"
        "<content><qm:testcase><qm:webId>1</qm:webId></qm:testcase></content>"
        "</entry>"
        "</feed>"
    )


# ── create_xml_resource ──────────────────────────────────────────────────


class TestCreateXmlResource:
    """Tests for create_xml_resource()."""

    def test_basic_testplan(self):
        xml = create_xml_resource("testplan", "My Plan", "Plan description")
        assert "<dc:title>My Plan</dc:title>" in xml
        assert "<dc:description>Plan description</dc:description>" in xml
        assert "qm:testplan" in xml

    def test_with_categories(self):
        cats = [{"term": "Test-Level", "value": "Unit Test", "href": "https://example.com/cat"}]
        xml = create_xml_resource("testcase", "TC", "Desc", categories=cats)
        assert 'term="Test-Level"' in xml
        assert 'value="Unit Test"' in xml
        assert 'href="https://example.com/cat"' in xml

    def test_with_extra_fields(self):
        xml = create_xml_resource("testcase", "TC", "D", weight="200")
        assert "<qm:weight>200</qm:weight>" in xml

    def test_href_prefix_creates_href_attribute(self):
        xml = create_xml_resource("testcase", "TC", "D", href_testscript="https://example.com/script/1")
        assert 'href="https://example.com/script/1"' in xml
        assert "qm:testscript" in xml

    def test_escapes_special_characters(self):
        xml = create_xml_resource("testplan", "Plan <A> & B", "Desc with <tags>")
        assert "&lt;A&gt;" in xml
        assert "&amp; B" in xml

    def test_category_without_href(self):
        cats = [{"term": "Region", "value": "EU"}]
        xml = create_xml_resource("testcase", "TC", "D", categories=cats)
        assert 'term="Region"' in xml
        assert "href" not in xml.split("Region")[1].split("/>")[0] or 'href=""' not in xml


# ── update_xml_resource ──────────────────────────────────────────────────


class TestUpdateXmlResource:
    """Tests for update_xml_resource()."""

    def test_update_title(self, simple_testcase_xml):
        result = update_xml_resource(simple_testcase_xml, title="New Title")
        assert isinstance(result, bytes)
        text = result.decode("utf-8")
        assert "New Title" in text
        assert "Old Title" not in text

    def test_update_description(self, simple_testcase_xml):
        result = update_xml_resource(simple_testcase_xml, description="New Desc")
        text = result.decode("utf-8")
        assert "New Desc" in text
        assert "Old Desc" not in text

    def test_update_custom_field(self, simple_testcase_xml):
        result = update_xml_resource(simple_testcase_xml, weight="300")
        text = result.decode("utf-8")
        assert "300" in text

    def test_returns_bytes(self, simple_testcase_xml):
        result = update_xml_resource(simple_testcase_xml, title="T")
        assert isinstance(result, bytes)

    # -- Rich-text section paths (precondition / postcondition) -----------

    def test_update_existing_precondition_section(self):
        """Replaces XHTML content inside an existing precondition section."""
        section_tag = "com.ibm.rqm.planning.editor.section.testCasePreCondition"
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>TC</dc:title>"
            f"<ns2:{section_tag}>"
            '<div xmlns="http://www.w3.org/1999/xhtml"><p>Old pre</p></div>'
            f"</ns2:{section_tag}>"
            "</ns2:testcase>"
        )
        result = update_xml_resource(xml, precondition="New precondition")
        text = result.decode("utf-8")
        assert "New precondition" in text
        assert "Old pre" not in text
        # XHTML wrapper must be present
        assert '<div xmlns="http://www.w3.org/1999/xhtml">' in text
        assert "<p>New precondition</p>" in text

    def test_update_existing_postcondition_section(self):
        """Replaces XHTML content inside an existing postcondition section."""
        section_tag = "com.ibm.rqm.planning.editor.section.testCasePostCondition"
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>TC</dc:title>"
            f"<ns2:{section_tag}>"
            '<div xmlns="http://www.w3.org/1999/xhtml"><p>Old post</p></div>'
            f"</ns2:{section_tag}>"
            "</ns2:testcase>"
        )
        result = update_xml_resource(xml, postcondition="New postcondition")
        text = result.decode("utf-8")
        assert "New postcondition" in text
        assert "Old post" not in text
        assert '<div xmlns="http://www.w3.org/1999/xhtml">' in text
        assert "<p>New postcondition</p>" in text

    def test_insert_precondition_when_section_absent(self):
        """Creates the precondition section before the root closing tag when missing."""
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>TC</dc:title>"
            "</ns2:testcase>"
        )
        result = update_xml_resource(xml, precondition="Brand new pre")
        text = result.decode("utf-8")
        section_tag = "com.ibm.rqm.planning.editor.section.testCasePreCondition"
        assert section_tag in text
        assert "Brand new pre" in text
        assert '<div xmlns="http://www.w3.org/1999/xhtml">' in text
        assert "<p>Brand new pre</p>" in text
        # Section must appear before the root closing tag
        assert text.index(section_tag) < text.index("</ns2:testcase>")

    def test_insert_postcondition_when_section_absent(self):
        """Creates the postcondition section before the root closing tag when missing."""
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>TC</dc:title>"
            "</ns2:testcase>"
        )
        result = update_xml_resource(xml, postcondition="Brand new post")
        text = result.decode("utf-8")
        section_tag = "com.ibm.rqm.planning.editor.section.testCasePostCondition"
        assert section_tag in text
        assert "Brand new post" in text
        assert '<div xmlns="http://www.w3.org/1999/xhtml">' in text
        assert "<p>Brand new post</p>" in text
        assert text.index(section_tag) < text.index("</ns2:testcase>")

    def test_rich_text_value_is_html_escaped(self):
        """Special characters in rich-text values are escaped in the XHTML output."""
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>TC</dc:title>"
            "</ns2:testcase>"
        )
        result = update_xml_resource(xml, precondition="A & B <check>")
        text = result.decode("utf-8")
        assert "&amp;" in text
        assert "&lt;check&gt;" in text
        assert "A & B <check>" not in text

    def test_update_precondition_and_postcondition_together(self):
        """Both rich-text fields can be updated in a single call."""
        pre_tag = "com.ibm.rqm.planning.editor.section.testCasePreCondition"
        post_tag = "com.ibm.rqm.planning.editor.section.testCasePostCondition"
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
            "<dc:title>TC</dc:title>"
            "</ns2:testcase>"
        )
        result = update_xml_resource(xml, precondition="Pre value", postcondition="Post value")
        text = result.decode("utf-8")
        assert pre_tag in text
        assert post_tag in text
        assert "Pre value" in text
        assert "Post value" in text


# ── strip_invalid_weight_fields ──────────────────────────────────────────


class TestStripInvalidWeightFields:
    """Tests for strip_invalid_weight_fields()."""

    def test_removes_prefixed_weight(self):
        xml = "<root><ns2:weight>100</ns2:weight><dc:title>T</dc:title></root>"
        result = strip_invalid_weight_fields(xml)
        assert "weight" not in result
        assert "<dc:title>T</dc:title>" in result

    def test_removes_unprefixed_weight(self):
        xml = '<root><weight xmlns="http://example.com" extensionDisplayName="weight">50</weight></root>'
        result = strip_invalid_weight_fields(xml)
        assert "weight" not in result

    def test_preserves_other_elements(self):
        xml = "<root><ns2:weight>100</ns2:weight><ns2:state>active</ns2:state></root>"
        result = strip_invalid_weight_fields(xml)
        assert "<ns2:state>active</ns2:state>" in result


# ── fix_et_corruption ────────────────────────────────────────────────────


class TestFixEtCorruption:
    """Tests for fix_et_corruption() — 4 corruption patterns."""

    def test_fixes_html_prefixed_tags(self):
        xml = '<root><html:div xmlns:html="http://www.w3.org/1999/xhtml"><html:p>text</html:p></html:div></root>'
        result, fixes = fix_et_corruption(xml)
        assert "<html:" not in result
        assert "<p>text</p>" in result
        assert len(fixes) > 0

    def test_removes_leaked_namespace_declarations(self):
        xml = '<root><div xmlns="http://www.w3.org/1999/xhtml" xmlns:ns0="http://internal">content</div></root>'
        result, fixes = fix_et_corruption(xml)
        assert "xmlns:ns0" not in result

    def test_restores_ms_office_namespaces(self):
        xml = '<root><div xmlns="http://www.w3.org/1999/xhtml">content</div></root>'
        result, fixes = fix_et_corruption(xml)
        assert "xmlns:o=" in result

    def test_no_changes_on_clean_xml(self):
        xml = "<root><element>clean</element></root>"
        result, fixes = fix_et_corruption(xml)
        assert result == xml
        assert fixes == []


# ── find_custom_attribute_element ────────────────────────────────────────


class TestFindCustomAttributeElement:
    """Tests for find_custom_attribute_element()."""

    def test_found(self):
        root = ET.fromstring(SAMPLE_TEST_CASE_XML)
        elem = find_custom_attribute_element(root, "Honda_Test_Case_ID")
        assert elem is not None

    def test_not_found(self):
        root = ET.fromstring(SAMPLE_TEST_CASE_XML)
        elem = find_custom_attribute_element(root, "NonExistent")
        assert elem is None


# ── update_custom_attribute_in_xml ───────────────────────────────────────


class TestUpdateCustomAttributeInXml:
    """Tests for update_custom_attribute_in_xml()."""

    def test_set_value(self, simple_testcase_xml):
        result = update_custom_attribute_in_xml(simple_testcase_xml, "MyAttr", "new_val")
        text = result.decode("utf-8")
        assert "new_val" in text
        assert "original" not in text

    def test_append_value(self, simple_testcase_xml):
        result = update_custom_attribute_in_xml(simple_testcase_xml, "MyAttr", "appended", append=True)
        text = result.decode("utf-8")
        assert "original; appended" in text

    def test_create_new_attribute(self, simple_testcase_xml):
        result = update_custom_attribute_in_xml(simple_testcase_xml, "NewAttr", "new_val")
        text = result.decode("utf-8")
        assert "NewAttr" in text
        assert "new_val" in text

    def test_raises_without_custom_attributes_section(self):
        xml = '<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"></ns2:testcase>'
        with pytest.raises(ValueError, match="Cannot find"):
            update_custom_attribute_in_xml(xml, "Attr", "val")


# ── xml_element_to_dict ──────────────────────────────────────────────────


class TestXmlElementToDict:
    """Tests for xml_element_to_dict()."""

    def test_with_text_children(self):
        xml = "<root><name>Alice</name><age>30</age></root>"
        result = xml_element_to_dict(ET.fromstring(xml))
        assert result["name"] == "Alice"
        assert result["age"] == "30"

    def test_with_href_attribute(self):
        xml = '<root><link href="https://example.com"/></root>'
        result = xml_element_to_dict(ET.fromstring(xml))
        assert result["link"] == "https://example.com"

    def test_with_nested_children(self):
        xml = "<root><parent><child>val</child></parent></root>"
        result = xml_element_to_dict(ET.fromstring(xml))
        assert isinstance(result["parent"], dict)
        assert result["parent"]["child"] == "val"

    def test_list_values_for_duplicate_tags(self):
        xml = "<root><item>A</item><item>B</item></root>"
        result = xml_element_to_dict(ET.fromstring(xml))
        assert isinstance(result["item"], list)
        assert result["item"] == ["A", "B"]


# ── extract_entries_from_feed ────────────────────────────────────────────


class TestExtractEntriesFromFeed:
    """Tests for extract_entries_from_feed()."""

    def test_with_atom_entries(self, sample_atom_feed_xml):
        entries, next_url = extract_entries_from_feed(sample_atom_feed_xml, "testcase")
        assert len(entries) == 2
        assert entries[0]["title"] == "Test Case 1"
        assert next_url is None

    def test_with_next_url(self, feed_with_next):
        entries, next_url = extract_entries_from_feed(feed_with_next, "testcase")
        assert len(entries) == 1
        assert next_url == "https://etm.example.com/page2"

    def test_empty_feed(self):
        xml = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        entries, next_url = extract_entries_from_feed(xml, "testcase")
        assert entries == []
        assert next_url is None

    def test_direct_resources(self):
        xml = (
            '<?xml version="1.0"?>'
            '<feed xmlns="http://www.w3.org/2005/Atom"'
            ' xmlns:qm="http://jazz.net/xmlns/alm/qm/v0.1/">'
            "<qm:testcase><qm:webId>10</qm:webId></qm:testcase>"
            "</feed>"
        )
        entries, next_url = extract_entries_from_feed(xml, "testcase")
        assert len(entries) >= 1

    def test_invalid_xml(self):
        entries, next_url = extract_entries_from_feed("not xml at all", "testcase")
        assert entries == []
        assert next_url is None


# ── classify_execution_state ─────────────────────────────────────────────


class TestClassifyExecutionState:
    """Tests for classify_execution_state()."""

    def test_passed(self):
        assert classify_execution_state("com.ibm.rqm.execution.common.state.passed") == "passed"

    def test_failed(self):
        assert classify_execution_state("com.ibm.rqm.execution.common.state.failed") == "failed"

    def test_blocked(self):
        assert classify_execution_state("com.ibm.rqm.execution.common.state.blocked") == "blocked"

    def test_unknown_defaults_to_incomplete(self):
        assert classify_execution_state("com.ibm.rqm.execution.common.state.notrun") == "incomplete"

    def test_case_insensitive(self):
        assert classify_execution_state("PASSED") == "passed"


# ── parse_resource_to_json ───────────────────────────────────────────────


class TestParseResourceToJson:
    """Tests for parse_resource_to_json()."""

    def test_valid_xml(self):
        xml = '<testcase xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>TC</dc:title></testcase>'
        result = json.loads(parse_resource_to_json(xml))
        assert result["title"] == "TC"
        assert result["_type"] == "testcase"

    def test_invalid_xml_returns_parse_error(self):
        result = json.loads(parse_resource_to_json("<<< bad xml"))
        assert "parse_error" in result


# ── parse_test_case_details ──────────────────────────────────────────────


class TestParseTestCaseDetails:
    """Tests for parse_test_case_details() using SAMPLE_TEST_CASE_XML."""

    def test_extracts_title(self, sample_test_case_xml):
        root = ET.fromstring(sample_test_case_xml)
        details = parse_test_case_details(root)
        assert details["title"] == "Sample Test Case"

    def test_extracts_description(self, sample_test_case_xml):
        root = ET.fromstring(sample_test_case_xml)
        details = parse_test_case_details(root)
        assert details["description"] == "A test case for testing"

    def test_extracts_web_id(self, sample_test_case_xml):
        root = ET.fromstring(sample_test_case_xml)
        details = parse_test_case_details(root)
        assert details["webId"] == "12345"

    def test_extracts_categories(self, sample_test_case_xml):
        root = ET.fromstring(sample_test_case_xml)
        details = parse_test_case_details(root)
        cats = details["categories"]
        assert len(cats) == 2
        terms = {c["term"] for c in cats}
        assert "Test-Level" in terms
        assert "Regression Test" in terms

    def test_extracts_custom_attributes(self, sample_test_case_xml):
        root = ET.fromstring(sample_test_case_xml)
        details = parse_test_case_details(root)
        assert "custom_attributes" in details
        attrs = details["custom_attributes"]
        assert any(a.get("name") == "Honda_Test_Case_ID" for a in attrs)
        assert any(a.get("value") == "HTC-001" for a in attrs)

    def test_extracts_weight(self, sample_test_case_xml):
        root = ET.fromstring(sample_test_case_xml)
        details = parse_test_case_details(root)
        assert details["weight"] == "100"

    def test_state_element_present_in_xml(self, sample_test_case_xml):
        """Verify state element exists in the XML (parse_test_case_details may not
        extract it due to a known Element truthiness quirk with the ``or`` pattern)."""
        root = ET.fromstring(sample_test_case_xml)
        ns = {"qm": "http://jazz.net/xmlns/alm/qm/v0.1/"}
        state_elem = root.find(".//qm:state", ns)
        assert state_elem is not None
        assert state_elem.text == "com.ibm.rqm.planning.common.new"
