*** Settings ***
Documentation    Keywords for ECU flashing operations

Library   rfw.lib.SshLibrary


*** Keywords ***
Flash ECU Software
    [Documentation]    Flash ECU with new software using rb_drb_flash.sh script
    Log To Console    ===== Starting ECU Flashing =====
    Execute Command    cd /scratch && pwd    /scratch
    Execute Command    chmod +x rb_drb_flash.sh && ls -l    rb_drb_flash.sh
    Execute Command    ./rb_drb_flash.sh f    Flash
    Log To Console    ===== Flash completed =====

Sync ECU Software
    [Documentation]    Synchronize ECU software using rb_drb_flash.sh script
    Log To Console    ===== Starting ECU SYNC =====
    Execute Command    cd /scratch && ./rb_drb_flash.sh s    Sync
    Log To Console    ===== ECU SYNC completed =====
