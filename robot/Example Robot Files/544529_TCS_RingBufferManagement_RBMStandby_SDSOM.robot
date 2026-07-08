
*** Settings ***
Documentation     Test suite for verifying SDSOM RBM Standby transitions. Ensures correct state handling and event recording.
Variables         ../configuration/test_bench.py
Resource          ../resources/ssh_keywords.resource
Resource          ../resources/rbm_keywords.resource
Resource          ../resources/pps_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot    AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH

*** Test Cases ***
544529_TCS_RingBufferManagement_RBMStandby_SDSOM
    [Documentation]    Test standby transitions for SDSOM RBM, including state verification.
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
    Exit RBM Stub
    Launch SDSOM Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify SDSOM Standby State
