*** Settings ***
Documentation     Test Suite for validating ADIS DLT logs across power cycle.
...               This suite verifies:
...               1. DLT daemon availability
...               2. ECU behavior after power cycle
...               3. ADIS context visibility in DLT Viewer

Variables    ../configuration/test_bench.py
Resource    ../resources/pps_keywords.resource
Resource    ../resources/ssh_keywords.resource
Resource    ../resources/dlt_keywords.resource

Test Setup       Initialize DLT Configuration
Test Teardown    Cleanup Test Environment


*** Test Cases ***
DLT ADIS Verification
    [Documentation]    Verify ADIS context visibility in DLT logs after power cycle
    Verify DLT Daemon Is Running
    Power Cycle
    Initialize DLT Configuration
    Verify ADIS Context Is Visible In DLT
