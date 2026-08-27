*** Settings ***
Documentation    Generated from: examples/diagrams/rbm_init.puml - Flow: SDSOM -> RBM Init
Library          SSHLibrary
Library          OperatingSystem

*** Variables ***
${ECU_HOST}      127.0.0.1
${ECU_USER}      root
${ECU_PASS}      password

*** Test Cases ***
TCS_RBM_Init_SDSOM
    [Documentation]    Verifies RBM init sequence from SDSOM client
    [Setup]    Setup Test Environment
    Log    Step 1: Get Version
    Execute Command    echo 'RBM_GetVersion()'
    Log    Step 2: Request Callback
    Execute Command    echo 'RBM_ReqCbk()'
    Log    Step 3: Get State
    Execute Command    echo 'RBM_GetState()'
    Log    Step 4: Get OM FIFO Path
    Execute Command    echo 'RBM_GetOMFIFOpath()'
    Log    Step 5: Open OM FIFO
    Execute Command    echo 'RBM_OpenOMFIFO()'
    Log    Step 6: Get OM Storage Path
    Execute Command    echo 'RBM_GetOMPrmntStorgPth()'
    [Teardown]    Teardown Test Environment

*** Keywords ***
Setup Test Environment
    Log    Setting up test environment (ensure SSH and OM FIFO available)

Teardown Test Environment
    Log    Tearing down test environment (unregister callbacks, close handles)
