# RQM sync pending — this test case has not yet been uploaded/linked to RQM.
# rqm_test_id: N/A
# rqm_url: N/A

*** Settings ***
Documentation     Test suite for TCS_RBM_Init_ADISS_Client.
...               Verifies the RBM (Ring Buffer Manager) initialization sequence invoked by the
...               ADISS client, including version/state queries, buffer content creation,
...               storage path retrieval, and the time-sync dependent transition into
...               RBM_Standby state (alt/else branch of RBM_EnterStandby).
...               Source: rbm_init.puml (Flow 1) | Architecture Baseline Version: v0.3.1
...               Platform Type: uP (QNX/Linux ECU)

Variables         ../../robot/mpci_drb_automation/configuration/test_bench.py

Resource          ../../robot/mpci_drb_automation/resources/pps_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/ssh_keywords.resource
Resource          ../../robot/mpci_drb_automation/resources/flashing_keywords.resource

Suite Setup       Run Keywords    Connect To PPS    AND    Flash Release SW And Verify Processes
Suite Teardown    Disconnect PPS

Test Setup        Run Keywords    Power Cycle ECU And Wait For Boot    AND    Connect To ECU Over SSH
Test Teardown     Disconnect SSH


*** Test Cases ***
TCS_RBM_Init_ADISS_Client_TimeSyncValid
    [Documentation]    Steps 1-7 (alt branch) + Step 9: RBM initialization sequence via ADISS
    ...                client, ending with RBM_EnterStandby(isTimeSyncValid=true) accepted and
    ...                the asynchronous RBM_StateChange->RBM_Standby callback verified.
    ...                Post-condition: RBM confirmed in RBM_Standby via RBM_GetState().
    [Tags]             RBM    ADISS    Init    Standby    uP    TimeSyncValid

    RBM GetVersion Via ADISS
    RBM Register Callback Via ADISS
    RBM Request Callback Via ADISS    RBM_StorSize
    RBM Get State Via ADISS    RBM_Init
    RBM Create Buffer Content Via ADISS
    RBM Get ADISS Persistent Storage Path
    RBM Enter Standby Via ADISS    ${TRUE}
    Verify RBM State Change Callback To Standby
    RBM Get State Via ADISS    RBM_Standby

TCS_RBM_Init_ADISS_Client_TimeSyncInvalid
    [Documentation]    Steps 1-6 + Step 8 (else branch): RBM initialization sequence via ADISS
    ...                client, ending with RBM_EnterStandby(isTimeSyncValid=false) rejected with
    ...                RBM_NoTSync, and RBM remaining in RBM_Init state (no transition occurs).
    [Tags]             RBM    ADISS    Init    Standby    uP    TimeSyncInvalid    NoTSync

    RBM GetVersion Via ADISS
    RBM Register Callback Via ADISS
    RBM Request Callback Via ADISS    RBM_StorSize
    RBM Get State Via ADISS    RBM_Init
    RBM Create Buffer Content Via ADISS
    RBM Get ADISS Persistent Storage Path
    RBM Enter Standby Via ADISS    ${FALSE}
    RBM Get State Via ADISS    RBM_Init


*** Keywords ***
Flash Release SW And Verify Processes
    [Documentation]    Pre-conditions 1-7: Flash the release SW and verify ADISS/RBM processes
    ...                and the RBM shared library are present before starting the sequence.
    Flash ECU Software
    ${ps_output}=    Execute Command    ps -e
    Should Contain    ${ps_output}    adiss
    Should Contain    ${ps_output}    rbm
    ${lib_output}=    Execute Command    ls /usr/lib | grep librbm_shared_lib.so
    Should Contain    ${lib_output}    librbm_shared_lib.so
    Log    ADISS process, RBM process, and RBM shared library verified present.

Power Cycle ECU And Wait For Boot
    # TODO: No dedicated "Power Cycle ECU And Wait For Boot" keyword was found in
    # robot/mpci_drb_automation/resources/pps_keywords.resource. Composed here from the
    # existing PPS keywords (Power Off ECU / Power On ECU) as a placeholder. Confirm/replace
    # with the actual boot-wait implementation used elsewhere (e.g. a boot-log/console check).
    [Documentation]    Power cycles the ECU and waits for it to boot before SSH connection.
    Power Off ECU
    Sleep    5s
    Power On ECU
    Sleep    10s

