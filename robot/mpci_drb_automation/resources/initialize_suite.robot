*** Settings ***
Documentation   Set Software Version Metadata
Library   String


*** Keywords ***
Initialize Suite
    [Documentation]    Initialize test suite with software version metadata
    ${SOFTWARE_VERSION}=    OperatingSystem.Get File
    ...    ./software_version.txt
    ${SOFTWARE_VERSION}=    Strip String    ${SOFTWARE_VERSION}
    Set Suite Variable      ${SOFTWARE_VERSION}
    Set Suite Metadata      Software Version    ${SOFTWARE_VERSION}
    Log To Console          Running on Software Version: ${SOFTWARE_VERSION}
