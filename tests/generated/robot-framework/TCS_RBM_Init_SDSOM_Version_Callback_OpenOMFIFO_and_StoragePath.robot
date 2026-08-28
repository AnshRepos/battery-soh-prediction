*** Settings ***
Documentation    Generated from: examples/diagrams/rbm_init.puml
... Flow: SDSOM - Version/Callback/OpenOMFIFO/StoragePath
Library    OperatingSystem
Library    Process
Library    BuiltIn

*** Variables ***
${ECU_USER}    root
${ECU_HOST}    127.0.0.1

*** Test Cases ***
TCS_RBM_Init_SDSOM_Version_Callback_OpenOMFIFO_and_StoragePath
    [Documentation]    Verifies RBM interactions for SDSOM client: version, callback, get OM FIFO path, open FIFO, get storage path
    [Tags]    rbm_init    sdsom

    Log    Step 1: Get Version
    ${v} =    Run Process    echo    RBM_GetVersion    shell=True    stdout=PIPE
    Should Not Be Empty    ${v.stdout}

    Log    Step 2: Confirm RBM_ok
    ${ok} =    Run Process    echo    RBM_ok    shell=True    stdout=PIPE
    Should Contain    ${ok.stdout}    RBM_ok

    Log    Step 3: Request Callback StorSize
    ${cb} =    Run Process    echo    RBM_ReqCbk    shell=True    stdout=PIPE
    Should Contain    ${cb.stdout}    RBM_StorSize

    Log    Step 4: Verify State is RBM_Init
    ${s} =    Run Process    echo    RBM_GetState    shell=True    stdout=PIPE
    Should Contain    ${s.stdout}    RBM_Init

    Log    Step 5: Get OM FIFO Path and Open FIFO
    ${f} =    Run Process    echo    RBM_GetOMFIFOpath    shell=True    stdout=PIPE
    Should Not Be Empty    ${f.stdout}
    ${open} =    Run Process    echo    RBM_OpenOMFIFO    shell=True    stdout=PIPE
    Should Not Be Empty    ${open.stdout}

    Log    Step 6: Get OM Permanent Storage Path
    ${p} =    Run Process    echo    RBM_GetOMPrmntStorgPth    shell=True    stdout=PIPE
    Should Not Be Empty    ${p.stdout}
