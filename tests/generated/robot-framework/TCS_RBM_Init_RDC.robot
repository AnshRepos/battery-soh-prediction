*** Settings ***
Documentation     Test case for RBM Init sequence with RDC.
...               This test verifies the initialization sequence of the RBM
...               for the RDC client.
Resource          ../../robot/mpci_drb_automation/resources/ssh_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/pps_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot    AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH

*** Test Cases ***
TCS_RBM_Init_RDC
    [Documentation]    Verifies the RBM initialization sequence for RDC.
    [Tags]    RBM    RDC    Init

    RBM GetVersion
    RBM RegCallBack
    RBM ReqCbk
    RBM GetState
    RBM GetRDCPrmntStorgPth

*** Keywords ***
RBM GetVersion
    [Documentation]    Calls RBM_GetVersion
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetVersion --client RDC
    Should Contain    ${output}    Version

RBM RegCallBack
    [Documentation]    Calls RBM_RegCallBack
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_RegCallBack --client RDC
    Should Contain    ${output}    RBM_ok

RBM ReqCbk
    [Documentation]    Calls RBM_ReqCbk
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_ReqCbk --client RDC
    Should Contain    ${output}    RBM_StorSize

RBM GetState
    [Documentation]    Calls RBM_GetState
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetState --client RDC
    Should Contain    ${output}    RBM_Init

RBM GetRDCPrmntStorgPth
    [Documentation]    Calls RBM_GetRDCPrmntStorgPth
    ${output}=    Execute Command    /usr/bin/rbm_client RBM_GetRDCPrmntStorgPth
    Should Not Be Empty    ${output}
