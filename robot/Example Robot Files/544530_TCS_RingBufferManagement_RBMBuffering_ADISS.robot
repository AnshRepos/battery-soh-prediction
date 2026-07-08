
*** Settings ***
Documentation     Test suite for verifying ADISS RBM Buffering transitions. Ensures correct state handling and event recording.
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
544530_TCS_RingBufferManagement_RBMBuffering_ADISS
    [Documentation]    Test buffering transitions for ADISS RBM, including event recording and state verification.
    ADISS_RBM_Buffering_Preparation
    ADISS_RBM_Buffering_Event_Recording
    ADISS_RBM_Buffering_Finalization

*** Keywords ***
ADISS_RBM_Buffering_Preparation
    [Documentation]    Prepare ADISS RBM for buffering state.
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
    [Documentation]    Record and verify ADISS RBM buffering events.
    ${euuid}=    Trigger ADISS Single Event Record And Verify Folder
    Add ADISS Metadata    ${euuid}
    Delete ADISS Entry    ${euuid}
    ${trigger_handle}=    Trigger ADISS Continuous Event Record
    Stop ADISS Event Record And Verify    ${trigger_handle}
    ${trigger_handle}=    Trigger ADISS Event Record On
    Stop ADISS Event Record And Verify    ${trigger_handle}    metaStop    5    khihg
    ${trigger_handle}=    Trigger ADISS Event Record On
    Stop ADISS Event Record Off And Verify    ${trigger_handle}

ADISS RBM Buffering Finalization
    Enter ADISS Standby
    Get Number Of Ongoing Triggers

