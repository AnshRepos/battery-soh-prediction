# RQM sync skipped by user — no RQM Test Case ID / URL associated with this script.
# Generated standalone from local test design: tests/generated/tabular/TCS_RBM_Init_RDC_Client.md

*** Settings ***
Documentation     Test suite for verifying the RBM initialization sequence invoked by the
...               RDC client, covering version/state queries, callback registration, and
...               RDC-specific persistent storage path retrieval.
...
...               Architecture Baseline Version: v0.3.1
...               Source: rbm_init.puml (Flow 2)
...               Platform Type: uP (QNX/Linux ECU, SSH, CANoe, DLT Viewer)

Variables         ../../robot/mpci_drb_automation/configuration/test_bench.py

Resource          ../../robot/mpci_drb_automation/resources/pps_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/flashing_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/ssh_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/dlt_keywords.resource

Suite Setup       Setup RBM RDC Client Test Environment
Suite Teardown    Teardown RBM RDC Client Test Environment

*** Test Cases ***
TCS_RBM_Init_RDC_Client
    [Documentation]    Verifies the RBM initialization sequence invoked by the RDC client:
    ...                version query, ack verification, callback registration/request,
    ...                state query, and RDC persistent storage path retrieval.
    [Tags]             RBM    RDC    Init    uP    Integration

    # Step 1: Call RBM_GetVersion() via RDC
    ${version_output}=    Execute RDC Client Command    RBM_GetVersion()
    Verify RBM Version Response    ${version_output}

    # Step 2: Verify acknowledgement response after RBM_GetVersion() call
    Verify RBM Acknowledgement    ${version_output}

    # Step 3: Call RBM_ReqCbk() via RDC with reason = RBM_StorSize
    Execute RDC Client Command    RBM_ReqCbk(reason=RBM_StorSize)
    Verify RBM Storage Size Callback

    # Step 4: Call RBM_GetState() via RDC
    ${state_output}=    Execute RDC Client Command    RBM_GetState()
    Verify RBM State Is Init    ${state_output}

    # Step 5: Call RBM_GetRDCPrmntStorgPth() via RDC
    ${storage_path_output}=    Execute RDC Client Command    RBM_GetRDCPrmntStorgPth()
    Get RBM RDC Persistent Storage Path    ${storage_path_output}

*** Keywords ***
Setup RBM RDC Client Test Environment
    [Documentation]    Applies pre-conditions: power-up, flash release SW, SSH/serial
    ...                connection, DLT init, and process/state verification.
    Log To Console    \n========== [SETUP] Initializing RBM RDC Client Test Environment ==========
    Connect To PPS
    Configure Power Supply
    Power On ECU
    Flash ECU Software
    Connect To ECU Over SSH
    Initialize DLT Configuration
    Verify Process Is Running    rdcd
    Verify Process Is Running    rbmd
    Verify RBM Shared Library Is Available
    Verify RBM Is In Init State
    Log To Console    ========== [SETUP] Environment Ready ==========

Teardown RBM RDC Client Test Environment
    [Documentation]    Applies post-conditions in LIFO order: verify RBM remains in
    ...                RBM_Init state, power down the ECU, close SSH connection.
    Log To Console    \n========== [TEARDOWN] Cleaning Up ==========
    ${final_state}=    Execute RDC Client Command    RBM_GetState()
    Verify RBM State Is Init    ${final_state}
    Disconnect SSH
    Power Off ECU
    Disconnect PPS
    Cleanup Test Environment
    Log To Console    ========== [TEARDOWN] Complete ==========

Execute RDC Client Command
    [Documentation]    Executes an RBM API command via the RDC test client over SSH.
    ...                TODO: Confirm actual RDC client binary path / CLI syntax with firmware team.
    [Arguments]    ${command}
    Log To Console    [RDC CLIENT] Executing: ${command}
    ${output}=    Execute Command    /usr/bin/rdc_test_client --command "${command}"
    RETURN    ${output}

Verify RBM Version Response
    [Documentation]    Verifies RBM_GetVersion() returns RBM_ok and a valid
    ...                major.minor.revision version string.
    [Arguments]    ${output}
    Should Contain    ${output}    Return Value = 0 (RBM_ok)
    Log    ${output}
    # TODO: Add regex match for major.minor.revision format once exact log format is confirmed.

Verify RBM Acknowledgement
    [Documentation]    Verifies the acknowledgement response received after RBM_GetVersion().
    [Arguments]    ${output}
    Should Contain    ${output}    Return Value = 0 (RBM_ok)
    Log    Acknowledgement received: ${output}

Verify RBM Storage Size Callback
    [Documentation]    Waits for and verifies the async RBM_StorSize callback via DLT logs
    ...                after RBM_ReqCbk() is invoked.
    Wait Until Keyword Succeeds    10s    1s    Check For DLT Log    RBM_StorSize
    Log    RBM_StorSize callback received containing available RDC storage size value.

Verify RBM State Is Init
    [Documentation]    Verifies RBM_GetState() returns RBM_ok and RBMState = RBM_Init (state code = 0).
    [Arguments]    ${output}
    Should Contain    ${output}    Return Value = 0 (RBM_ok)
    Should Contain    ${output}    RBM_Init
    Log    ${output}

Get RBM RDC Persistent Storage Path
    [Documentation]    Verifies RBM_GetRDCPrmntStorgPth() returns RBM_ok and a valid
    ...                RDC persistent storage location.
    [Arguments]    ${output}
    Should Contain    ${output}    Return Value = 0 (RBM_ok)
    Should Not Be Empty    ${output}
    Log    Storage Path: ${output}

Verify Process Is Running
    [Documentation]    Verifies that a given process is running on the target via 'ps -e'.
    [Arguments]    ${process_name}
    ${output}=    Execute Command    ps -e | grep ${process_name}
    Should Not Be Empty    ${output}
    Log To Console    [OK] Process '${process_name}' is running.

Verify RBM Shared Library Is Available
    [Documentation]    Verifies the RBM API interface (librbm_shared_lib.so) is available at /usr/lib.
    ${output}=    Execute Command    ls /usr/lib | grep librbm_shared_lib.so
    Should Not Be Empty    ${output}
    Log To Console    [OK] librbm_shared_lib.so found at /usr/lib.

Verify RBM Is In Init State
    [Documentation]    Confirms RBM is currently in RBM_Init state before starting the sequence.
    ${output}=    Execute RDC Client Command    RBM_GetState()
    Verify RBM State Is Init    ${output}

Check For DLT Log
    [Documentation]    Checks for a specific string in the DLT logs.
    ...                TODO: Replace placeholder log path with actual DLT capture file/live search
    ...                via dlt_keywords.resource (e.g. Search Logs keyword).
    [Arguments]    ${log_string}
    Log    Searching for '${log_string}' in DLT logs.
    ${logs}=    Execute Command    grep ${log_string} /tmp/dlt_capture.log
    Should Not Be Empty    ${logs}
