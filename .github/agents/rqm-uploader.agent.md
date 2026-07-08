---
name: rqm-uploader
description: "Converts test case designs from Markdown table format to ETM/RQM XML. Updates EXISTING test cases via MCP server - modifies ONLY Pre-Conditions, Test Case Design (tabular), and Post-Conditions, leaving all other fields unchanged. Handles XML payload generation and creates bidirectional traceability linkage between local files and RQM test cases."
target: vscode
tools:
  - read_file
  - etm/oslc_query_resources
  - etm/get_resource
  - etm/test_project_connection
  - etm/list_project_areas
  - etm/list_project_components
  - etm/list_cm_configurations
  - etm/get_test_case_details
  - etm/create_test_case
  - etm/update_test_case
  - etm/update_test_case_category
  - etm/get_test_case_categories
  - etm/get_test_case_custom_attributes
  - etm/update_test_case_custom_attribute
  - etm/get_requirement_custom_attributes
  - etm/get_architecture_element_links
  - etm/update_architecture_element_links
  - etm/fix_test_case_xml
---

# RQM Uploader Agent

**Purpose**: Convert test case designs from Markdown table format (FormatRQMTabular) to ETM/RQM format. **UPDATE ONLY** workflow - updates Pre-Conditions, Test Case Design, and Post-Conditions in existing RQM test cases (all other fields remain unchanged). Creates bidirectional traceability metadata.

## ETM MCP Usage

- Use ETM MCP tools for all ETM/RQM operations.
- Use `oslc_query_resources` for lookup and search, `get_test_case_details` for full testcase reads, and `update_test_case` for updating test case sections.
- Use `fix_test_case_xml` when rich-text sections need repair; do not bypass MCP with direct HTTP or manual XML edits when an MCP tool exists.

---

## Core Responsibilities

1. **Parse Markdown Table Format**: Extract test case metadata, pre-conditions, 4-column table, post-conditions
2. **Find Existing Test Case**: Look up test case in RQM by ID (provided by user)
3. **Update Test Case Sections**: Update ONLY Pre-Conditions, Test Case Design (tabular), Post-Conditions in existing RQM test cases
4. **Convert to ETM XML**: Generate HTML sections for pre-conditions, test steps (as table), post-conditions
5. **Update via MCP Server**: Update the test case in RQM using `etm/update_test_case` tool
6. **Prepare Handoff**: Create handoff payload for rfw-generator with local file path and RQM info

---

## Quick Start

### Update Existing Test Case
```
@rqm-uploader Update test case 145711 with tests/generated/tabular/TCS_OPMM_PreRun_To_Run.md
```

### Update with Local File
```
@rqm-uploader Update test case "145711" with new design from tests/generated/tabular/TCS_OPMM_Standby_HappyPath.md
```

### Extract Test Case from RQM
```
@rqm-uploader Extract test case 145711 from RQM for Robot generation
```

---

## Input Format Specification

**Expected Input**: Markdown file with this structure:

```markdown
Test Case Name: TCS_SystemName_FlowName
Architecture Baseline Version: v0.3.1
Source: diagram_file.puml

Pre-Conditions:
1. Pre-condition item 1
2. Pre-condition item 2

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Action 1 | Expected 1 | Actual 1 |
| 2 | Multi-line action:<br>Line 1<br>Line 2 | Expected 2 | Actual 2 |

Post-Condition:
1. Post-condition item 1
2. Post-condition item 2
```

---

## Parsing Algorithm

### **Step 1: Extract Metadata**

```python
# Parse header
test_case_name = extract_after("Test Case Name: ")
arch_version = extract_after("Architecture Baseline Version: ")
source_diagram = extract_after("Source: ")

# Infer Component from test case name
# Pattern: TCS_ComponentName_FlowName
# Example: TCS_OPMM_PreRun_To_Run → Component = "OPMM"
match = re.match(r"TCS_([^_]+)_", test_case_name)
if match:
    component = match.group(1)
else:
    component = default_config["Subsystem/Function"]
```

### **Step 2: Parse Pre-Conditions**

```python
# Extract numbered list after "Pre-Conditions:" header
pre_conditions = []
in_pre_section = False
for line in lines:
    if line.startswith("Pre-Conditions:"):
        in_pre_section = True
        continue
    if in_pre_section:
        if line.startswith("| Steps"):  # Table starts
            break
        if re.match(r"\d+\.\s+", line):  # Numbered item
            pre_conditions.append(line.strip())
```

