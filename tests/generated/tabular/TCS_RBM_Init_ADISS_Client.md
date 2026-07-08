# Test Case: TCS_RBM_Init_ADISS_Client

**Platform Type**: uP (Microprocessor)  
**Source Diagram**: rbm_init.puml  
**Generated**: 2026-07-07  
**Architecture Baseline Version**: v0.3.1

---

## Pre-Conditions

1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench, make necessary SSH and serial connections
4. TRACE32 is up and running
5. Verify ADISS process is running using 'ps -e' command
6. RBM API interface (librbm_shared_lib.so) is available at /usr/lib

---

## Test Case Design

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via ADISS | Return Value = 0 (RBM_ok)<br>Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok)<br>Version Info displayed (major.minor.revision format) |
| 2 | Call RBM_RegCallBack() via ADISS to register callback function | Return Value = 0 (RBM_ok)<br>Callback registration successful | Return Value = 0 (RBM_ok)<br>Callback registration successful |
| 3 | Call RBM_ReqCbk() via ADISS with reason = RBM_StorSize | Callback received with RBM_StorSize containing available storage size value | Callback received with RBM_StorSize containing available storage size value |
| 4 | Call RBM_GetState() via ADISS | Return Value = 0 (RBM_ok)<br>RBMState = RBM_Init (state code = 0) | Return Value = 0 (RBM_ok)<br>RBMState = RBM_Init (state code = 0) |
| 5 | Call RBM_CreateBufswContent(arg0) via ADISS | Return Value = 0 (RBM_ok)<br>Buffer content created successfully | Return Value = 0 (RBM_ok)<br>Buffer content created successfully |
| 6 | Call RBM_GetADISSPrmntStorgPth() via ADISS | Return Value = 0 (RBM_ok)<br>storgPth returned with valid ADISS partition path | Return Value = 0 (RBM_ok)<br>storgPth returned with valid ADISS partition path |
| 7 | Call RBM_EnterStandby() via ADISS | If isTimeSyncValid=true: Return Value = 0 (RBM_ok)<br>If isTimeSyncValid=false: Return Value = RBM_NoTSync | If isTimeSyncValid=true: Return Value = 0 (RBM_ok)<br>If isTimeSyncValid=false: Return Value = RBM_NoTSync |
| 8 | Verify asynchronous callback received after EnterStandby | Callback received: RBM_StateChange with value RBM_Standby (state code = 1) | Callback received: RBM_StateChange with value RBM_Standby (state code = 1) |

---

## Post-Condition

1. Verify RBM is in RBM_Standby state using RBM_GetState()
2. Power down the ECU
3. Close SSH connection
