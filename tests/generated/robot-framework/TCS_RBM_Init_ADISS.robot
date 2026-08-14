*** Settings ***
Documentation     Test case for RBM Init sequence with ADISS.
...               This test verifies the initialization sequence of the RBM
...               and the transition to standby state for the ADISS client.
Resource          ../../robot/mpci_drb_automation/resources/ssh_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/pps_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot    AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH

*** Test Cases ***
TCS_RBM_Init_ADISS
    [Documentation]    Verifies the RBM initialization sequence for ADISS.
    [Tags]    RBM    ADISS    Init    Standby

    RBM GetVersion
    RBM RegCallBack
    RBM ReqCbk
    RBM GetState
    RBM CreateBufswContent
    RBM GetADISSPrmntStorgPth
    RBM EnterStandby
    Verify RBM State Is Standby

*** Keywords ***
RBM GetVersion
    [Documentation]    Calls RBM_GetVersion
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetVersion
    Should Contain    ${output}    Version

RBM RegCallBack
    [Documentation]    Calls RBM_RegCallBack
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_RegCallBack
    Should Contain    ${output}    RBM_ok

RBM ReqCbk
    [Documentation]    Calls RBM_ReqCbk
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_ReqCbk
    Should Contain    ${output}    RBM_StorSize

RBM GetState
    [Documentation]    Calls RBM_GetState
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetState
    Should Contain    ${output}    RBM_Init

RBM CreateBufswContent
    [Documentation]    Calls RBM_CreateBufswContent
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_CreateBufswContent arg0
    Should Contain    ${output}    RBM_ok

RBM GetADISSPrmntStorgPth
    [Documentation]    Calls RBM_GetADISSPrmntStorgPth
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetADISSPrmntStorgPth
    Should Not Be Empty    ${output}

RBM EnterStandby
    [Documentation]    Calls RBM_EnterStandby and checks for RBM_ok or RBM_NoTSync
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_EnterStandby
    ${status}=    Run Keyword And Return Status    Should Contain    ${output}    RBM_ok
    Run Keyword Unless    ${status}    Should Contain    ${output}    RBM_NoTSync

Verify RBM State Is Standby
    [Documentation]    Verifies that the RBM state has transitioned to Standby.
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetState
    Should Contain    ${output}    RBM_Standby
