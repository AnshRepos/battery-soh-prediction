# TCS_RingBufferManagement_RBMInit

## Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench, make necessary SSH and serial connections
4. Verify ADISS, SDS_RDC, and SDSOM processes are running using 'ps -e' command
5. RBM API interface (librbm_shared_lib.so) is available at /usr/lib
6. DLT Viewer is up and running for log verification

## Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via ADISS client | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) |
| 2 | Call RBM_RegCallBack() via ADISS client | Return Value = 0 (RBM_ok), Callback function registered successfully | Return Value = 0 (RBM_ok), Callback function registered successfully |
| 3 | Call RBM_ReqCbk() via ADISS client with reason = RBM_StorSize | Callback received with RBM_StorSize containing available storage size value | Callback received with RBM_StorSize containing available storage size value |
| 4 | Call RBM_GetState() via ADISS client | Return Value = 0 (RBM_ok), RBMState = RBM_Init | Return Value = 0 (RBM_ok), RBMState = RBM_Init |
| 5 | Call RBM_CreateBufswContent(arg0) via ADISS client | Return Value = 0 (RBM_ok), Buffer switch content created successfully | Return Value = 0 (RBM_ok), Buffer switch content created successfully |
| 6 | Call RBM_GetADISSPrmntStorgPth() via ADISS client | Return Value = 0 (RBM_ok), ADISS permanent storage path returned (storgPth) | Return Value = 0 (RBM_ok), ADISS permanent storage path returned (storgPth) |
| 7 | Set system time synchronization as Valid<br>Call RBM_EnterStandby() via ADISS client | Return Value = 0 (RBM_ok), RBM successfully transitions from RBM_Init to RBM_Standby state | Return Value = 0 (RBM_ok), RBM successfully transitions from RBM_Init to RBM_Standby state |
| 8 | Verify asynchronous RBM state change callback after successful EnterStandby | Callback received: RBM_StateChange with value RBM_Standby | Callback received: RBM_StateChange with value RBM_Standby |
| 9 | Set system time synchronization as Invalid<br>Call RBM_EnterStandby() via ADISS client | Return Value = -1 (RBM_NoTSync), State transition fails and RBM stays in RBM_Init | Return Value = -1 (RBM_NoTSync), State transition fails and RBM stays in RBM_Init |
| 10 | Call RBM_GetVersion() via SDS_RDC client | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) |
| 11 | Call RBM_ReqCbk() via SDS_RDC client with reason = RBM_StorSize | Callback received with RBM_StorSize containing available storage size value | Callback received with RBM_StorSize containing available storage size value |
| 12 | Call RBM_GetState() via SDS_RDC client | Return Value = 0 (RBM_ok), RBMState = RBM_Init | Return Value = 0 (RBM_ok), RBMState = RBM_Init |
| 13 | Call RBM_GetRDCPrmntStorgPth() via SDS_RDC client | Return Value = 0 (RBM_ok), RDC permanent storage path returned (storgPth) | Return Value = 0 (RBM_ok), RDC permanent storage path returned (storgPth) |
| 14 | Call RBM_GetVersion() via SDSOM client | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok), Version Info displayed (major.minor.revision format) |
| 15 | Call RBM_ReqCbk() via SDSOM client with reason = RBM_StorSize | Callback received with RBM_StorSize containing available storage size value | Callback received with RBM_StorSize containing available storage size value |
| 16 | Call RBM_GetState() via SDSOM client | Return Value = 0 (RBM_ok), RBMState = RBM_Init | Return Value = 0 (RBM_ok), RBMState = RBM_Init |
| 17 | Call RBM_GetOMFIFOpath() via SDSOM client | Return Value = 0 (RBM_ok), OM FIFO path returned (fifopath) | Return Value = 0 (RBM_ok), OM FIFO path returned (fifopath) |
| 18 | Call RBM_OpenOMFIFO() via SDSOM client | Return Value = 0 (RBM_ok), OM FIFO opened successfully | Return Value = 0 (RBM_ok), OM FIFO opened successfully |
| 19 | Call RBM_GetOMPrmntStorgPth() via SDSOM client | Return Value = 0 (RBM_ok), OM permanent storage path returned (storgPth) | Return Value = 0 (RBM_ok), OM permanent storage path returned (storgPth) |

## Post-Condition:
1. Close DLT Viewer
2. Close SSH and serial connections
3. Power down the ECU
