# Robot Framework Generator - Pattern Recognition Skills

**Purpose**: Intelligence rules for mapping test case operations to Robot Framework keywords. Used by rfw-generator agent during Step 3 (Pattern Recognition).

---

## Skill 1: Test Case Parsing

### Parse Markdown File (4-Column Table Format)

**Input Format**:
```markdown
Test Case Name: TCS_ComponentName_FlowName
Architecture Baseline Version: vX.Y.Z
Source: diagram.puml
Platform Type: uP / uC (optional)

Pre-Conditions:
1. Pre-condition item 1
2. Pre-condition item 2

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Action 1 | Expected 1 | Actual 1 |
| 2 | Action 2 | Expected 2 | Actual 2 |

Post-Condition:
1. Post-condition item 1
2. Post-condition item 2
```

**Extraction Algorithm**:

```python
def parse_test_case_markdown(file_path):
    content = read_file(file_path)
    
    # Extract metadata
    test_case_name = extract_after("Test Case Name: ")
    arch_version = extract_after("Architecture Baseline Version: ")
    source_diagram = extract_after("Source: ")
    platform_type = extract_after("Platform Type: ")  # May be None
    
    # Extract pre-conditions (numbered list)
    pre_conditions = []
    in_pre_section = False
    for line in lines:
        if line.startswith("Pre-Conditions:") or line.startswith("Pre-Condition:"):
            in_pre_section = True
            continue
        if in_pre_section:
            if line.startswith("| Steps"):  # Table starts
                break
            if re.match(r"\d+\.\s+", line):  # Numbered item
                pre_conditions.append(line.strip())
    
    # Extract test steps (4-column table)
    test_steps = []
    in_table = False
    for line in lines:
        if line.startswith("| Steps"):
            in_table = True
            continue  # Skip header
        if in_table and line.startswith("|"):
            if "---|" in line:  # Skip separator
                continue
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(cells) == 4:
                test_steps.append({
                    "step_num": cells[0],
                    "input_operation": cells[1],
                    "expected_result": cells[2],
                    "actual_results": cells[3]
                })
        elif in_table and not line.startswith("|"):
            break  # End of table
    
    # Extract post-conditions (numbered list)
    post_conditions = []
    in_post_section = False
    for line in lines:
        if line.startswith("Post-Condition:"):
            in_post_section = True
            continue
        if in_post_section:
            if re.match(r"\d+\.\s+", line):
                post_conditions.append(line.strip())
    
    return {
        "name": test_case_name,
        "arch_version": arch_version,
        "source": source_diagram,
        "platform_type": platform_type,
        "pre_conditions": pre_conditions,
        "test_steps": test_steps,
        "post_conditions": post_conditions
    }
```

---

## Skill 2: Platform Type Detection

### Detect uP (Microprocessor) vs uC (Microcontroller)

**uP (Microprocessor) Indicators**:

```python
def is_microprocessor(pre_conditions, test_steps):
    """
    Returns True if test is for uP (Microprocessor/QNX)
    """
    all_text = " ".join(pre_conditions + [step["input_operation"] for step in test_steps])
    all_text_lower = all_text.lower()
    
    # Strong indicators
    if any(keyword in all_text_lower for keyword in [
        "ssh", "putty", "qnx", "serial connection",
        "cd /usr", "./stub", "ps -e"
    ]):
        return True
    
    # Power cycle with boot sequence
    if "power cycle" in all_text_lower and "boot" in all_text_lower:
        return True
    
    # Check pre-conditions specifically
    for condition in pre_conditions:
        condition_lower = condition.lower()
        if "putty" in condition_lower or "ssh" in condition_lower:
            return True
    
    return False
```

**uC (Microcontroller) Indicators**:

```python
def is_microcontroller(pre_conditions, test_steps):
    """
    Returns True if test is for uC (Microcontroller/bare-metal)
    """
    all_text = " ".join(pre_conditions + [step["input_operation"] for step in test_steps])
    all_text_lower = all_text.lower()
    
    # Strong indicators
    if any(keyword in all_text_lower for keyword in [
        "trace32", "jtag", "bare-metal", "rtos"
    ]):
        # Check if SSH is NOT mentioned (pure uC)
        if "ssh" not in all_text_lower and "putty" not in all_text_lower:
            return True
    
    # Flash only, no SSH
    if "flash" in all_text_lower and "ssh" not in all_text_lower:
        return True
    
    return False
```

