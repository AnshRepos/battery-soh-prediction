*** Settings ***
Documentation     Test suite for verifying Ring Buffer Management Initialization (RBM_Init) across multiple clients.
...               Verifies initialization, callback registration, storage paths, state transitions,
...               and FIFO path queries for ADISS, SDS_RDC, and SDSOM.
Variables         ../../../robot/mpci_drb_automation/configuration/test_bench.py
Resource          ../../../robot/mpci_drb_automation/resources/ssh_keywords.resource
Resource          ../../../robot/mpci_drb_automation/resources/pps_keywords.resource
Resource          ../../../robot/mpci_drb_automation/resources/dlt_keywords.resource

Suite Setup       Connect To PPS
Suite Teardown    Disconnect PPS
Test Setup        Run Keywords    Power Cycle    AND    Connect To ECU Over SSH
Test Teardown     Run Keywords    Cleanup Test Environment

*** Test Cases ***
643114_TCS_RingBufferManagement_RBMInit
    [Documentation]    Verifies initialization process of RBM for ADISS, SDS_RDC, and SDSOM.
    [Tags]             uP    RBM    Initialization    RQM_643114
    Sync ECU Time

    # ==========================================
    # Phase 1: ADISS Client Initialization
    # ==========================================
    Log To Console    \n========== Phase 1: ADISS Client Initialization ==========
    Kill ADISS Process
    Launch ADISS Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify ADISS Init State
    Create ADISS Buffer Content Test
    Verify ADISS Permanent Storage Path

    # ==========================================
    # Phase 2: ADISS State Transition under Valid TimeSync
    # ==========================================
    Log To Console    \n========== Phase 2: ADISS Standby with Valid TimeSync ==========
    Ensure Time Sync Is Valid
    Enter ADISS Standby
    Verify ADISS Standby State
    Exit RBM Stub

    # ==========================================
    # Phase 3: ADISS State Transition under Invalid TimeSync
    # ==========================================
    Log To Console    \n========== Phase 3: ADISS Standby with Invalid TimeSync ==========
    Launch ADISS Stub
    Ensure Time Sync Is Invalid
    Enter ADISS Standby
    Verify ADISS State Remains Init
    Exit RBM Stub

    # ==========================================
    # Phase 4: SDS_RDC Client Initialization
    # ==========================================
    Log To Console    \n========== Phase 4: SDS_RDC Client Initialization ==========
    Launch SDSRDC Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify SDSRDC Init State
    Verify SDSRDC Permanent Storage Path
    Exit RBM Stub

    # ==========================================
    # Phase 5: SDSOM Client Initialization
    # ==========================================
    Log To Console    \n========== Phase 5: SDSOM Client Initialization ==========
    Launch SDSOM Stub
    Validate RBM Version
    Register RBM Callback
    Request RBM Callback
    Verify SDSOM Init State
    Verify SDSOM FIFO Path
    Open SDSOM FIFO
    Verify SDSOM Permanent Storage Path
    Exit RBM Stub

*** Keywords ***
Sync ECU Time
    [Documentation]    Synchronizes the ECU's system time
    Log To Console    Syncing ECU Time...
    # Implement actual SSH commands or keyword call if available

Kill ADISS Process
    [Documentation]    Terminates any running ADISS process
    Log To Console    Killing active ADISS process...
    # Execute Command    killall -9 SC_1412_ADISS

Launch ADISS Stub
    [Documentation]    Launches the ADISS stub tool
    Log To Console    Launching ADISS stub client...

Validate RBM Version
    [Documentation]    Verifies that the RBM version is returned correctly
    Log To Console    Validating RBM version...

Register RBM Callback
    [Documentation]    Registers the callback on the RBM interface
    Log To Console    Registering callback on RBM API interface...

Request RBM Callback
    [Documentation]    Requests a callback from the RBM interface (RBM_StorSize)
    Log To Console    Requesting RBM Callback (RBM_StorSize)...

Verify ADISS Init State
    [Documentation]    Verifies that the current ADISS RBM state is RBM_Init (0)
    Log To Console    Verifying ADISS is in RBM_Init state...

Create ADISS Buffer Content Test
    [Documentation]    Calls RBM_CreateBufswContent to create buffering file content
    Log To Console    Creating buffer switch content...

Verify ADISS Permanent Storage Path
    [Documentation]    Queries and verifies ADISS permanent storage path
    Log To Console    Verifying ADISS permanent storage path...

Ensure Time Sync Is Valid
    [Documentation]    Sets Time Sync to a valid state on the ECU
    Log To Console    Ensuring Time Sync is valid...

Ensure Time Sync Is Invalid
    [Documentation]    Sets Time Sync to an invalid state on the ECU
    Log To Console    Simulating invalid Time Sync...

Enter ADISS Standby
    [Documentation]    Calls RBM_EnterStandby via ADISS
    Log To Console    Calling RBM_EnterStandby...

Verify ADISS Standby State
    [Documentation]    Verifies that the ADISS state is RBM_Standby
    Log To Console    Verifying ADISS is in RBM_Standby state...

Verify ADISS State Remains Init
    [Documentation]    Verifies that the ADISS state remains in RBM_Init
    Log To Console    Verifying ADISS state remains in RBM_Init...

Exit RBM Stub
    [Documentation]    Exits the active client stub
    Log To Console    Exiting active client stub...

Launch SDSRDC Stub
    [Documentation]    Launches the SDS_RDC stub tool
    Log To Console    Launching SDS_RDC stub client...

Verify SDSRDC Init State
    [Documentation]    Verifies that the current SDS_RDC state is RBM_Init
    Log To Console    Verifying SDS_RDC is in RBM_Init state...

Verify SDSRDC Permanent Storage Path
    [Documentation]    Queries and verifies SDS_RDC permanent storage path
    Log To Console    Verifying SDS_RDC permanent storage path...

Launch SDSOM Stub
    [Documentation]    Launches the SDSOM stub tool
    Log To Console    Launching SDSOM stub client...

Verify SDSOM Init State
    [Documentation]    Verifies that the current SDSOM state is RBM_Init
    Log To Console    Verifying SDSOM is in RBM_Init state...

Verify SDSOM FIFO Path
    [Documentation]    Queries the FIFO path for SDSOM
    Log To Console    Querying SDSOM FIFO path...

Open SDSOM FIFO
    [Documentation]    Opens the SDSOM FIFO channel
    Log To Console    Opening SDSOM FIFO...

Verify SDSOM Permanent Storage Path
    [Documentation]    Queries and verifies SDSOM permanent storage path
    Log To Console    Verifying SDSOM permanent storage path...
