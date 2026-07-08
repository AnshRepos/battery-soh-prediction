
*** Settings ***
Documentation     Test suite for verifying OM RBM Buffering transitions. Ensures correct state handling and event recording.
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
544649_TCS_RingBufferManagement_RBMBuffering_OM
    [Documentation]    Test buffering transitions for OM RBM, including event recording and state verification.
    OM_RBM_Buffering_Preparation
    OM_RBM_Buffering_Event_Recording
    OM_RBM_Buffering_Finalization

*** Keywords ***
OM_RBM_Buffering_Preparation
    [Documentation]    Prepare OM RBM for buffering state.
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
    Kill SDSOM Process
    Launch SDSOM Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Get SDSOM OM FIFO Path
    Open SDSOM OM FIFO

OM RBM Buffering Event Recording
    ${trigger_handle}=    Trigger SDSOM OM Event Record
    Get Number Of Ongoing Triggers
    Stop SDSOM OM Event Record And Verify    ${trigger_handle}
    ${trigger_handle}=    Trigger SDSOM OM Event Record On
    Stop SDSOM OM Event Record And Verify    ${trigger_handle}
    ${trigger_handle}=    Trigger SDSOM OM Event Record On
    Stop SDSOM OM Event Record Off And Verify    ${trigger_handle}

OM RBM Buffering Finalization
    Verify Number Of Ongoing Triggers    3