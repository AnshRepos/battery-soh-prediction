# Robot Framework Generator - Execution Instructions

**Purpose**: Step-by-step workflow execution guide for rfw-generator agent. Follow these instructions exactly during test script generation.

---

## Handoff Input Format (When Called from rqm-uploader)

When invoked via `runSubagent` from rqm-uploader, you will receive a handoff payload in the prompt:

```json
{
  "local_file": "tests/generated/tabular/TCS_OPMM_PreRun_To_Run.md",
  "rqm_test_id": "145711",
  "rqm_url": "https://rb-alm-14-p.de.bosch.com/qm/...",
  "platform_type": "uP",
  "test_case_name": "TCS_OPMM_PreRun_To_Run"
}
```

**Field Descriptions**:
- `local_file`: Full path to the local Markdown test case file (4-column table format)
- `rqm_test_id`: Numeric RQM test case ID (used for traceability comment in .robot file)
- `rqm_url`: Full URL to the RQM test case (used for traceability comment)
- `platform_type`: Either "uP" (Microprocessor/QNX) or "uC" (Microcontroller/bare-metal) - hint from test-generator
- `test_case_name`: Test case title (used for output filename)

**How to Extract Payload**:
Parse the prompt text for the JSON payload structure. If present, set `invoked_from_handoff = true`. If not present, this is a standalone invocation and you should prompt the user for the file path.

**Standalone Invocation**:
When user calls directly (e.g., `@rfw-generator Generate robot script from tests/generated/tabular/TCS_Test.md`), extract the file path from the user's message and set `invoked_from_handoff = false`.

---

## Workflow Overview

```
START
  ↓
[Checkpoint 0: Input Validation] 🛑
  ↓
[Step 1: Parse Test Case]
  ↓
[Step 2: Detect Platform Type]
  ↓
[Step 3: Pattern Recognition]
  ↓
[Step 4: Resource Determination]
  ↓
[Step 5: Script Generation]
  ↓
[Checkpoint 1: Review Script] 🛑
  ↓
[Step 6: Save Robot File]
  ↓
[Checkpoint 2: Confirm Save] 🛑
  ↓
END ✓
```

---

## Checkpoint 0: Input Validation

### Trigger
- At workflow start, before any processing
- Applies to both standalone and handoff invocations

### Actions

1. **Verify Input Source**
   ```
   IF invoked_from_handoff:
       payload = received_handoff_payload
       file_path = payload["local_file"]
       platform_hint = payload.get("platform_type")
       rqm_info = {
           "test_id": payload.get("rqm_test_id"),
           "url": payload.get("rqm_url")
       }
   ELSE:
       file_path = user_provided_path
       platform_hint = None
       rqm_info = None
   ```

2. **MANDATORY: Validate File Exists**
   ```python
   # CRITICAL: MUST verify file exists before proceeding
   # Extract folder and filename from path
   folder_path = extract_folder_from_path(file_path)
   file_name = extract_filename_from_path(file_path)
   
   # Use list_dir to check folder contents
   folder_contents = list_dir(folder_path)
   
   if file_name not in folder_contents:
       ERROR: "❌ CRITICAL: Local test case file not found!"
       ERROR: f"Expected file: {file_path}"
       ERROR: f"Folder path: {folder_path}"
       ERROR: f"Folder contents: {folder_contents}"
       ERROR: "The test case file must be created before Robot Framework generation."
       ERROR: "Workflow failure: File creation was skipped or failed in previous step."
       
       if invoked_from_handoff:
           ERROR: "This is a workflow bug - the calling agent should have created the file."
           ERROR: "The test-generator or rqm-uploader agent must verify file creation."
       else:
           ERROR: "Please provide the correct path to an existing test case file."
       
       STOP WORKFLOW
       DO NOT PROCEED with Robot generation
       RETURN error to calling agent
   
   print(f"✅ Local file verified: {file_path}")
   print(f"✅ Folder: {folder_path}")
   print(f"✅ File exists in folder: {file_name}")
   ```

3. **Validate File Format**
   ```python
   content = read_file(file_path)
   
   # Check required sections
   required = [
       "Test Case Name:",
       "Pre-Condition",
       "| Steps | Input Operations | Expected Result | Actual Results |",
       "Post-Condition"
   ]
   
   missing = []
   for section in required:
       if section not in content:
           missing.append(section)
   
   if missing:
       ERROR: "Missing required sections: {missing}"
       User options: ["fix file", "cancel"]
       STOP
   ```