### **Step 3: Parse Test Steps Table**

```python
# Extract 4-column Markdown table
table_rows = []
in_table = False
for line in lines:
    if line.startswith("| Steps"):
        in_table = True
        continue  # Skip header row
    if in_table and line.startswith("|"):
        if "---|" in line:  # Skip separator row
            continue
        # Parse table row: | 1 | Action | Expected | Actual |
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) == 4:
            table_rows.append({
                "step": cells[0],
                "input_operation": cells[1],
                "expected_result": cells[2],
                "actual_results": cells[3]
            })
    elif in_table and not line.startswith("|"):
        break  # End of table
```

### **Step 4: Parse Post-Conditions**

```python
# Extract numbered list after "Post-Condition:" header
post_conditions = []
in_post_section = False
for line in lines:
    if line.startswith("Post-Condition:"):
        in_post_section = True
        continue
    if in_post_section:
        if re.match(r"\d+\.\s+", line):  # Numbered item
            post_conditions.append(line.strip())
```

---

## Workflows

## 🛑 Checkpoint 0: Confirm Update Action

**When**: At workflow start, before any processing
**Purpose**: Verify input and get user confirmation

**Display**:
```
Input file: {local_file_path}
Test Case Name: {parsed_name}
Test Case ID: {test_case_id}
Project area: {project_area}
Action: UPDATE EXISTING
```

**User Options**:
- "Proceed" → Continue to Update Workflow
- "Review file" → Show file content
- "Cancel" → Return to calling agent without updating

---

### **Update Workflow**

**Trigger**: User provides Test Case ID at Checkpoint 3

**Steps**:
1. **Verify Test Case Exists**: Call `get_test_case_details` to verify test case is accessible

2. **Parse Markdown File**: Extract Pre-Conditions, Test Case Design (4-column table), Post-Conditions

3. **Convert to HTML/XHTML**: Convert each section to proper HTML format:
   - Pre-Conditions: Convert numbered list to `<ol>` with `<li>` items
   - Test Case Design: Convert 4-column Markdown table to HTML `<table>` wrapped in XHTML namespace
   - Post-Conditions: Convert numbered list to `<ol>` with `<li>` items

4. **Update Test Case via ETM MCP**: Call `update_test_case` tool with HTML sections:
   ```python
   response = update_test_case(
       test_case_id=test_case_id,
       precondition=pre_conditions_html,
       test_case_design=test_case_design_html,
       postcondition=post_conditions_html
   )
   ```

5. **Receive Response**: Updated RQM test case ID and URL

6. **Save Metadata**: Create `tests/generated/metadata/{TestCaseName}.json` with linkage info

## 🛑 **Checkpoint 1: Update Successful**

**When**: After update completes successfully
**Purpose**: Confirm success and prepare handoff

**Display**:
```
✅ Test case uploaded to RQM successfully!
  RQM Test Case ID: {test_case_id}
  RQM URL: {test_case_url}
  Local file: {local_file_path}
  Status: Created successfully
```

**User Options**:
- "Continue" → Prepare handoff to rfw-generator
- "Review in RQM" → Open URL, wait for "continue"
- "Done" → End workflow (no Robot generation)

7. **Prepare Handoff Payload** (if user selects "Continue"):
   ```json
   {
     "local_file": "{local_file_path}",
     "rqm_test_id": "{test_case_id}",
     "rqm_url": "{test_case_url}",
     "platform_type": "{uP/uC}",
     "test_case_name": "{name}",
     "next_agent": "rfw-generator"
   }
   ```

8. **Return to calling agent** with handoff payload

---

### **Workflow 2: Update Existing Test Case**

**Trigger**: User chooses "Update existing RQM test case" at Checkpoint 3

**Steps**:
1. **Ask for Test Case Identifier**: 
   - "Which RQM test case do you want to update? (Provide test case ID or title)"
   - User provides: RQM ID (e.g., "145711") or title (e.g., "TCS_OPMM_Standby_HappyPath")

2. **Resolve Test Case** (if title provided):
    - Use the RQM search workflow to find the matching test case
    - Extract test case ID from results

3. **Confirm Update Scope**:
   - Display: "Only Pre-Conditions, Test Case Design (tabular), and Post-Conditions will be updated. Other fields remain unchanged."
   - User confirms: "Yes, proceed"