**Decision Logic**:

```python
def detect_platform_type(pre_conditions, test_steps, platform_hint=None):
    """
    Detect platform type with priority:
    1. Use hint if provided
    2. Check indicators
    3. Ask user if ambiguous
    """
    if platform_hint:
        return platform_hint
    
    is_up = is_microprocessor(pre_conditions, test_steps)
    is_uc = is_microcontroller(pre_conditions, test_steps)
    
    if is_up and not is_uc:
        return "uP"
    elif is_uc and not is_up:
        return "uC"
    elif is_up and is_uc:
        # Ambiguous - ask user
        return prompt_user("Is this for uP (Microprocessor) or uC (Microcontroller)?")
    else:
        # Default to uP if unclear
        return "uP"
```

---

## Skill 3: Operation → Keyword Mapping (40+ Patterns)

### Pattern Recognition Rules

**Category 1: Power Operations**

```python
POWER_PATTERNS = [
    {
        "pattern": r"power\s+cycle|poweroff\s*->\s*poweron",
        "keyword": "Power Cycle ECU And Wait For Boot",
        "resource": "pps_keywords.resource"
    },
    {
        "pattern": r"power-up\s+the\s+ecu|voltage\s*=\s*12v",
        "keyword": "Power On ECU",
        "resource": "pps_keywords.resource"
    },
    {
        "pattern": r"power\s+down|power\s+off",
        "keyword": "Power Off ECU",
        "resource": "pps_keywords.resource"
    }
]
```

**Category 2: SSH Operations**

```python
SSH_PATTERNS = [
    {
        "pattern": r"ssh\s+connection|connect.*ssh|make.*ssh|putty.*available",
        "keyword": "Connect To ECU Over SSH",
        "resource": "ssh_keywords.resource"
    },
    {
        "pattern": r"close\s+ssh|disconnect\s+ssh|putty.*closed",
        "keyword": "Disconnect SSH",
        "resource": "ssh_keywords.resource"
    }
]
```

**Category 3: CANoe/CAN Operations**

```python
CANOE_PATTERNS = [
    {
        "pattern": r"canoe.*initialization|can\s+initialization",
        "keyword": "Can Initialization",
        "resource": "canoe_keywords.resource"
    },
    {
        "pattern": r"can\s+disconnect",
        "keyword": "Can Disconnect",
        "resource": "canoe_keywords.resource"
    },
    {
        "pattern": r"verify\s+can\s+communication|can.*alive",
        "keyword": "Verify CAN Communication Is Alive",
        "resource": "canoe_keywords.resource"
    },
    {
        "pattern": r"opmm.*request|power\s+blade\s+mode",
        "keyword": "Send OPMM Power Blade Mode Request",
        "resource": "canoe_keywords.resource"
    },
    {
        "pattern": r"inter_blade.*sim|set.*inter.*blade",
        "keyword": "Set Inter Blade To SIM",
        "resource": "canoe_keywords.resource"
    }
]
```

**Category 4: DLT Operations**

```python
DLT_PATTERNS = [
    {
        "pattern": r"dlt.*configuration|initialize\s+dlt|start.*dlt",
        "keyword": "Initialize DLT Configuration",
        "resource": "dlt_keywords.resource"
    },
    {
        "pattern": r"launch\s+dlt\s+connector",
        "keyword": "Launch Dlt Connector",
        "resource": "dlt_keywords.resource"
    },
    {
        "pattern": r"stop\s+dlt\s+logging",
        "keyword": "Stop DLT Logging",
        "resource": "dlt_keywords.resource"
    }
]
```

**Category 5: TRACE32 Operations**

```python
TRACE32_PATTERNS = [
    {
        "pattern": r"trace32\s+debugger|start.*trace32",
        "keyword": "Start Trace32 Debugger",
        "resource": "t32_keywords.resource"
    },
    {
        "pattern": r"load\s+debug\s+file|load.*elf",
        "keyword": "Load Debug File",
        "resource": "t32_keywords.resource"
    },
    {
        "pattern": r"set\s+breakpoint",
        "keyword": "Set Breakpoints For FUNCTIONS",
        "resource": "t32_keywords.resource"
    },
    {
        "pattern": r"attach.*target|trace32.*attach",
        "keyword": "Attach Trace32 To Target",
        "resource": "t32_keywords.resource"
    },
    {
        "pattern": r"get.*program\s+counter|pc\s+value",
        "keyword": "Get Current Program Counter",
        "resource": "t32_keywords.resource"
    }
]
```

