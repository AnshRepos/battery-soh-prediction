
*** Settings ***
Documentation     Test suite for verifying RDC RBM Buffering transitions. Ensures correct state handling and event recording.
Variables         ../configuration/test_bench.py
Resource          ../resources/ssh_keywords.resource
Resource          ../resources/rbm_keywords.resource
Resource          ../resources/pps_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot
...              AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH

*** Test Cases ***
544625_TCS_RingBufferManagement_RBMBuffering_RDC
    [Documentation]    Test buffering transitions for RDC RBM, including event recording and state verification.
    RDC_RBM_Buffering_Preparation
    RDC_RBM_Buffering_Event_Recording
    RDC_RBM_Buffering_Finalization

*** Keywords ***
RDC_RBM_Buffering_Preparation
    [Documentation]    Prepare RDC RBM for buffering state.
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
    Exit RBM Stub
    Kill SDSRDC Process
    Launch SDSRDC Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify SDSRDC Buffering State

RDC RBM Buffering Event Recording
    ${euuid}=    Trigger SDSRDC Single Event Record And Verify Folder
    Add SDSRDC Metadata    ${euuid}
    Delete SDSRDC Entry    ${euuid}
    ${trigger_handle}=    Trigger SDSRDC Continuous Event Record
    Stop SDSRDC Event Record And Verify    ${trigger_handle}
    ${trigger_handle}=    Trigger SDSRDC Event Record On
    Stop SDSRDC Event Record And Verify    ${trigger_handle}    metaStop    5    khihg
    ${trigger_handle}=    Trigger SDSRDC Event Record On
    Stop SDSRDC Event Record Off And Verify    ${trigger_handle}

RDC RBM Buffering Finalization
    Get Number Of Ongoing Triggers
