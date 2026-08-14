Test Case Name: TCS_RingBufferManagement_RBMInit_ADISS

Description: Verify the initialization and standby entry of the ADISS client with the Ring Buffer Management (RBM) component.

Pre-Conditions:
1. Power Supply (PPS) is connected and set to 12V.
2. ECU is power cycled and boot is complete.
3. SSH connection to ECU is established.
4. ADISS process is killed to ensure a clean state.
5. ADISS stub is launched.

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call `RBM_GetVersion` API from ADISS | RBM returns Version Info successfully | RBM returns Version Info successfully |
| 2 | Call `RBM_RegCallBack` API to register callback handler | RBM registers callback and returns `RBM_ok` | RBM registers callback and returns `RBM_ok` |
| 3 | Call `RBM_ReqCbk` API from ADISS | RBM triggers callback for `RBM_StorSize` | RBM triggers callback for `RBM_StorSize` |
| 4 | Call `RBM_GetState` to retrieve current state | RBM returns state `RBM_Init` | RBM returns state `RBM_Init` |
| 5 | Call `RBM_CreateBufswContent(arg0)` API | RBM returns `RBM_ok` | RBM returns `RBM_ok` |
| 6 | Call `RBM_GetADISSPrmntStorgPth` to query storage path | RBM returns valid storage path (`storgPth`) | RBM returns valid storage path (`storgPth`) |
| 7 | Call `RBM_EnterStandby` from ADISS | If time sync is valid, RBM returns `RBM_ok`. Otherwise, RBM returns `RBM_NoTSync`. | If time sync is valid, RBM returns `RBM_ok`. Otherwise, RBM returns `RBM_NoTSync`. |
| 8 | Monitor callback event notifications from RBM | RBM triggers callback event indicating `RBM_StateChange` to `RBM_Standby` | RBM triggers callback event indicating `RBM_StateChange` to `RBM_Standby` |

Post-Condition:
1. Disconnect SSH from ECU.
2. Disconnect PPS power supply.

Source: examples/diagrams/rbm_init.puml
Generated: Tuesday, August 11, 2026
Platform Type: uP (Microprocessor)