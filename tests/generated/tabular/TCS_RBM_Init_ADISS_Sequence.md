Test Case Name: TCS_RBM_Init_ADISS_Sequence

Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench, make necessary SSH and serial connections
4. CANoe is loaded with correct *.cfg file
5. DLT Viewer is up and running for log verification
6. Verify ADISS process is running using 'ps -e' command
7. RBM API interface (librbm_shared_lib.so) is available at /usr/lib

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via ADISS | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) |
| 2 | Call RBM_RegisterCallback() via ADISS to register notification callback | Return Value = 0 (RBM_ok), Callback successfully registered with RBM | Return Value = 0 (RBM_ok), Callback successfully registered with RBM |
| 3 | Call RBM_ReqCbk() via ADISS with reason = RBM_StorSize (1) | Return Value = 0 (RBM_ok), callback received containing available storage size value for ADISS partition | Return Value = 0 (RBM_ok), callback received containing available storage size value for ADISS partition |
| 4 | Call RBM_GetState() via ADISS | Return Value = 0 (RBM_ok), RBMState = RBM_Init (state code = 0) | Return Value = 0 (RBM_ok), RBMState = RBM_Init (state code = 0) |
| 5 | Call RBM_CreateBufferSWContent() via ADISS | Return Value = 0 (RBM_ok), buffer software content created successfully | Return Value = 0 (RBM_ok), buffer software content created successfully |
| 6 | Call RBM_GetPermanentStoragePath() via ADISS for ADISS partition | Return Value = 0 (RBM_ok), retrieves correct permanent storage path | Return Value = 0 (RBM_ok), retrieves correct permanent storage path |
| 7 | Call RBM_EnterStandby() via ADISS with valid time synchronization (isTimeSyncValid is true) | Return Value = 0 (RBM_ok), RBM transitions towards Standby state | Return Value = 0 (RBM_ok), RBM transitions towards Standby state |
| 8 | Call RBM_EnterStandby() via ADISS with invalid time synchronization (isTimeSyncValid is false) | Return Value = RBM_NoTSync (value != 0), RBM rejects transition or handles state safely | Return Value = RBM_NoTSync (value != 0), RBM rejects transition or handles state safely |
| 9 | Verify state change callback is received by ADISS from RBM after successful EnterStandby request | Callback received: RBM_StateChange with value RBM_Standby (state code = 1) | Callback received: RBM_StateChange with value RBM_Standby (state code = 1) |

Post-Condition:
1. Verify RBM is in RBM_Standby state using RBM_GetState()
2. Close DLT Viewer
3. Close CANoe
4. Close SSH connection
5. Power down the ECU

Source: rbm_init.puml