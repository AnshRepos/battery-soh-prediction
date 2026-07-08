
*** Settings ***
Documentation     Test suite for verifying ADISS RBM Standby and Buffering transitions. Ensures correct state handling and event recording.
Variables         ../configuration/test_bench.py
Resource          ../resources/ssh_keywords.resource
Resource          ../resources/rbm_keywords.resource
Resource          ../resources/pps_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot    AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH

*** Test Cases ***
542327_TCS_RingBufferManagement_RBMStandby_ADISS
    [Documentation]    Test standby and buffering transitions for ADISS RBM, including event recording and state verification.
    Sync ECU Time
    Kill ADISS Process
    Launch ADISS Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Init State
    Create ADISS Buffer Content Test
    Enter ADISS Standby
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Standby State
    Enter ADISS Buffering
    ${euuid}=    Trigger ADISS Single Event Record And Verify Folder
    Add ADISS Metadata    ${euuid}
    Delete ADISS Entry    ${euuid}
    Verify ADISS Buffering State
    Enter ADISS Standby
    Verify ADISS Standby State
    Reinitialize ADISS

