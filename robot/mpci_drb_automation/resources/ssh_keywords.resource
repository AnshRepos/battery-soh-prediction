*** Settings ***
Documentation    Keywords for SSH connections

Library   rfw.lib.SshLibrary
Variables    ../configuration/test_bench.py


*** Keywords ***
Connect To ECU Over SSH
    [Documentation]    Connect to ECU using SSH
    SSH Connect   ${SSH_HOST}   ${SSH_USER}   ${SSH_PASSWORD}   ${SSH_TIMEOUT}

Disconnect SSH
    [Documentation]    Disconnect SSH connection
    SSH Disconnect