**Category 6: Flash Operations**

```python
FLASH_PATTERNS = [
    {
        "pattern": r"flash\s+.*sw|flash.*release|flashing\s+script",
        "keyword": "Flash ECU Software",
        "resource": "flashing_keywords.resource"
    },
    {
        "pattern": r"ecu\s+sync|sync.*ecu.*software",
        "keyword": "Sync ECU Software",
        "resource": "flashing_keywords.resource"
    }
]
```

**Category 7: LUM Operations**

```python
LUM_PATTERNS = [
    {
        "pattern": r"upload\s+lum\s+package",
        "keyword": "Upload LUM Package To ECU",
        "resource": "lum_keywords.resource"
    },
    {
        "pattern": r"run\s+lum\s+stub|lum.*stub.*app",
        "keyword": "Run LUM Stub App",
        "resource": "lum_keywords.resource"
    },
    {
        "pattern": r"move.*flash\s+script|lum_flash_main",
        "keyword": "Move LUM Flash Script",
        "resource": "lum_keywords.resource"
    },
    {
        "pattern": r"dump.*api\s+logs|check.*api\s+logs",
        "keyword": "Dump And Check API Logs",
        "resource": "lum_keywords.resource"
    }
]
```

**Category 8: Component-Specific Operations (Custom Keywords)**

These operations don't have dedicated resource files and must be generated as custom keywords in *** Keywords *** section:

```python
COMPONENT_CUSTOM_PATTERNS = [
    {
        "pattern": r"rbm_getversion\(\)",
        "keyword": "Validate RBM Version",
        "custom_keyword": True,
        "base": "Execute Command Return Message"
    },
    {
        "pattern": r"rbm_getstate\(\)",
        "keyword": "Verify {Component} {State} State",
        "custom_keyword": True,
        "requires_component": True
    },
    {
        "pattern": r"rbm_enterstandby|enter.*standby",
        "keyword": "Enter {Component} Standby",
        "custom_keyword": True,
        "requires_component": True
    },
    {
        "pattern": r"rbm_startbuffering|enter.*buffering",
        "keyword": "Enter {Component} Buffering",
        "custom_keyword": True,
        "requires_component": True
    },
    {
        "pattern": r"rbm_regcallback\(\)",
        "keyword": "Register RBM Callback",
        "custom_keyword": True
    },
    {
        "pattern": r"rbm_reqcbk",
        "keyword": "Request RBM Callback",
        "custom_keyword": True
    },
    {
        "pattern": r"rbm_trigsingleevtrec",
        "keyword": "Trigger {Component} Single Event Record And Verify Folder",
        "custom_keyword": True,
        "requires_component": True,
        "returns_variable": "${euuid}"
    },
    {
        "pattern": r"rbm_addmetadata",
        "keyword": "Add {Component} Metadata",
        "custom_keyword": True,
        "requires_component": True,
        "takes_argument": "${euuid}"
    },
    {
        "pattern": r"rbm_deleteentry",
        "keyword": "Delete {Component} Entry",
        "custom_keyword": True,
        "requires_component": True,
        "takes_argument": "${euuid}"
    },
    {
        "pattern": r"rbm_reinit",
        "keyword": "Reinitialize {Component}",
        "custom_keyword": True,
        "requires_component": True
    },
    {
        "pattern": r"rbm_createbufswcontenttest",
        "keyword": "Create {Component} Buffer Content Test",
        "custom_keyword": True,
        "requires_component": True
    },
    {
        "pattern": r"kill\s+(\w+)\s+process",
        "keyword": "Kill {Component} Process",
        "custom_keyword": True,
        "extract_component": True
    },
    {
        "pattern": r"stub_(\w+)|launch.*stub|execute.*stub",
        "keyword": "Launch {Component} Stub",
        "custom_keyword": True,
        "extract_component": True
    },
    {
        "pattern": r"sync\s+ecu\s+time",
        "keyword": "Sync ECU Time",
        "custom_keyword": True
    }
]
```

**Note**: When `custom_keyword: True`, generate the keyword in *** Keywords *** section with TODO comment and reference to Example Robot Files.

