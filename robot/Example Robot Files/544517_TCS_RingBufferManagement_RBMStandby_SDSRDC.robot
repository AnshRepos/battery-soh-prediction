
*** Settings ***
Documentation     Test suite for verifying SDSRDC RBM Standby and Buffering transitions. Ensures correct state handling and event recording.
Variables         ../configuration/test_bench.py
Resource          ../resources/ssh_keywords.resource
Resource          ../resources/rbm_keywords.resource
Resource          ../resources/pps_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot    AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH

*** Test Cases ***
544517_TCS_RingBufferManagement_RBMStandby_SDSRDC
    [Documentation]    Test standby and buffering transitions for SDSRDC RBM, including event recording and state verification.
    Sync ECU Time
    # Phase 1: ADISS drives state to Standby
    Kill ADISS Process
    Launch ADISS Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Init State
    Create ADISS Buffer Content Test
    Enter ADISS Standby
    Verify ADISS Standby State
    Exit RBM Stub

    # Phase 2: SDSRDC verifies Standby and cleans partition (RBM stays in Standby)
    Launch SDSRDC Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify SDSRDC Standby State
    Clean SDSRDC Partition
    Exit RBM Stub

    # Phase 3: ADISS drives state to Buffering
    Launch ADISS Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Standby State
    Enter ADISS Buffering
    Exit RBM Stub

    # Phase 4: SDSRDC verifies Buffering state and triggers event record
    Launch SDSRDC Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify SDSRDC Buffering State
    ${euuid}=    Trigger SDSRDC Single Event Record And Verify Folder
    Add SDSRDC Metadata    ${euuid}
    Delete SDSRDC Entry    ${euuid}
    Exit RBM Stub

    # Phase 5: ADISS cleanup
    Launch ADISS Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Buffering State
    Enter ADISS Standby
    Verify ADISS Standby State
    Reinitialize ADISS
