*** Settings ***
Documentation   Verify LUM Stub update flow using system logs
Resource     ../resources/pps_keywords.resource
Resource     ../resources/ssh_keywords.resource
Variables    ../configuration/test_bench.py
Library   String
Library   rfw.lib.SshLibrary


*** Keywords ***
Configure SSH and PPS
    [Documentation]    Configure SSH connection and Power Supply for testing
    Log To Console    ========================================
    Log To Console    Initializing Test Bench Setup
    Log To Console    ========================================

    Log To Console    Connecting to Power Supply...
    Connect To PPS
    Configure Power Supply
    Power On ECU
    Sleep  5s

    Log To Console    Connecting to ECU over SSH...
    Connect To ECU Over SSH
    Wait For ECU Fully Ready
    Log To Console    Setup Completed Successfully
    Log To Console    ========================================

Post Conditions
    [Documentation]    Clean up test environment and disconnect resources
    Log To Console    ========================================
    Log To Console    Starting Cleanup
    Log To Console    ========================================

    Log To Console    Disconnecting SSH...
    Disconnect SSH

    Log To Console    Powering Off ECU...
    Power Off ECU

    Log To Console    Disconnecting Power Supply...
    Disconnect PPS

    Log To Console    Cleanup Completed
    Log To Console    ========================================

Wait For ECU Fully Ready
    [Documentation]    Wait until ECU is fully ready for operations
    Log To Console    Waiting for ECU to be fully ready...
    Wait Until Keyword Succeeds    1 min    5 sec    Check ECU Ready
    Log To Console    ECU is fully ready.

Check ECU Ready
    [Documentation]    Check if ECU is ready by verifying scp availability
    ${out}=    Execute Command Return Message    which scp    10
    Should Not Be Empty    ${out}

Upload LUM Package To ECU
    [Documentation]    Transfer tgz_c file to ECU scratch folder
    Log To Console    ========================================
    Log To Console    Uploading LUM Package
    Log To Console    Source: ${LOCAL_TGZ}
    Log To Console    Destination: ${REMOTE_DIR}
    Log To Console    ========================================
    Push File    ${LOCAL_TGZ}    ${REMOTE_DIR}    ${PERMISSIONS}
    Log To Console    Upload Completed Successfully

Move LUM Flash Script
    [Documentation]    Move lum_flash_main.sh from /etc to /scratch and make it executable

    Log To Console    Moving lum_flash_main.sh to /scratch
    Execute Command Return Message    mv /etc/lum_flash_main.sh /scratch/    30

    Log To Console    Making script executable
    Execute Command Return Message    chmod +x /scratch/lum_flash_main.sh     30

    Log To Console    Flash script prepared

Verify LUM Flash Script
    [Documentation]    Verify that LUM flash script exists and is properly set up
    Log To Console    Verifying flash script in /scratch...
    ${output}=    Execute Command Return Message    ls -l /scratch/    30
    Should Contain    ${output}    lum_flash_main.sh
    Log To Console    Flash script verification successful

Run LUM Stub App
    [Documentation]   Dumps logs to a temporary file

    Log To Console    ========================================
    Log To Console    Running LUM Stub Application
    Log To Console    Path: ${LUM_APP_PATH}
    Log To Console    Command: ${LUM_CMD}
    Log To Console    ========================================
    ${output}=    Execute Command Return Message    cd ${LUM_APP_PATH} && ${LUM_CMD}    720

    Log To Console    LUM Stub Application Execution Finished
    Log    ${output}

Dump And Check API Logs
    [Documentation]    Dump system logs and verify LUM API calls
    Log To Console    Dumping slog logs to /tmp/slog.txt
    Execute Command Return Message    slog2info > /tmp/slog.txt    30

    Log To Console    Searching for getSlots API logs...
    ${output}=      Execute Command Return Message    grep getSlots /tmp/slog.txt   30
    Log    ${output}
    Should Contain    ${output}    rbLumStubApp
    Should Contain    ${output}    100
    Should Contain    ${output}    rbLumBswClientAdaptor_Pmgr_DRB_Bl::getSlots()
    Log To Console    API Log Verification Successful
