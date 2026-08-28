*** Settings ***
Documentation    Generated from: examples/diagrams/rbm_init.puml
... Flow: ADISS - RegisterCallback/CreateBuffer/EnterStandby
Library    OperatingSystem
Library    Process
Library    BuiltIn

*** Variables ***
${ECU_USER}    root
${ECU_HOST}    127.0.0.1

*** Test Cases ***
TCS_RBM_Init_ADISS_RegisterCallback_CreateBuffer_EnterStandby
    [Documentation]    Verifies RBM init sequence for ADISS client: version, register callback, request storage size callback, create buffer content, get storage path, enter standby (time sync variants)
    [Tags]    rbm_init    adiss

    # Pre-Conditions
    Log    Ensure RBM service and ADISS client are running and storage is writable

    # Steps
    Log    Step 1: Get Version
    ${rc} =    Run Process    echo    RBM_GetVersion    shell=True    stdout=PIPE
    Should Not Be Empty    ${rc.stdout}

    Log    Step 2: Register Callback
    ${rc2} =    Run Process    echo    RBM_RegCallBack    shell=True    stdout=PIPE
    Should Contain    ${rc2.stdout}    RBM_ok

    Log    Step 3: Request Callback (StorSize)
    ${rc3} =    Run Process    echo    RBM_ReqCbk    shell=True    stdout=PIPE
    Should Contain    ${rc3.stdout}    RBM_StorSize

    Log    Step 4: Get State and Create Buffer Content
    ${state} =    Run Process    echo    RBM_GetState    shell=True    stdout=PIPE
    Should Contain    ${state.stdout}    RBM_Init
    ${cb} =    Run Process    echo    RBM_CreateBufswContent arg0    shell=True    stdout=PIPE
    Should Contain    ${cb.stdout}    RBM_ok

    Log    Step 5: Get Storage Path and Enter Standby
    ${path} =    Run Process    echo    RBM_GetADISSPrmntStorgPth    shell=True    stdout=PIPE
    Should Not Be Empty    ${path.stdout}
    ${enter} =    Run Process    echo    RBM_EnterStandby    shell=True    stdout=PIPE
    Should Match Regexp    ${enter.stdout}    RBM_ok|RBM_NoTSync

*** Keywords ***
# Placeholder keywords; replace with real connectors for RBM interface