RBM GetVersion Via ADISS
    [Documentation]    Step 1: Call RBM_GetVersion() via ADISS. Verifies Return Value = 0
    ...                (RBM_ok) and that version info (major.minor.revision) is displayed.
    # TODO: Confirm actual ADISS client CLI/API invocation syntax for RBM_GetVersion.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_GetVersion    30
    Should Contain    ${output}    RBM_ok
    Log    ${output}

RBM Register Callback Via ADISS
    [Documentation]    Step 2: Call RBM_RegCallBack() via ADISS to register the callback
    ...                handler. Verifies Return Value = 0 (RBM_ok).
    # TODO: Confirm actual ADISS client CLI/API invocation syntax for RBM_RegCallBack.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_RegCallBack    30
    Should Contain    ${output}    RBM_ok

RBM Request Callback Via ADISS
    [Arguments]    ${reason}
    [Documentation]    Step 3: Call RBM_ReqCbk() via ADISS with the given reason (e.g.
    ...                RBM_StorSize) and verify the corresponding callback is received.
    # TODO: Confirm actual ADISS client CLI/API invocation syntax for RBM_ReqCbk.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_ReqCbk --reason ${reason}    30
    Should Contain    ${output}    ${reason}
    Log    ${output}

RBM Get State Via ADISS
    [Arguments]    ${expected_state}
    [Documentation]    Step 4 / Post-condition: Call RBM_GetState() via ADISS and verify
    ...                Return Value = 0 (RBM_ok) and RBMState matches ${expected_state}.
    # TODO: Confirm actual ADISS client CLI/API invocation syntax for RBM_GetState.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_GetState    30
    Should Contain    ${output}    RBM_ok
    Should Contain    ${output}    ${expected_state}
    Log    ${output}

RBM Create Buffer Content Via ADISS
    [Documentation]    Step 5: Call RBM_CreateBufswContent(arg0) via ADISS. Verifies Return
    ...                Value = 0 (RBM_ok) and that buffer software content is created.
    # TODO: Confirm actual argument value/name for arg0 and CLI/API invocation syntax.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_CreateBufswContent arg0    30
    Should Contain    ${output}    RBM_ok

RBM Get ADISS Persistent Storage Path
    [Documentation]    Step 6: Call RBM_GetADISSPrmntStorgPth() via ADISS. Verifies Return
    ...                Value = 0 (RBM_ok) and that a valid storage path (storgPth) is returned.
    # TODO: Confirm actual ADISS client CLI/API invocation syntax for RBM_GetADISSPrmntStorgPth.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_GetADISSPrmntStorgPth    30
    Should Not Be Empty    ${output}
    Log    ADISS Persistent Storage Path: ${output}

RBM Enter Standby Via ADISS
    [Arguments]    ${time_sync_valid}
    [Documentation]    Steps 7/8 (alt/else branch): Call RBM_EnterStandby() via ADISS with
    ...                the given isTimeSyncValid flag.
    ...                alt (True): expects Return Value = 0 (RBM_ok), transition accepted.
    ...                else (False): expects Return Value = RBM_NoTSync, transition rejected.
    # TODO: Confirm actual ADISS client CLI/API invocation syntax for RBM_EnterStandby.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_EnterStandby --isTimeSyncValid ${time_sync_valid}    30
    IF    ${time_sync_valid}
        Should Contain    ${output}    RBM_ok
    ELSE
        Should Contain    ${output}    RBM_NoTSync
    END
    Log    ${output}

Verify RBM State Change Callback To Standby
    [Documentation]    Step 9: Verify the asynchronous RBM state-change callback is received
    ...                with value RBM_StateChange = RBM_Standby, following a successful
    ...                RBM_EnterStandby(true) call.
    # TODO: Replace with the actual asynchronous callback verification mechanism
    # (e.g. DLT log search via dlt_keywords.resource, or a dedicated callback-stub check).
    # Placeholder implementation polls the ADISS client for the pending callback.
    ${output}=    Execute Command Return Message    /usr/bin/adiss_client RBM_PollCallback --wait 10    30
    Should Contain    ${output}    RBM_StateChange
    Should Contain    ${output}    RBM_Standby
    Log    ${output}