```python
def extract_component_from_test_name(test_name):
    """
    Extract component name from test case name.
    Pattern: TCS_ComponentName_FlowName
    Example: TCS_OPMM_PreRun_To_Run → OPMM
             TCS_RingBufferManagement_RBMStandby_ADISS → ADISS
    """
    parts = test_name.split("_")
    if len(parts) >= 2:
        # Try to find component name
        if parts[1] in ["OPMM", "RBM", "ADISS", "SDSRDC", "SDSOM", "RDC", "OM"]:
            return parts[1]
        # Check last part for component
        if parts[-1] in ["ADISS", "SDSRDC", "SDSOM", "RDC", "OM"]:
            return parts[-1]
    return None

def extract_component_from_operation(operation):
    """
    Extract component from operation text.
    Example: "stub_adiss" → "ADISS"
             "Kill ADISS Process" → "ADISS"
    """
    operation_upper = operation.upper()
    
    components = ["ADISS", "SDSRDC", "SDSOM", "RDC", "OM", "OPMM"]
    for comp in components:
        if comp in operation_upper:
            return comp
    
    # Check for stub_xxx pattern
    match = re.search(r"stub_(\w+)", operation, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    
    return None
```

### Pattern Matching Algorithm

```python
def match_operation_to_keyword(operation, component=None):
    """
    Match operation text to Robot keyword using pattern library.
    Returns: {
        "keyword": "Keyword Name",
        "resource": "resource_file.resource" (optional),
        "custom_keyword": bool,
        "variable": "${var}" (optional),
        "argument": "${arg}" (optional)
    }
    """
    operation_lower = operation.lower()
    
    # Combine all pattern libraries
    all_patterns = (
        POWER_PATTERNS +
        SSH_PATTERNS +
        CANOE_PATTERNS +
        DLT_PATTERNS +
        TRACE32_PATTERNS +
        FLASH_PATTERNS +
        LUM_PATTERNS +
        COMPONENT_CUSTOM_PATTERNS  # Custom keywords
    )
    
    for pattern_def in all_patterns:
        if re.search(pattern_def["pattern"], operation_lower):
            keyword = pattern_def["keyword"]
            
            # Replace {Component} placeholder
            if "{Component}" in keyword:
                if component:
                    keyword = keyword.replace("{Component}", component)
                else:
                    # Try to extract from operation
                    extracted_comp = extract_component_from_operation(operation)
                    if extracted_comp:
                        keyword = keyword.replace("{Component}", extracted_comp)
            
            result = {
                "keyword": keyword,
                "custom_keyword": pattern_def.get("custom_keyword", False)
            }
            
            # Add resource only if not custom keyword
            if not result["custom_keyword"]:
                result["resource"] = pattern_def.get("resource")
            
            # Add variable assignment if pattern returns value
            if pattern_def.get("returns_variable"):
                result["variable"] = pattern_def["returns_variable"]
            
            # Add argument if pattern takes input
            if pattern_def.get("takes_argument"):
                result["argument"] = pattern_def["takes_argument"]
            
            return result
    
    # No match found
    return {
        "keyword": f"# TODO: Implement keyword for: {operation}",
        "resource": None,
        "custom_needed": True
    }
```

---

## Skill 4: Resource Import Intelligence

### Determine Required Resources

```python
def determine_required_resources(test_steps, platform_type):
    """
    Analyze test steps and determine which resource files to import.
    """
    resources = set()
    
    all_operations = " ".join([step["input_operation"] for step in test_steps])
    all_operations_lower = all_operations.lower()
    
    # SSH operations (uP only)
    if platform_type == "uP" and any(kw in all_operations_lower for kw in ["ssh", "putty", "cd /usr", "stub", "execute"]):
        resources.add("../resources/ssh_keywords.resource")
    
    # Power operations
    if any(kw in all_operations_lower for kw in ["power", "voltage", "12v", "kl30"]):
        resources.add("../resources/pps_keywords.resource")
    
    # CANoe operations
    if any(kw in all_operations_lower for kw in ["canoe", "can ", "opmm", "inter_blade"]):
        resources.add("../resources/canoe_keywords.resource")
    
    # TRACE32 operations
    if any(kw in all_operations_lower for kw in ["trace32", "debugger", "jtag", "breakpoint", "elf"]):
        resources.add("../resources/t32_keywords.resource")
    
    # DLT operations
    if any(kw in all_operations_lower for kw in ["dlt", "diagnostic log"]):
        resources.add("../resources/dlt_keywords.resource")
    
    # Flash operations
    if "flash" in all_operations_lower and ("sw" in all_operations_lower or "release" in all_operations_lower):
        resources.add("../resources/flashing_keywords.resource")
    
    # LUM operations
    if any(kw in all_operations_lower for kw in ["lum", "lum_flash", "upload package"]):
        resources.add("../resources/lum_keywords.resource")
    
    return sorted(list(resources))
```