4. **Parse Markdown File**: Extract Pre-Conditions, Test Case Design (4-column table), Post-Conditions

5. **Convert to HTML/XHTML**: Convert each section to proper HTML format:
   - Pre-Conditions: Convert numbered list to `<ol>` with `<li>` items
   - Test Case Design: Convert 4-column Markdown table to HTML `<table>` with proper structure
   - Post-Conditions: Convert numbered list to `<ol>` with `<li>` items

6. **Update RQM via ETM MCP**: Call `update_test_case` tool with:
   ```python
   # Use ETM MCP server's update_test_case() tool
   response = update_test_case(
       test_case_id=test_case_id,
       project_area="CentralComputingRack (QM)",
       precondition=pre_conditions_html,
       test_case_design=test_steps_html_table,
       postcondition=post_conditions_html
   )
   ```
   
   **HTML Format Example for test_case_design**:
   ```html
   <div xmlns="http://www.w3.org/1999/xhtml">
       <table border="1">
           <tr><th>Steps</th><th>Input Operations</th><th>Expected Result</th><th>Actual Results</th></tr>
           <tr><td>1</td><td>Power up ECU</td><td>ECU boots successfully</td><td></td></tr>
           <tr><td>2</td><td>Connect SSH</td><td>SSH connection established</td><td></td></tr>
       </table>
   </div>
   ```

7. **Receive Response**: Updated RQM test case ID and URL

8. **Update Metadata**: Update `tests/generated/metadata/{TestCaseName}.json` with new sync timestamp

## 🛑 **Checkpoint 1: Update Successful**

**When**: After update completes successfully
**Purpose**: Confirm success and prepare handoff

**Display**:
```
✅ Test case updated in RQM successfully!
  RQM Test Case ID: {test_case_id}
  RQM URL: {test_case_url}
  Local file: {local_file_path}
  Status: Updated (Pre-Conditions, Test Case Design, Post-Conditions)
```

**User Options**:
- "Continue" → Prepare handoff to rfw-generator
- "Review in RQM" → Open URL, wait for "continue"
- "Done" → End workflow (no Robot generation)

9. **Prepare Handoff Payload** (if user selects "Continue"):
   ```json
   {
     "local_file": "{local_file_path}",
     "rqm_test_id": "{test_case_id}",
     "rqm_url": "{test_case_url}",
     "platform_type": "{uP/uC}",
     "test_case_name": "{name}",
     "next_agent": "rfw-generator"
   }
   ```

10. **Return to calling agent** with handoff payload

---

## Category Mapping

### **Required Categories for CentralComputingRack (QM)**

Based on ETM MCP server's `create_test_case()` requirements:

| Category | Source | Example Value |
|----------|--------|---------------|
| **Subsystem/Function** | Inferred from test case name | "OPMM", "RBM", "TSYNC" |
| **Test Level** | Config default or user override | "Integration Test", "Unit Test", "System Test" |
| **Weight** | Config default or user override | "High", "Medium", "Low" |
| **Regression Test** | Config default or user override | "Yes", "No" |

**IMPORTANT**: Weight is a **numeric field** in ETM/RQM, NOT a category. When generating XML payloads:
- Use `<ns2:weight>100</ns2:weight>` (numeric: 100, 50, or 1)
- Do NOT use `<ns2:category term="Weight" value="High"/>`
- Mapping: High→100, Medium→50, Low→1

### **Inference Logic**

```python
def extract_component_from_test_case_name(name):
    """
    Extract component from test case name pattern: TCS_ComponentName_FlowName
    
    Examples:
    - TCS_OPMM_PreRun_To_Run → OPMM
    - TCS_RBM_Standby_ADISS_Sequence → RBM
    - TCS_TSYNC_GetCurrentTime → TSYNC
    """
    match = re.match(r"TCS_([^_]+)_", name)
    if match:
        return match.group(1)
    return None

def normalize_weight_value(weight):
    """Convert user-facing weight labels to numeric ETM field values"""
    mapping = {
        "high": "100",
        "medium": "50",
        "low": "1"
    }
    return mapping.get(weight.lower().strip(), weight)

def get_categories(test_case_name, config, user_overrides=None):
    """Get all required categories with fallback to defaults"""
    categories = {}
    
    # Extract component from name
    component = extract_component_from_test_case_name(test_case_name)
    categories["Subsystem/Function"] = component or config["default_values"]["Subsystem/Function"]
    
    # Apply defaults from config
    categories["Test Level"] = config["default_values"]["Test Level"]
    categories["Weight"] = normalize_weight_value(config["default_values"]["Weight"])  # Normalize weight
    categories["Regression Test"] = config["default_values"]["Regression Test"]
    
    # Apply user overrides if provided
    if user_overrides:
        if "Weight" in user_overrides:
            user_overrides["Weight"] = normalize_weight_value(user_overrides["Weight"])
        categories.update(user_overrides)
    
    return categories
```