4. **Display Validation Summary**
   ```
   Input file: {file_path}
   File format: ✓ Valid (4-column table detected)
   Required fields: ✓ All present
     - Test Case Name: {name}
     - Pre-Conditions: {count} items
     - Test Steps: {count} steps
     - Post-Conditions: {count} items
   
   {IF from_handoff}
   RQM Test Case ID: {rqm_info.test_id}
   RQM URL: {rqm_info.url}
   Platform Type: {platform_hint} (from handoff)
   {ENDIF}
   ```

5. **Wait for User Confirmation**
   
   **Use vscode_askQuestions**:
   ```typescript
   vscode_askQuestions({
     questions: [{
       header: "Input Validation",
       question: "File validation complete. Proceed with Robot Framework generation?",
       message: `Input file: ${file_path}\nFile format: ✓ Valid\nTest Case: ${test_case_name}`,
       options: [
         { label: "Proceed with generation", description: "Start generating Robot Framework script", recommended: true },
         { label: "Show file content", description: "View raw Markdown content" },
         { label: "Cancel", description: "End workflow" }
       ]
     }]
   })
   ```
   
   Handle response accordingly.

---

## Step 1: Parse Test Case

### Actions

1. **Extract Metadata**
   ```python
   test_case = parse_test_case_markdown(file_path)
   # Returns: {name, arch_version, source, platform_type, pre_conditions, test_steps, post_conditions}
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 1 for parsing algorithm.

2. **Validate Parsed Data**
   ```python
   if not test_case["name"]:
       ERROR: "Test case name not found"
       STOP
   
   if not test_case["test_steps"]:
       ERROR: "No test steps found"
       STOP
   ```

3. **Log Parsing Results**
   ```
   [Step 1] Parsing test case... ✓
   - Name: {test_case.name}
   - Architecture Version: {test_case.arch_version}
   - Source: {test_case.source}
   - Pre-Conditions: {len(test_case.pre_conditions)} items
   - Test Steps: {len(test_case.test_steps)} steps
   - Post-Conditions: {len(test_case.post_conditions)} items
   ```

---

## Step 2: Detect Platform Type

### Actions

1. **Check for Platform Hint**
   ```python
   if platform_hint:
       platform_type = platform_hint
       print(f"[Step 2] Platform type: {platform_type} (from handoff) ✓")
       SKIP detection, go to Step 3
   ```

2. **Run Detection Algorithm**
   ```python
   platform_type = detect_platform_type(
       test_case["pre_conditions"],
       test_case["test_steps"],
       platform_hint=None
   )
   # Returns: "uP", "uC", or None (ambiguous)
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 2 for detection algorithm.

3. **Handle Ambiguous Case**
   ```python
   if platform_type is None:
       print("[Step 2] Platform type: Ambiguous - asking user...")
       user_response = prompt_user(
           "Is this for uP (Microprocessor) or uC (Microcontroller)?",
           options=["uP", "uC"]
       )
       platform_type = user_response
   ```

4. **Log Detection Results**
   ```
   [Step 2] Platform type detected: {platform_type} ✓
   {IF uP}
   Indicators: SSH connection, Putty mentioned, Linux commands
   {ELIF uC}
   Indicators: TRACE32 only, no SSH, bare-metal operations
   {ENDIF}
   ```

---

## Step 3: Pattern Recognition

### Actions

1. **Extract Component Name**
   ```python
   component = extract_component_from_test_name(test_case["name"])
   if not component:
       # Try to find in steps
       for step in test_case["test_steps"]:
           component = extract_component_from_operation(step["input_operation"])
           if component:
               break
   ```

