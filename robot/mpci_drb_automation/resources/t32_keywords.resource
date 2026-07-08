*** Settings ***
Documentation    Keywords for Trace32 debugger operations and testing
Variables    ../configuration/test_bench.py
Library    String
Library    Collections
Library    rfw.lib.T32lib.T32lib
...    ${config_file_contents}
...    ${dll_path}
...    ${exe_path}
...    ${config_file_path}
...    ${cmm_script_path}
...    ${ftti_time_limit}


*** Variables ***
${ELF_FILE}    C:/build/output/application.elf
${TRACE32_DEBUG_FILE}   C:/Users/WPW2KOR/Downloads/PI25_4_BF4/drb_r5f.debug
@{FUNCTION_SEQUENCE}    rb_pcb_tempmon_main_func    rb_Iic_Read   rb_Gpio_BankRead    rbIpi3_WriteBuffer    rb_Canfd_CopySafetyPDU
${SEQ_INDEX}    0


*** Keywords ***
Initialize Trace32 Test Environment
    [Documentation]    Initialize Trace32 test environment with PPS and SSH connections
    Connect To PPS
    Configure Power Supply
    Power On ECU
    Connect To ECU Over SSH
    Log To Console    \n=========================================
    Log To Console    [INIT] Starting CANoe Initialization
    Log To Console    =========================================
    Log To Console    [INIT] Using config: ${ONE_RBS}
    ${normalized_cfg}=    Normalize Path    ${ONE_RBS}
    Log To Console    [INIT] Normalized CANoe cfg: ${normalized_cfg}
    Can Initialization    ${normalized_cfg}

Cleanup Trace32 Test Environment
    [Documentation]    Clean up Trace32 test environment and disconnect all connections
    Can Disconnect
    Disconnect SSH
    Disconnect PPS

Power Cycle
    [Documentation]    Perform power cycle of ECU
    Power Off ECU
    Power On ECU

Start Trace32 Debugger
    [Documentation]    Start Trace32 debugger and load CMM script
    T32 Start
    T32 Send Command    DO "${cmm_script_path}"
    Sleep     10s
    T32 Get State

Load Debug File
    [Documentation]    Load debug file (ELF) into Trace32
    T32 Send Command    Data.LOAD.Elf ${TRACE32_DEBUG_FILE} /nocode
    T32 Get State

Attach Trace32 To Target
    [Documentation]    Attach Trace32 debugger to target system
    T32 Send Command    SYStem.Mode Attach

Halt Target Execution
    [Documentation]    Halt target execution using breakpoint
    T32 Send Command    Break

Resume Execution
    [Documentation]    Resume target execution
    T32 Go
    Sleep   3s

Set Breakpoints For FUNCTIONS
  [Documentation]    Set breakpoints for specified functions
  [Arguments]   @{func_list}
  FOR   ${func}   IN    @{func_list}
      Log To Console    Setting breakpoint for ${func}
      ${addr}   ${access}=    T32 Get Symbol    ${func}  # ${size} variable removed as unused
      T32 Write Breakpoint    ${addr}   ${access}   1   1
      Log    Breakpoint set for '${func}' at address '${addr}'

  END

Get Current Program Counter
    [Documentation]    Get current program counter value and convert to symbol format
    T32 Send Command    PRINT Register(PC)
    ${pc}=    T32 Get Message
    Log    PC=${pc}

    ${sr}=    Convert Address To Symbol Format     ${pc}
    Log    SR=${sr}
    RETURN    ${sr}

Get Current Function Name
    [Documentation]    Get current function name from program counter
    ${sr}=    Get Current Program Counter

    T32 Send Command    PRINT SYmbol.FUNCTION(${sr})
    ${func}=    T32 Get Message

    Log    FUNCTION=${func}

    ${function_name}=  Extract Function Name       ${func}
    Log    Function Name=${function_name}
    RETURN    ${function_name}

Extract Function Name
    [Documentation]    Extract function name from full path
    [Arguments]    ${full_path}
    @{parts}=    Split String    ${full_path}    \\
    ${func}=    Set Variable    ${parts}[-1]
    RETURN    ${func}

Validate Function In Sequence
    [Documentation]    Validate that current function matches expected sequence
    ${current_function}=    Get Current Function Name
    Log     Current Function= ${current_function}
    IF    ${SEQ_INDEX}
        ${next_index}=    Evaluate    ${SEQ_INDEX} + 1
        ${next_function}=    Get From List    ${FUNCTION_SEQUENCE}     ${next_index}

        WHILE    ${current_function} != ${next_function}
            Log    Function ${current_function} is looping. Resuming execution...
            Resume Execution
            ${current_function}=    Get Current Function Name
        END
    END
    ${expected}=    Get From List    ${FUNCTION_SEQUENCE}    ${SEQ_INDEX}

    Log    Expected=${expected} | Actual=${current_function}

    Should Be Equal    ${current_function}    ${expected}

    ${SEQ_INDEX}=    Evaluate    ${SEQ_INDEX} + 1
    Set Suite Variable    ${SEQ_INDEX}

Convert Address To Symbol Format
    [Documentation]    Convert address to symbol format for Trace32
    [Arguments]    ${pc}
    ${pc_hex}=    Evaluate    format(int("${pc}", 16), "08X")
    ${sr}=    Set Variable    SR:${pc_hex}
    RETURN    ${sr}