**Note**: Component-specific operations (like RBM APIs, stub commands) don't have dedicated resource files. These will be generated as custom keywords in the *** Keywords *** section, using SSH Execute Command as the base implementation.

---

## Skill 5: Setup/Teardown Generation

### Pre-Condition → Setup Mapping

```python
def generate_setup_teardown(pre_conditions, post_conditions, platform_type):
    """
    Generate Suite/Test Setup and Teardown from pre/post conditions.
    """
    pre_text = " ".join(pre_conditions).lower()
    post_text = " ".join(post_conditions).lower()
    
    setup = {
        "suite_setup": None,
        "suite_teardown": None,
        "test_setup": [],
        "test_teardown": []
    }
    
    # Detect specialized setups
    has_canoe = "canoe" in pre_text
    has_dlt = "dlt" in pre_text
    has_trace32 = "trace32" in pre_text
    has_ssh = platform_type == "uP" and ("ssh" in pre_text or "putty" in pre_text)
    has_power = "power" in pre_text or "voltage" in pre_text
    
    # Specialized Suite Setup patterns
    if has_canoe and has_ssh:
        setup["suite_setup"] = "Initialize CANoe and SSH"
        setup["suite_teardown"] = "Disconnect CANoe and SSH"
    elif has_dlt:
        setup["suite_setup"] = "Initialize DLT Configuration"
        setup["suite_teardown"] = "Cleanup Test Environment"
    elif has_trace32:
        setup["suite_setup"] = "Initialize Trace32 Test Environment"
        setup["suite_teardown"] = "Cleanup Trace32 Test Environment"
    elif has_power:
        # Standard PPS setup
        setup["suite_setup"] = "Connect To PPS"
        setup["suite_teardown"] = "Disconnect PPS"
    
    # Test Setup (Multi-step)
    test_setup_steps = []
    
    # Power cycle or power on
    if "power cycle" in pre_text:
        test_setup_steps.append("Power Cycle ECU And Wait For Boot")
    elif "power on" in pre_text or "power-up" in pre_text:
        test_setup_steps.append("Power On ECU")
    
    # SSH connection (if not in specialized suite setup)
    if has_ssh and not has_canoe and not has_trace32:
        test_setup_steps.append("Connect To ECU Over SSH")
        setup["test_teardown"].append("Disconnect SSH")
    
    # Test Teardown
    if has_ssh and (has_canoe or has_trace32):
        setup["test_teardown"].append("Disconnect SSH")
    
    if "power down" in post_text or "power off" in post_text:
        if not has_dlt:  # DLT handles power in suite teardown
            setup["test_teardown"].append("Power Off ECU")
    
    # Combine test setup steps
    if len(test_setup_steps) == 1:
        setup["test_setup"] = test_setup_steps[0]
    elif len(test_setup_steps) > 1:
        setup["test_setup"] = f"Run Keywords    {test_setup_steps[0]}"
        for step in test_setup_steps[1:]:
            setup["test_setup"] += f"\n...              AND    {step}"
    
    return setup
```

**Generated Output Examples**:

**Example 1: Standard uP with SSH**
```robot
Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot
...              AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH
```

**Example 2: CANoe + SSH**
```robot
Suite Setup       Initialize CANoe and SSH
Suite Teardown    Disconnect CANoe and SSH
Test Setup        Power Cycle
Test Teardown     Disconnect SSH
```

**Example 3: DLT**
```robot
Suite Setup       Initialize DLT Configuration
Suite Teardown    Cleanup Test Environment
Test Setup        Power On ECU
Test Teardown     Power Off ECU
```

**Example 4: TRACE32**
```robot
Suite Setup       Initialize Trace32 Test Environment
Suite Teardown    Cleanup Trace32 Test Environment
Test Setup        Power Cycle
Test Teardown     Power Off ECU
```

**Example 5: uC without SSH**
```robot
Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Power On ECU
Test Teardown     Power Off ECU
```

---