2. **Match Operations to Keywords**
   ```python
   matched_keywords = []
   
   for step in test_case["test_steps"]:
       operation = step["input_operation"]
       
       match_result = match_operation_to_keyword(operation, component)
       # Returns: {keyword, resource, variable?, argument?, custom_needed?}
       
       matched_keywords.append({
           "step_num": step["step_num"],
           "operation": operation,
           "match": match_result
       })
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 3 for pattern matching.

3. **Count Pattern Categories**
   ```python
   categories = {
       "power": 0,
       "ssh": 0,
       "rbm_api": 0,
       "process": 0,
       "trace32": 0,
       "canoe": 0,
       "dlt": 0,
       "unknown": 0
   }
   
   for match in matched_keywords:
       resource = match["match"].get("resource")
       if "pps_keywords" in resource:
           categories["power"] += 1
       elif "ssh_keywords" in resource:
           categories["ssh"] += 1
       # ... etc
       elif match["match"].get("custom_needed"):
           categories["unknown"] += 1
   ```

4. **Log Recognition Results**
   ```
   [Step 3] Pattern recognition: {len(matched_keywords)} operations mapped ✓
   {IF component}
   - Component identified: {component}
   {ENDIF}
   - Power operations: {categories.power}
   - SSH operations: {categories.ssh}
   - RBM API operations: {categories.rbm_api}
   - Process operations: {categories.process}
   {IF categories.unknown > 0}
   - Unknown operations: {categories.unknown} (will generate TODOs)
   {ENDIF}
   ```

---

## Step 4: Resource Determination

### Actions

1. **Determine Required Resources**
   ```python
   resources = determine_required_resources(
       test_case["test_steps"],
       platform_type
   )
   # Returns: list of resource file paths
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 4 for resource determination.

2. **Add Always-Required Resources**
   ```python
   variables = ["../configuration/test_bench.py"]
   ```

3. **Log Resource Results**
   ```
   [Step 4] Resources needed: {len(resources)} files ✓
   {FOR resource IN resources}
   - {resource}
   {ENDFOR}
   - Variables: ../configuration/test_bench.py
   ```

---

## Step 5: Script Generation

### Actions

1. **Generate Setup/Teardown**
   ```python
   setup_teardown = generate_setup_teardown(
       test_case["pre_conditions"],
       test_case["post_conditions"],
       platform_type
   )
   # Returns: {suite_setup, suite_teardown, test_setup, test_teardown}
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 5 for setup/teardown generation.

2. **Generate Test Case Body**
   ```python
   keywords = generate_test_case_body(
       test_case["test_steps"],
       component
   )
   # Returns: list of keyword dicts
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 6 for test case body generation.

3. **Format Keywords as Robot**
   ```python
   body_text = format_keywords_as_robot(keywords, indent=4)
   ```

4. **Generate Documentation**
   ```python
   # From test case name
   doc_text = f"Test suite for verifying {component} {extract_flow_name(test_case['name'])}."
   
   # Generate tags
   tags = [component] if component else []
   if "Standby" in test_case["name"]:
       tags.append("Standby")
   if "Buffering" in test_case["name"]:
       tags.append("Buffering")
   tags.append("Integration")  # Default
   ```

5. **Assemble Complete Script**
   ```python
   script = f"""*** Settings ***
Documentation     {doc_text}
Variables         {variables[0]}
"""
   
   # Add resources
   for resource in resources:
       script += f"Resource          {resource}\n"
   
   script += "\n"
   
   # Add setup/teardown
   if setup_teardown["suite_setup"]:
       script += f"Suite Setup       {setup_teardown['suite_setup']}\n"
   if setup_teardown["suite_teardown"]:
       script += f"Suite Teardown    {setup_teardown['suite_teardown']}\n"
   if setup_teardown["test_setup"]:
       script += f"Test Setup        {setup_teardown['test_setup']}\n"
   if setup_teardown["test_teardown"]:
       script += f"Test Teardown     {setup_teardown['test_teardown']}\n"
   
   script += "\n*** Test Cases ***\n"
   script += f"{test_case['name']}\n"
   script += f"    [Documentation]    {doc_text}\n"
   script += f"    [Tags]             {' '.join(tags)}\n"
   script += body_text
   
   # Add RQM traceability if from handoff
   if rqm_info:
       script = f"# RQM Test Case ID: {rqm_info['test_id']}\n"
       script += f"# RQM URL: {rqm_info['url']}\n\n"
       script += script
   ```

6. **Validate Generated Script**
   ```python
   errors = validate_robot_syntax(script)
   if errors:
       print("[Step 5] Validation warnings:")
       for error in errors:
           print(f"  - {error}")
   ```
   See `.github/instructions/rfw-generator.skills.md` Skill 8 for validation rules.

7. **Log Generation Results**
   ```
   [Step 5] Generating script... ✓
   - Settings section: ✓
   - Setup/Teardown: ✓
   - Test Cases section: ✓
   - Total lines: {len(script.split('\n'))}
   {IF errors}
   - Validation warnings: {len(errors)} (see above)
   {ENDIF}
   ```

