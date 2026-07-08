*** Settings ***
Documentation    Keywords for CANoe communication and SSH connections

Variables    ../configuration/test_bench.py
Library           OperatingSystem
Library           rfw.lib.CanLinLibrary
Library           rfw.lib.SshLibrary
Resource    ssh_keywords.resource


*** Keywords ***
Initialize CANoe and SSH
    [Documentation]    Initialize CANoe configuration and establish SSH connection
    Connect To ECU Over SSH
    Log To Console    \n=========================================
    Log To Console    [INIT] Starting CANoe Initialization
    Log To Console    =========================================
    Log To Console    [INIT] Using config: ${ONE_RBS}
    ${normalized_cfg}=    Normalize Path    ${ONE_RBS}
    Log To Console    [INIT] Normalized CANoe cfg: ${normalized_cfg}
    Can Initialization    ${normalized_cfg}

Disconnect CANoe and SSH
    [Documentation]    Clean up CANoe and SSH connections
    Log To Console    [CLEANUP] Disconnecting CANoe
    Disconnect SSH
    Can Disconnect

Verify CAN Communication Is Alive
    [Documentation]    Verify that CAN communication is active
    Log To Console    -----------------------------------------
    Log To Console    [CHECK] Verifying CAN communication
    Log To Console    -----------------------------------------
    Verify CAN Alive    ${CHANNEL}    ${CAN_BAUDRATE}   yes   5
    Log To Console    [CHECK] CAN communication is alive\n

Set Inter Blade To SIM
    [Documentation]    Set Inter_blade_sim to SIM mode (value 1)
    Log To Console    [SIM] Setting Inter_blade_sim = 1 (SIM mode)
    Set Sysvar    hil_ctrl    Inter_blade_sim    1
    Sleep    1s
    Log To Console    [SIM] Inter blade set to SIM successfully

Send OPMM Power Blade Mode Request
    [Documentation]    Set OperatingModeRequest_PowerBlade to 1
    Log To Console    -----------------------------------------
    Log To Console    [CAN TX] Preparing OPMM Power Blade Mode Request
    Log To Console    -----------------------------------------

    Write Signal
    ...   OPMM_POWER
    ...   OperatingModeRequest_PowerBlade
    ...   1
    ...   17
    Log To Console    [CAN TX] Power Blade Mode request sent successfully\n

Verify OPMM DRB Mode Response
      [Documentation]    Verify OperatingModeResponse_DRBBlade
      Log To Console    -----------------------------------------
      Log To Console    [CAN RX] Waiting for DRB Mode Response
      Log To Console    -----------------------------------------
      Log To Console    Expected Value : 2
      Log To Console    Channel        : 17
      Validate Signal
      ...   OperatingMode_DRB
      ...   OperatingModeResponse_DRBBlade
      ...   2
      ...   17
      Log To Console    [CAN RX] DRB Mode response validated successfully\n

Verify Socket Communication
    [Documentation]    Verify RX/TX traffic via tcpdump on specified ports
    Log To Console    -----------------------------------------
    Log To Console    [SOCKET] Verifying RX/TX traffic via tcpdump
    Log To Console    -----------------------------------------

    Log To Console    [SOCKET] Checking RX on port 42811

    ${rx_output}=    Execute Command
    ...    tcpdump -xxvvv -i lo0 port 42811 | grep 8010
    ...    timeout=10s
    Should Contain    ${rx_output}    ff01 0100

    Log To Console    [SOCKET] RX traffic verified

    Log To Console    [SOCKET] Checking TX on port 42991
    ${tx_output}=    Execute Command
    ...    tcpdump -xxvvv -i lo0 port 42991 | grep 801d
    ...    timeout=10s
    Should Contain    ${tx_output}    0000 0202
    Log To Console    [SOCKET] TX traffic verified\n