## Skill 6: Test Case Body Generation

### Transform Steps to Keywords

```python
def generate_test_case_body(test_steps, component):
    """
    Transform test steps into Robot Framework keyword calls.
    """
    keywords = []
    variables = {}  # Track variables created (e.g., ${euuid})
    
    for step in test_steps:
        operation = step["input_operation"]
        
        # Match to keyword
        match_result = match_operation_to_keyword(operation, component)
        
        if match_result.get("custom_needed"):
            # Unknown operation - add as comment
            keywords.append({
                "type": "comment",
                "content": match_result["keyword"]
            })
        elif match_result.get("variable"):
            # Operation returns a variable
            keywords.append({
                "type": "assignment",
                "variable": match_result["variable"],
                "keyword": match_result["keyword"]
            })
            # Store for later use
            variables[match_result["variable"]] = True
        elif match_result.get("argument"):
            # Operation takes an argument
            arg_name = match_result["argument"]
            if arg_name in variables:
                # Use previously captured variable
                keywords.append({
                    "type": "call",
                    "keyword": match_result["keyword"],
                    "argument": arg_name
                })
            else:
                # Argument not available - add comment
                keywords.append({
                    "type": "comment",
                    "content": f"# TODO: Provide argument for: {match_result['keyword']}"
                })
        else:
            # Simple keyword call
            keywords.append({
                "type": "call",
                "keyword": match_result["keyword"]
            })
    
    return keywords

def format_keywords_as_robot(keywords, indent=4):
    """
    Format keyword list as Robot Framework syntax.
    """
    lines = []
    indent_str = " " * indent
    
    for kw in keywords:
        if kw["type"] == "comment":
            lines.append(f"{indent_str}{kw['content']}")
        elif kw["type"] == "assignment":
            lines.append(f"{indent_str}{kw['variable']}=    {kw['keyword']}")
        elif kw["type"] == "call":
            if "argument" in kw:
                lines.append(f"{indent_str}{kw['keyword']}    {kw['argument']}")
            else:
                lines.append(f"{indent_str}{kw['keyword']}")
    
    return "\n".join(lines)
```

---

## Skill 7: Custom Keyword Creation

### When to Create Custom Keywords

**Criteria for custom keyword**:
1. Component-specific operations (RBM APIs, stub execution, etc.)
2. Multi-step operation in single test step
3. Repeated operation pattern across steps
4. Complex logic with conditionals
5. Operation not matching any available resource pattern

**Custom Keyword Structure**:

Based on patterns from `robot/Example Robot Files/*.robot`:

```robot
*** Keywords ***
Launch ADISS Stub
    [Documentation]    Execute ADISS stub application via SSH
    Execute Command Return Message    cd /usr/sbin && ./stub_adiss    30

Sync ECU Time
    [Documentation]    Synchronize ECU time via SSH
    # TODO: Implement time sync logic based on requirements
    Execute Command Return Message    # Time sync command    30

Kill ADISS Process
    [Documentation]    Kill ADISS process on ECU
    Execute Command Return Message    killall -9 adiss    30

Validate RBM Version
    [Documentation]    Verify RBM_GetVersion() API
    # TODO: Implement RBM_GetVersion() call
    # Reference: Example Robot Files for similar patterns
    Execute Command Return Message    # RBM version check command    30

Enter ADISS Standby
    [Documentation]    Enter RBM Standby state for ADISS
    # TODO: Implement RBM_EnterStandby for ADISS
    Execute Command Return Message    # RBM_EnterStandby command    30

Verify ADISS Standby State
    [Documentation]    Verify ADISS is in Standby state
    # TODO: Implement state verification
    Execute Command Return Message    # RBM_GetState command    30

${euuid}=    Trigger ADISS Single Event Record And Verify Folder
    [Documentation]    Trigger single event record and return EUUID
    # TODO: Implement RBM_trigSingleEvtRec with parameters
    # Returns: EUUID folder name
    Execute Command Return Message    # RBM_trigSingleEvtRec command    30
    # Parse and return EUUID

Add ADISS Metadata    [Arguments]    ${euuid}
    [Documentation]    Add metadata to ADISS event record
    # TODO: Implement RBM_AddMetaData with EUUID
    Execute Command Return Message    # RBM_AddMetaData ${euuid} command    30

Delete ADISS Entry    [Arguments]    ${euuid}
    [Documentation]    Delete ADISS event record entry
    # TODO: Implement RBM_DeleteEntry with EUUID
    Execute Command Return Message    # RBM_DeleteEntry ${euuid} command    30
```

