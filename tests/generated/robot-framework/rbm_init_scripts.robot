*** Settings ***
Documentation    Test suite for RBM Init functionality.
...              Generated from rbm_init.puml.
Resource         ../../robot/mpci_drb_automation/resources/ssh_keywords.resource
Resource         ../../robot/mpci_drb_automation/resources/pps_keywords.resource

*** Variables ***
${RBM_VERSION_STRING}    UNKNOWN

*** Test Cases ***
ADISS Success Path
    [Documentation]    Test the successful standby entry for ADISS.
    [Tags]    ADISS    Success
    Suite Setup
    Connect via SSH
    ${version}=    Validate RBM Version
    Set Suite Variable    ${RBM_VERSION_STRING}    ${version}
    Enter ADISS Standby And Verify OK
    Disconnect SSH

ADISS Failure Path
    [Documentation]    Test the failed standby entry for ADISS.
    [Tags]    ADISS    Failure
    Suite Setup
    Connect via SSH
    ${version}=    Validate RBM Version
    Set Suite Variable    ${RBM_VERSION_STRING}    ${version}
    Enter ADISS Standby And Verify NOK
    Disconnect SSH

RDC Path
    [Documentation]    Test the RDC get version.
    [Tags]    RDC
    Suite Setup
    Connect via SSH
    ${version}=    Validate RBM Version
    Set Suite Variable    ${RBM_VERSION_STRING}    ${version}
    Disconnect SSH

SDSOM Path
    [Documentation]    Test the SDSOM get version.
    [Tags]    SDSOM
    Suite Setup
    Connect via SSH
    ${version}=    Validate RBM Version
    Set Suite Variable    ${RBM_VERSION_STRING}    ${version}
    Disconnect SSH

*** Keywords ***
Suite Setup
    [Documentation]    Setup for the uP-aurix platform.
    Power On PPS
    Wait Until    60    1    Is SSH Port Open

Validate RBM Version
    [Documentation]    Calls RBM_GetVersion and validates the output.
    [Tags]    RBM
    ${output}=    Execute Command Return Message    ./stub_rbm get_version
    Should Not Be Empty    ${output}
    [Return]    ${output}

Enter ADISS Standby And Verify OK
    [Documentation]    Calls RBM_EnterStandby for ADISS and expects OK.
    ...    TODO: Final implementation of this keyword is needed.
    [Tags]    RBM    ADISS
    ${output}=    Execute Command Return Message    ./stub_adiss enter_standby
    Should Be Equal As Strings    ${output}    RBM_OK

Enter ADISS Standby And Verify NOK
    [Documentation]    Calls RBM_EnterStandby for ADISS and expects NOK.
    ...    TODO: Final implementation of this keyword is needed.
    [Tags]    RBM    ADISS
    ${output}=    Execute Command Return Message    ./stub_adiss enter_standby --fail
    Should Be Equal As Strings    ${output}    RBM_NOK