---

## Checkpoint 1: Review Generated Script

### Trigger
- After script generation (Step 5)
- Before saving to disk

### Actions

1. **Display Complete Script**
   ```
   [Checkpoint 1] Generated script preview:
   ════════════════════════════════════════════════════════
   {script}
   ════════════════════════════════════════════════════════
   
   Script statistics:
   - Total lines: {line_count}
   - Keywords: {keyword_count}
   - Resources imported: {resource_count}
   {IF rqm_info}
   - RQM Test Case: {rqm_info.test_id}
   {ENDIF}
   ```

2. **Wait for User Response**
   
   **Use vscode_askQuestions**:
   ```typescript
   vscode_askQuestions({
     questions: [{
       header: "Review Generated Script",
       question: "Robot Framework script generated. What would you like to do?",
       message: `[Display complete script here]\n\nStatistics:\n- Total lines: ${line_count}\n- Keywords: ${keyword_count}\n- Resources: ${resource_count}${rqm_info ? '\n- RQM Test Case: ' + rqm_info.test_id : ''}`,
       options: [
         { label: "Save file", description: "Save the script to disk", recommended: true },
         { label: "Modify script", description: "Make changes to the generated script" },
         { label: "Regenerate", description: "Start over with different settings" },
         { label: "Cancel", description: "Discard script and end workflow" }
       ]
     }]
   })
   ```

3. **Handle User Response**
   ```python
   if response == "Save file":
       goto Step 6
   elif response == "Modify script":
       # Ask for modification details in natural language
       modification = prompt_user("Describe the changes you want:")
       apply_modifications(script, modification)
       goto Checkpoint 1 (show updated script)
   elif response == "Regenerate":
       ask_what_to_change = prompt_user(
           "What should be regenerated?",
           options=["Pattern matching", "Setup/Teardown", "Everything"]
       )
       goto appropriate step
   elif response == "Cancel":
       END workflow
   ```

---

## Step 6: Save Robot File

### Actions

1. **Determine Output Path**
   ```python
   output_dir = "tests/generated/robot-framework/"
   ensure_directory_exists(output_dir)
   
   filename = f"{test_case['name']}.robot"
   output_path = os.path.join(output_dir, filename)
   ```

2. **Check for Existing File**
   ```python
   if file_exists(output_path):
       overwrite_warning = True
   else:
       overwrite_warning = False
   ```

3. **Calculate File Size**
   ```python
   file_size_kb = len(script.encode('utf-8')) / 1024
   ```

---

## Checkpoint 2: Confirm Save

### Trigger
- After determining output path (Step 6)
- Before writing file to disk

### Actions

1. **Display Save Information**
   ```
   [Checkpoint 2] Ready to save file:
   
   Output path: {output_path}
   File size: {file_size_kb:.1f} KB
   {IF overwrite_warning}
   ⚠️  Warning: File already exists and will be overwritten
   {ENDIF}
   {IF rqm_info}
   RQM Test Case ID: {rqm_info.test_id}
   RQM URL: {rqm_info.url}
   {ENDIF}
   ```

2. **Wait for User Confirmation**
   
   **Use vscode_askQuestions**:
   ```typescript
   vscode_askQuestions({
     questions: [{
       header: "Confirm Save",
       question: "Ready to save Robot Framework script. Confirm?",
       message: `Output path: ${output_path}\nFile size: ${file_size_kb} KB${overwrite_warning ? '\n⚠️ Warning: File already exists and will be overwritten' : ''}${rqm_info ? '\n\nRQM Test Case ID: ' + rqm_info.test_id + '\nRQM URL: ' + rqm_info.url : ''}`,
       options: [
         { label: "Save file", description: "Write script to disk", recommended: true },
         { label: "Change path", description: "Specify different output location" },
         { label: "Cancel", description: "Discard script and end workflow" }
       ]
     }]
   })
   ```