**Example: Complex Multi-Step Keyword** (from 544530 example):

**Input**:
```
Multiple operations requiring coordination
```

**Generated Custom Keyword**:
```robot
*** Keywords ***
ADISS_RBM_Buffering_Preparation
    [Documentation]    Prepare ADISS RBM for buffering state
    Sync ECU Time
    Kill ADISS Process
    Launch ADISS Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Init State
    Create ADISS Buffer Content Test
    Enter ADISS Standby
    Verify ADISS Standby State
    Enter ADISS Buffering
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback

ADISS_RBM_Buffering_Event_Recording
    [Documentation]    Record and verify ADISS RBM buffering events
    ${euuid}=    Trigger ADISS Single Event Record And Verify Folder
    Add ADISS Metadata    ${euuid}
    Delete ADISS Entry    ${euuid}
    ${trigger_handle}=    Trigger ADISS Continuous Event Record
    Stop ADISS Event Record And Verify    ${trigger_handle}

ADISS_RBM_Buffering_Finalization
    [Documentation]    Finalize ADISS RBM buffering test
    Enter ADISS Standby
    Get Number Of Ongoing Triggers
```

**Key Patterns**:
1. Use `Execute Command Return Message` from SshLibrary as base
2. Add [Arguments] for keywords that take parameters
3. Use ${variable}= for keywords that return values
4. Add TODO comments for implementation details
5. Reference Example Robot Files in comments
6. Use descriptive [Documentation] strings

---

## Skill 8: Validation Rules

### Syntax Validation

```python
def validate_robot_syntax(script_content):
    """
    Validate Robot Framework syntax before saving.
    """
    errors = []
    
    # Check required sections
    if "*** Settings ***" not in script_content:
        errors.append("Missing *** Settings *** section")
    
    if "*** Test Cases ***" not in script_content:
        errors.append("Missing *** Test Cases *** section")
    
    # Check indentation (4 spaces)
    lines = script_content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("    ") and len(line) > 4:
            # Check if it's 4-space indented
            if not (len(line) - len(line.lstrip())) % 4 == 0:
                errors.append(f"Line {i+1}: Incorrect indentation (must be multiples of 4 spaces)")
    
    # Check Setup/Teardown balance
    has_suite_setup = "Suite Setup" in script_content
    has_suite_teardown = "Suite Teardown" in script_content
    if has_suite_setup and not has_suite_teardown:
        errors.append("Suite Setup defined but no Suite Teardown")
    
    # Check resource paths
    for line in lines:
        if line.strip().startswith("Resource"):
            path = line.split("Resource")[1].strip()
            if not path.startswith("../resources/"):
                errors.append(f"Resource path should start with ../resources/: {path}")
    
    return errors
```

---

## Complete Pattern Library Summary

**Total Patterns**: 50+

| Category | Count | Resource File | Status |
|----------|-------|---------------|--------|
| Power Operations | 5 | pps_keywords.resource | ✅ Available |
| SSH Operations | 2 | ssh_keywords.resource | ✅ Available |
| CANoe/CAN Operations | 4 | canoe_keywords.resource | ✅ Available |
| DLT Operations | 3 | dlt_keywords.resource | ✅ Available |
| TRACE32 Operations | 6 | t32_keywords.resource | ✅ Available |
| Flash Operations | 2 | flashing_keywords.resource | ✅ Available |
| LUM Operations | 4 | lum_keywords.resource | ✅ Available |
| Component-Specific (RBM, stubs, etc.) | 20+ | Custom Keywords | ⚙️ Generated |

**Key Notes**:
- ✅ Available: Resource file exists in `robot/mpci_drb_automation/resources/`
- ⚙️ Generated: No dedicated resource file - generated as custom keywords in *** Keywords *** section
- Component-specific operations (RBM APIs, stub execution, custom verifications) are implemented as custom keywords using SSH Execute Command as foundation

**Example Resources**:
- Reference actual implementations: `robot/Example Robot Files/*.robot`
- See custom keyword patterns in files like `544530_TCS_RingBufferManagement_RBMBuffering_ADISS.robot`

---

**Usage**: These skills are invoked by rfw-generator.agent.md during the workflow. Each skill is a standalone function that can be tested independently.
