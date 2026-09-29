*** Settings ***
Documentation     Test suite for ADISS Client RBM Initialization.
...               
...               **Source Traceability:**
...               - Diagram: rbm_init.puml
...               - Test Case: tests/generated/tabular/TCS_RBM_Init_ADISS_Client.md
...               - Flow: Flow 1 - ADISS Client RBM Initialization
...               
...               This test verifies the complete RBM initialization sequence for ADISS client,
...               including version validation, callback registration, state queries, buffer content
...               creation, storage path retrieval, and standby state transition with callback verification.

Variables         ../configuration/test_bench.py
Resource          ../resources/ssh_keywords.resource
Resource          ../resources/rbm_keywords.resource
Resource          ../resources/pps_keywords.resource
Resource          ../resources/dlt_keywords.resource
Resource          ../resources/t32_keywords.resource

Suite Setup       Run Keywords    Connect To PPS
...              AND    Start Trace32 Debugger
...              AND    DLT Connect
Suite Teardown    Run Keywords    DLT Disconnect
...              AND    Stop Trace32 Debugger
...              AND    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot
...              AND    Connect To ECU Over SSH
...              AND    Verify RBM Daemon Running
...              AND    Verify ADISS Process Running
...              AND    Clean RBM Partition
Test Teardown     Disconnect SSH

*** Test Cases ***
TCS_RBM_Init_ADISS_Client
    [Documentation]    Test ADISS Client RBM Initialization sequence
    ...    
    ...    **Test Steps:**
    ...    1. Validate RBM version via ADISS
    ...    2. Register callback function
    ...    3. Request callback trigger
    ...    4. Query current RBM state
    ...    5. Create buffer/SW content
    ...    6. Get ADISS permanent storage path
    ...    7. Enter standby state with time sync validation
    ...    8. Verify state change callback received
    [Tags]    RBM    Initialization    ADISS    Client    uP

    # Step 1: RBM_GetVersion() via ADISS
    ${version_info}=    Validate RBM Version
    Log    RBM Version retrieved: ${version_info}

    # Step 2: RBM_RegCallBack() to register callback
    Register RBM Callback
    Log    RBM callback registered successfully

    # Step 3: RBM_ReqCbk() to trigger callback
    Request RBM Callback
    Log    RBM callback request sent

    # Step 4: RBM_GetState() query
    Verify ADISS Init State
    Log    ADISS RBM state verified as Init

    # Step 5: RBM_CreateBufswContent(arg0)
    Create ADISS Buffer Content Test
    Log    Buffer/SW content created successfully

    # Step 6: RBM_GetADISSPrmntStorgPth()
    ${storage_path}=    Get ADISS Permanent Storage Path
    Log    ADISS permanent storage path: ${storage_path}
    Should Not Be Empty    ${storage_path}    msg=Storage path should be returned

    # Step 7: RBM_EnterStandby() with conditional time sync validation
    Sync ECU Time
    Enter ADISS Standby
    Log    ADISS entered standby state

    # Step 8: Verify state change callback (RBM_Standby)
    Verify ADISS Standby State
    Log    State change callback verified - ADISS in Standby state

    # Post-condition verifications
    Verify ADISS State Is Standby
    ${final_path}=    Get ADISS Permanent Storage Path
    Should Be Equal    ${final_path}    ${storage_path}    msg=Storage path should remain consistent

*** Keywords ***
Verify RBM Daemon Running
    [Documentation]    Verify RBM daemon process is running on ECU
    ${result}=    Execute SSH Command    ps -e | grep rbm
    Should Contain    ${result}    rbm    msg=RBM daemon process not found

Verify ADISS Process Running
    [Documentation]    Verify ADISS process is running on ECU
    ${result}=    Execute SSH Command    ps -e | grep adiss
    Should Contain    ${result}    adiss    msg=ADISS process not found

Clean RBM Partition
    [Documentation]    Execute RBM_CleanPartition to prepare test environment
    Execute SSH Command    cd /usr/sbin
    ${result}=    Execute SSH Command    ./rbm_clean_partition
    Log    RBM partition cleaned: ${result}

Verify ADISS State Is Standby
    [Documentation]    Final verification that ADISS is in Standby state
    ${state}=    Get RBM State    ADISS
    Should Be Equal As Integers    ${state}    1    msg=Expected Standby state (1)

Stop Trace32 Debugger
    [Documentation]    Close TRACE32 debugger connection
    # Implementation depends on T32 API availability
    Log    TRACE32 debugger stopped
