Test Case Name: TCS_RBM_Init_ADISS_Client

Description: Verifies the RBM (Ring Buffer Manager) initialization sequence invoked by the ADISS client, including version/state queries, buffer content creation, storage path retrieval, and the time-sync dependent transition into RBM_Standby state (alt/else branch).

Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench, make necessary SSH and serial connections
4. Verify ADISS process is running using 'ps -e' command
5. Verify RBM process is running using 'ps -e' command
6. RBM API interface (librbm_shared_lib.so) is available at /usr/lib
7. Confirm RBM is currently in RBM_Init state before starting sequence

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via ADISS | Return Value = 0 (RBM_ok)<br>Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok)<br>Version Info displayed (major.minor.revision format) |
| 2 | Call RBM_RegCallBack() via ADISS to register callback handler | Return Value = 0 (RBM_ok), callback successfully registered | Return Value = 0 (RBM_ok), callback successfully registered |
| 3 | Call RBM_ReqCbk() via ADISS with reason = RBM_StorSize | Callback received: RBM_StorSize containing available storage size value | Callback received: RBM_StorSize containing available storage size value |
| 4 | Call RBM_GetState() via ADISS | Return Value = 0 (RBM_ok), RBMState = RBM_Init (state code = 0) | Return Value = 0 (RBM_ok), RBMState = RBM_Init (state code = 0) |
| 5 | Call RBM_CreateBufswContent(arg0) via ADISS | Return Value = 0 (RBM_ok), buffer software content successfully created | Return Value = 0 (RBM_ok), buffer software content successfully created |
| 6 | Call RBM_GetADISSPrmntStorgPth() via ADISS | Return Value = 0 (RBM_ok), storgPth returned pointing to valid ADISS persistent storage location | Return Value = 0 (RBM_ok), storgPth returned pointing to valid ADISS persistent storage location |
| 7 | Call RBM_EnterStandby() via ADISS with isTimeSyncValid = true (alt branch) | Return Value = 0 (RBM_ok), RBM accepts transition request since time sync is valid | Return Value = 0 (RBM_ok), RBM accepts transition request since time sync is valid |
| 8 | Call RBM_EnterStandby() via ADISS with isTimeSyncValid = false (else branch) | Return Value = RBM_NoTSync, RBM rejects transition due to invalid/unavailable time sync | Return Value = RBM_NoTSync, RBM rejects transition due to invalid/unavailable time sync |
| 9 | Verify asynchronous RBM state change callback after successful RBM_EnterStandby (true branch) | Callback received: RBM_StateChange with value RBM_Standby | Callback received: RBM_StateChange with value RBM_Standby |

Post-Condition:
1. Verify RBM is in RBM_Standby state using RBM_GetState()
2. Power down the ECU
3. Close SSH connection

Source: rbm_init.puml (Flow 1)
Generated: 2026-08-13
Platform Type: uP