3. **Handle User Response**
   ```python
   if response == "Save file":
       try:
           # Use create_file tool
           create_file(output_path, script)
           
           # MANDATORY: Verify file was actually created
           # Extract folder and filename
           folder_path = "tests/generated/robot-framework"
           file_name = f"{test_case['name']}.robot"
           
           # Use list_dir to check folder contents
           folder_contents = list_dir(folder_path)
           
           if file_name not in folder_contents:
               ERROR: "❌ CRITICAL: Failed to create Robot Framework file!"
               ERROR: f"Expected file: {output_path}"
               ERROR: f"Folder path: {folder_path}"
               ERROR: f"Folder contents: {folder_contents}"
               ERROR: "File creation returned success but file does not exist."
               ERROR: "This is a workflow bug - file system operation failed."
               raise Exception("File creation verification failed")
           
           # Read and display file preview (first 30 lines)
           file_content = read_file(output_path, start_line=1, end_line=30)
           
           print(f"✅ Robot Framework script saved and verified!")
           print(f"📄 Path: {output_path}")
           print(f"📊 Preview:")
           print(file_content)
           print(f"   Size: {file_size_kb:.1f} KB")
           print(f"   File verified: ✓")
           
           if rqm_info:
               print(f"   Linked to RQM Test Case: {rqm_info.test_id}")
           
           # Return success response for handoff
           return {
               "success": true,
               "robot_file_path": output_path,
               "test_case_name": test_case["name"],
               "rqm_info": rqm_info
           }
           
           goto END
       except Exception as e:
           ERROR: f"Failed to save file: {e}"
           # Retry checkpoint
   
   elif response == "Change path":
       new_path = prompt_user("Enter new output path:")
       output_path = new_path
       goto Checkpoint 2  # Re-display with new path
   
   elif response == "Cancel":
       print("Workflow cancelled. Script not saved.")
       END workflow
   ```

---

## Error Handling

### File Not Found
```
ERROR: File not found: {file_path}
Action: Ask user for correct path or cancel
```

### Invalid Format
```
ERROR: Invalid file format
Details: Missing sections: {missing_sections}
Action: Ask user to fix file or cancel
```

### Unknown Operations
```
WARNING: Unknown operation patterns detected: {count}
Details: {list of unknown operations}
Action: Generate TODOs in script, continue with warning
```

### Platform Type Ambiguous
```
WARNING: Cannot determine platform type
Action: Prompt user: "Is this for uP or uC?"
```

### Validation Errors
```
WARNING: Script validation issues: {count}
Details: {list of issues}
Action: Display warnings, continue if not critical
```

### Save Failed
```
ERROR: Failed to save file: {error_message}
Action: Offer retry or cancel
```

---

## Best Practices

### During Parsing
- Be lenient with format variations
- Log what was found vs expected
- Continue with warnings if possible

### During Pattern Matching
- Try multiple pattern variations
- Extract component from multiple sources
- Generate TODOs for unknown operations

### During Script Generation
- Follow Robot Framework style guide
- Use 4-space indentation
- Add documentation strings
- Include meaningful tags

### During Checkpoints
- Give clear options to user
- Show complete context (file size, path, etc.)
- Allow modifications without restarting

### Error Messages
- Be specific about what went wrong
- Suggest concrete fixes
- Provide alternatives to canceling

---

## Workflow Completion

### Success Path
```
[Checkpoint 0] ✓ Input validated
[Step 1] ✓ Test case parsed
[Step 2] ✓ Platform type detected: {type}
[Step 3] ✓ Pattern recognition: {count} operations
[Step 4] ✓ Resources determined: {count} files
[Step 5] ✓ Script generated
[Checkpoint 1] ✓ User approved: "save"
[Step 6] ✓ Output path determined
[Checkpoint 2] ✓ User confirmed: "Save file"

✅ Robot Framework script saved successfully!
   Path: {output_path}
   Size: {file_size_kb:.1f} KB
   {IF rqm_info}
   Linked to RQM Test Case: {rqm_info.test_id}
   {ENDIF}
```

### User Cancel Path
```
[Checkpoint X] User selected: "cancel"

Workflow canceled. No files were modified.
```

---

## Testing Checklist

Before considering workflow complete, verify:

- [ ] File was saved to correct location
- [ ] File has valid Robot Framework syntax
- [ ] All sections present (Settings, Test Cases)
- [ ] Resources imported with correct paths
- [ ] Setup/Teardown balanced
- [ ] Test case name matches filename
- [ ] Documentation strings present
- [ ] Metadata file created (if applicable)
- [ ] RQM traceability added (if from handoff)

---

**Remember**: Follow this workflow exactly. Use checkpoints to give user control. Generate clean, valid Robot Framework code.
