*** Settings ***
Documentation    Keywords for DLT (Diagnostic Log and Trace) functionality
Variables    ../configuration/test_bench.py
Resource    ssh_keywords.resource
Resource    pps_keywords.resource
Library           OperatingSystem
Library           rfw.lib.DLTLibrary
Library           rfw.lib.SshLibrary


*** Keywords ***
Initialize DLT Configuration
  [Documentation]    Initialize DLT configuration and connect to ECU
  Log To Console    \n========== [INIT] Initializing DLT Configuration ==========

  Log To Console    [INIT] Connecting to ECU via SSH...
  Connect To ECU Over SSH
  Log To Console    [OK] SSH connection established

  Log To Console    [INIT] Connecting to Power Supply...
  Connect To PPS
  Log To Console    [OK] PPS connection established

  Log To Console    [INIT] Configuring Power Supply...
  Configure Power Supply
  Log To Console    [OK] Power Supply configured

  Log To Console    [INIT] Starting DLT Logging...
  Start DLT Logging   ${DLT_FILE}   ${DLT_IP}

  Log To Console    [INIT] Launching DLT Connector (Mode=${DLT_MODE})...
  Launch Dlt Connector     ${ECU}     ${DLT_MODE}     C:/Users/WPW2KOR/Desktop/trace.dlt   NONE   COM3    115200     ${DLT_IP}    3490

  Connect
  Start Monitoring

  Log To Console    [OK] DLT monitoring started successfully
  Log To Console    ========================================================

Cleanup Test Environment
  [Documentation]    Clean up test environment and release resources
  Log To Console    \n========== [CLEANUP] Releasing Test Resources ==========

  Disconnect PPS

  Log To Console    [CLEANUP] Disconnecting DLT...
  Disconnect

  Log To Console    [CLEANUP] Stopping DLT logging...
  Stop DLT Logging

  Log To Console    [CLEANUP] Closing SSH connection...
  Disconnect SSH

  Log To Console    [OK] Cleanup completed
  Log To Console    ========================================================

Power Cycle
  [Documentation]    Perform power cycle of ECU using PPS
  Log To Console    \n========== [POWER] Starting ECU Power Cycle ==========

  Log To Console    [POWER] Disconnecting DLT before power cut...
  Disconnect

  Log To Console    [POWER] Disconnecting PPS session...
  Disconnect PPS

  Log To Console    [POWER] Reconnecting to PPS...
  Connect To PPS

  Log To Console    [POWER] Turning ECU OFF...
  Power Off ECU
  Log To Console    [WAIT] Waiting 5 seconds for full discharge...
  Sleep     3s

  Log To Console    [POWER] Turning ECU ON...
  Power On ECU
  Log To Console    [WAIT] Waiting for ECU boot (3 seconds)...
  Sleep     3s

  Log To Console    [POWER] Disconnecting PPS session...
  Disconnect PPS

  Log To Console    [OK] Power Cycle completed
  Log To Console    ========================================================

Verify DLT Daemon Is Running
  [Documentation]    Verify that DLT daemon is running on the target
  Log To Console    \n[VERIFY] Checking if DLT daemon (rb-dltd) is running...
  Execute Command    pidin | grep -i dlt    rb-dltd
  Log To Console    [OK] DLT daemon is running

Verify ADIS Context Is Visible In DLT
  [Documentation]    Verify ADIS context is registered and visible in DLT logs

  Log To Console    \n[VERIFY] Waiting for ADIS context in DLT logs...
  Log To Console    [INFO] Searching for CTID: ${DLT_CTID}

  Search Logs    ${DLT_CTID}    ${DLT_TIMEOUT}
  Log To Console    [OK] ADIS context detected

  Log To Console    [VERIFY] Checking for INFO level logs from ADIS...
  Search Logs    ${DLT_CTID}.*INFO    ${DLT_TIMEOUT}
  Log To Console    [OK] ADIS INFO logs detected
