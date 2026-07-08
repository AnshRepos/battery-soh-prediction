*** Settings ***
Documentation    Keywords for Power Supply (PPS) operations

Library   rfw.lib.PPSLibrary
Variables    ../configuration/test_bench.py


*** Keywords ***
Connect To PPS
    [Documentation]    Connect to Power Supply with specified parameters
    PPS Connect    ${PPS_ADDR}    ${PPS_BAUDRATE}    ${PPS_VENDOR}    5    ${INTERFACE_TYPE}
    Reload Library    rfw.lib.PPSLibrary
    Select Channel    1

Configure Power Supply
    [Documentation]    Configure voltage and current settings for power supply
    Set Voltage   ${PPS_VOLTAGE}
    Set Current   ${PPS_CURRENT}

Power On ECU
    [Documentation]    Turn on power output to ECU
    Output Status
    Output On
    Sleep    5s

Power Off ECU
    [Documentation]    Turn off power output to ECU
    Output Status
    Output Off

Disconnect PPS
    [Documentation]    Disconnect from Power Supply
    PPS Disconnect
