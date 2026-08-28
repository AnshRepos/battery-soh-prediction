*** Settings ***
Documentation    Generated from: examples/diagrams/rbm_init.puml
... Flow: RDC - Version/Callback/State/StoragePath
Library    OperatingSystem
Library    Process
Library    BuiltIn

*** Variables ***
${ECU_USER}    root
${ECU_HOST}    127.0.0.1

*** Test Cases ***
TCS_RBM_Init_RDC_Verify_Version_Callback_State_and_StoragePath
    [Documentation]    Verifies RBM interactions for RDC client: version, callback, state, permanent storage path
    [Tags]    rbm_init    rdc

    Log    Step 1: Get Version from RBM
    ${v} =    Run Process    echo    RBM_GetVersion    shell=True    stdout=PIPE
    Should Not Be Empty    ${v.stdout}

    Log    Step 2: Confirm RBM_ok response
    ${ok} =    Run Process    echo    RBM_ok    shell=True    stdout=PIPE
    Should Contain    ${ok.stdout}    RBM_ok

    Log    Step 3: Request Callback StorSize
    ${cb} =    Run Process    echo    RBM_ReqCbk    shell=True    stdout=PIPE
    Should Contain    ${cb.stdout}    RBM_StorSize

    Log    Step 4: Verify State is RBM_Init
    ${s} =    Run Process    echo    RBM_GetState    shell=True    stdout=PIPE
    Should Contain    ${s.stdout}    RBM_Init

    Log    Step 5: Get Permanent Storage Path
    ${p} =    Run Process    echo    RBM_GetRDCPrmntStorgPth    shell=True    stdout=PIPE
    Should Not Be Empty    ${p.stdout}