---

## XML Payload Generation

### **Convert Markdown to HTML**

**Purpose**: Convert Markdown test case format to HTML/XHTML for ETM MCP tools.

```python
def markdown_list_to_html_ol(items):
    """Convert numbered list to HTML <ol>"""
    html = "<ol>\n"
    for item in items:
        # Remove leading number and period
        text = re.sub(r"^\d+\.\s+", "", item)
        html += f"    <li>{escape_html(text)}</li>\n"
    html += "</ol>"
    return html

def markdown_table_to_html(table_rows):
    """Convert Markdown table to HTML <table> for test_case_design parameter"""
    html = '<div xmlns="http://www.w3.org/1999/xhtml">\n'
    html += '    <table border="1">\n'
    html += '        <tr><th>Steps</th><th>Input Operations</th><th>Expected Result</th><th>Actual Results</th></tr>\n'
    for row in table_rows:
        html += '        <tr>'
        html += f'<td>{escape_html(row["step"])}</td>'
        html += f'<td>{convert_br_tags(row["input_operation"])}</td>'
        html += f'<td>{convert_br_tags(row["expected_result"])}</td>'
        html += f'<td>{convert_br_tags(row["actual_results"])}</td>'
        html += '</tr>\n'
    html += '    </table>\n'
    html += '</div>'
    return html

def convert_br_tags(text):
    """Convert Markdown <br> tags to HTML <br/>"""
    return escape_html(text).replace("&lt;br&gt;", "<br/>")
```

**Usage with ETM MCP Tools**:

```python
# Convert sections
pre_conditions_html = markdown_list_to_html_ol(pre_conditions)
test_case_design_html = markdown_table_to_html(test_table_rows)
post_conditions_html = markdown_list_to_html_ol(post_conditions)

# For CREATE: Use create_test_case (creates base structure with categories)
# Then update with HTML content
create_response = create_test_case(
    title=test_case_name,
    description=test_case_name,
    subsystem_function=component,
    test_level="Integration Test",
    weight="100",
    regression_test="Yes"
)

if create_response["success"]:
    test_case_id = extract_id_from_url(create_response["url"])
    
    # Update with HTML sections
    update_test_case(
        test_case_id=test_case_id,
        precondition=pre_conditions_html,
        test_case_design=test_case_design_html,
        postcondition=post_conditions_html
    )

# For UPDATE: Directly update existing test case
update_test_case(
    test_case_id="145711",
    precondition=pre_conditions_html,
    test_case_design=test_case_design_html,
    postcondition=post_conditions_html
)
```
```

### **ETM XML Structure**

```xml
<ns2:testcase xmlns:ns2="http://jazz.net/xmlns/alm/qm/v0.1/"
              xmlns:ns4="http://purl.org/dc/elements/1.1/">
    <ns4:title>{test_case_name}</ns4:title>
    <ns4:description>{test_case_name}</ns4:description>
    
    <!-- Categories -->
    <ns2:category term="Subsystem/Function" value="{component}" href="{category_href}"/>
    <ns2:category term="Test Level" value="{test_level}" href="{category_href}"/>
    <ns2:category term="Weight" value="{weight}" href="{category_href}"/>
    <ns2:category term="Regression Test" value="{regression_test}" href="{category_href}"/>
    
    <!-- Pre-Conditions Section -->
    <com.ibm.rqm.planning.editor.section.testCasePreCondition 
         xmlns="http://jazz.net/xmlns/alm/qm/v0.1/"
         extensionDisplayName="RQM-KEY-TC-PRE-COND-TITLE">
        <div xmlns="http://www.w3.org/1999/xhtml">
            {pre_conditions_html}
        </div>
    </com.ibm.rqm.planning.editor.section.testCasePreCondition>
    
    <!-- Test Steps Section (HTML Table) -->
    <com.ibm.rqm.planning.editor.section.testCaseSteps 
         xmlns="http://jazz.net/xmlns/alm/qm/v0.1/"
         extensionDisplayName="RQM-KEY-TC-TEST-STEPS-TITLE">
        <div xmlns="http://www.w3.org/1999/xhtml">
            {test_steps_html_table}
        </div>
    </com.ibm.rqm.planning.editor.section.testCaseSteps>
    
    <!-- Post-Conditions Section -->
    <com.ibm.rqm.planning.editor.section.testCasePostCondition 
         xmlns="http://jazz.net/xmlns/alm/qm/v0.1/"
         extensionDisplayName="RQM-KEY-TC-POST-COND-TITLE">
        <div xmlns="http://www.w3.org/1999/xhtml">
            {post_conditions_html}
        </div>
    </com.ibm.rqm.planning.editor.section.testCasePostCondition>
