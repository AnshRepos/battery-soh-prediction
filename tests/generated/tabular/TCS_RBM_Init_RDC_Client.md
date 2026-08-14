Test Case Name: TCS_RBM_Init_RDC_Client

Description: Verifies the RBM initialization sequence invoked by the RDC client, covering version/state queries, callback registration, and RDC-specific persistent storage path retrieval.

Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench, make necessary SSH and serial connections
4. Verify RDC process is running using 'ps -e' command
5. Verify RBM process is running using 'ps -e' command
6. RBM API interface (librbm_shared_lib.so) is available at /usr/lib
7. Confirm RBM is currently in RBM_Init state before starting sequence

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via RDC | Return Value = 0 (RBM_ok)<br>Version Info displayed (major.minor.revision format) | Return Value = 0 (RBM_ok)<br>Version Info displayed (major.minor.revision format) |
| 2 | Verify acknowledgement response after RBM_GetVersion() call | Return Value = 0 (RBM_ok) acknowledgement received | Return Value = 0 (RBM_ok) acknowledgement received |
| 3 | Call RBM_ReqCbk() via RDC with reason = RBM_StorSize | Callback received: RBM_StorSize containing available RDC storage size value | Callback received: RBM_StorSize containing available RDC storage size value |
| 4 | Call RBM_GetState() via RDC | Return Value = 0 (RBM_ok), RBMState = RBM_Init (state code = 0) | Return Value = 0 (RBM_ok), RBMState = RBM_Init (state code = 0) |
| 5 | Call RBM_GetRDCPrmntStorgPth() via RDC | Return Value = 0 (RBM_ok), storgPth returned pointing to valid RDC persistent storage location | Return Value = 0 (RBM_ok), storgPth returned pointing to valid RDC persistent storage location |

Post-Condition:
1. Verify RBM remains in RBM_Init state using RBM_GetState()
2. Power down the ECU
3. Close SSH connection

Source: rbm_init.puml (Flow 2)
Generated: 2026-08-13
Platform Type: uP