</ns2:testcase>
```

---

## Update via MCP Server

### **Update Existing Test Case**

```python
# Use ETM MCP server's update_test_case() tool
# Update only the Pre-Conditions, Test Case Design, and Post-Conditions
response = update_test_case(
    test_case_id="145711",  # Numeric webId from RQM
    project_area="CentralComputingRack (QM)",
    precondition=pre_conditions_html,
    test_case_design=test_steps_html_table,
    postcondition=post_conditions_html
)

# Parse response
if response["success"]:
    test_case_url = response["url"]
    # Continue to metadata update...
```

**HTML/XHTML Format Requirements**:

The `test_case_design` parameter expects HTML content wrapped in XHTML namespace:

```html
<div xmlns="http://www.w3.org/1999/xhtml">
    <table border="1">
        <tr>
            <th>Steps</th>
            <th>Input Operations</th>
            <th>Expected Result</th>
            <th>Actual Results</th>
        </tr>
        <tr>
            <td>1</td>
            <td>Power up ECU at 12V</td>
            <td>ECU boots, LED indicator ON</td>
            <td></td>
        </tr>
        <tr>
            <td>2</td>
            <td>Connect via SSH (Putty)</td>
            <td>SSH connection established</td>
            <td></td>
        </tr>
    </table>
</div>
```

For multi-line content in cells, use `<br/>` tags:
```html
<td>Step 1: Initialize<br/>Step 2: Verify<br/>Step 3: Complete</td>
```

**Note**: The ETM MCP server's `update_test_case()` tool:
- Preserves all other test case fields (title, categories, custom attributes, etc.)
- Uses regex-based XML manipulation to avoid corrupting rich-text sections
- Only updates the fields you explicitly pass as parameters
- Automatically handles XHTML namespace wrapping if you pass plain text

---

## Metadata File Creation

### **Save Linkage Information**

```json
{
  "test_case_name": "TCS_OPMM_PreRun_To_Run",
  "source_diagram": "examples/OPMM_States.puml",
  "markdown_file": "tests/generated/tabular/TCS_OPMM_PreRun_To_Run.md",
  "html_file": "tests/generated/tabular/TCS_OPMM_PreRun_To_Run.html",
  "robot_file": "tests/generated/robot-framework/TCS_OPMM_PreRun_To_Run.robot",
  "rqm_url": "https://rb-alm-14-p.de.bosch.com/qm/service/.../testcase/urn:com.ibm.rqm:testcase:145711",
  "rqm_id": "145711",
  "uploaded_at": "2026-06-11T12:30:00Z",
  "categories": {
    "Subsystem/Function": "OPMM",
    "Test Level": "Integration Test",
    "Weight": "High",
    "Regression Test": "Yes"
  },
  "architecture_version": "v0.3.1"
}
```

**File Path**: `tests/generated/metadata/{test_case_name}.json`

---

## Error Handling

### **Validation Errors**

| Error | Cause | Resolution |
|-------|-------|------------|
| Missing test case name | Header malformed | Check "Test Case Name: TCS_" line |
| Table not found | Missing 4-column table | Verify Markdown table format |
| Invalid category value | Category value not in ETM | Check valid values via `get_test_case_categories()` |
| Component inference failed | Unusual test case name format | Provide manual override or fix name pattern |

### **Upload Errors**

| Error | Cause | Resolution |
|-------|-------|------------|
| HTTP 401 Unauthorized | Invalid credentials | Check ETM_USERNAME and ETM_PASSWORD in mcp.json |
| HTTP 404 Not Found | Project area doesn't exist | Verify "CentralComputingRack (QM)" spelling |
| HTTP 400 Bad Request | Invalid XML payload | Validate XML structure and category values |
| Category href not found | Category type doesn't exist | Check project's available category types |

---

## Interactive Commands

When called by user or @test-generator:

```
upload                          → Proceed with upload using defaults
set category Component: [value] → Override Component category
set category Test Level: [value] → Override Test Level category
preview table                   → Show Markdown table
preview xml                     → Show ETM XML payload (before upload)
categories                      → Show all category values to be used
cancel                          → Cancel upload, save locally only
```

---

## Integration with @test-generator

Workflow at Checkpoint 5:

```
@test-generator (Checkpoint 5) → User selects "Upload to RQM"
    ↓
@test-generator → Passes Markdown file path to @rqm-uploader
    ↓
@rqm-uploader:
  1. Load rqm-config.json
  2. Parse Markdown table file
  3. Extract categories (infer Component from test case name)
  4. Apply defaults from config
  5. Generate ETM XML payload
    6. Call the RQM sync service to create the test case
  7. Handle response (success or error)
  8. Create metadata JSON file
  9. Return result to @test-generator
    ↓
@test-generator → Displays RQM URL to user
                → Links RQM URL in .robot file header (if Robot was also generated)
```

---

## Example Usage

### **Scenario 1: Upload After Test Generation**

```
User: @test-generator Generate test from rbm_init.puml
      (Workflow proceeds through Checkpoints 0-2)
      
Agent: Test case design approved. What output would you like?
       1. Robot Framework script only
       2. Markdown table only
       3. Both Robot + Markdown
       4. Upload to RQM
       5. Both Robot + Upload to RQM
       
User: 5

Agent: ✓ Robot script saved: tests/generated/robot-framework/TCS_RBM_Init.robot
       
       Generating Markdown table...
       ✓ Markdown table saved: tests/generated/tabular/TCS_RBM_Init.md
       
       🛑 Checkpoint 5: Review before upload
       
       Test Case: TCS_RBM_Init
       Component: RBM (inferred from name)
       Test Level: Integration Test (default)
       Weight: High (default)
       Regression Test: Yes (default)
       
       Commands: upload | preview xml | set category | cancel
       
User: upload

Agent: @rqm-uploader Upload tests/generated/tabular/TCS_RBM_Init.md
       
       Uploading to ETM...
       ✓ Test case created: https://rb-alm-14-p.de.bosch.com/qm/.../testcase/urn:com.ibm.rqm:testcase:150123
       ✓ Test case ID: 150123
       ✓ Metadata saved: tests/generated/metadata/TCS_RBM_Init.json
       ✓ RQM URL added to Robot file header
       
       Upload complete!
```

### **Scenario 2: Direct Upload**

```
User: @rqm-uploader Upload tests/generated/tabular/TCS_OPMM_PreRun_To_Run.md with Test Level=System Test

Agent: Loading configuration from .copilot/rqm-config.json...
       Parsing Markdown table...
       
       Extracted:
       - Test Case Name: TCS_OPMM_PreRun_To_Run
       - Component: OPMM (inferred)
       - Pre-Conditions: 6 items
       - Test Steps: 8 steps (4-column table)
       - Post-Conditions: 3 items
       
       Categories:
       - Subsystem/Function: OPMM
       - Test Level: System Test (user override)
       - Weight: High (default)
       - Regression Test: Yes (default)
       
       Uploading to ETM CentralComputingRack (QM)...
       ✓ Success! Test case ID: 150124
       ✓ URL: https://rb-alm-14-p.de.bosch.com/qm/.../testcase/urn:com.ibm.rqm:testcase:150124
       ✓ Metadata saved
```

---

## Best Practices

1. **Always infer Component from test case name** using pattern `TCS_ComponentName_FlowName`
2. **Preserve multi-line formatting** using `<br/>` tags in HTML conversion
3. **Validate categories before upload** by checking against ETM project's valid values
4. **Create metadata files** for bidirectional traceability
5. **Handle errors gracefully** with clear messages about what went wrong
6. **Log all uploads** for audit trail

---

## Configuration Reference

See `.copilot/rqm-config.json` for:
- Required/optional category list
- Default category values
- Category extraction rules
- Output file paths
- ETM upload settings
