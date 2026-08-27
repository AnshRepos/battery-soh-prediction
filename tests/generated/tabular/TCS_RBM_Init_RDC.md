Test Case Name: TCS_RBM_Init_RDC

Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench; ensure SSH access to the ECU
4. RDC (SDS_RDC) process is running and able to call RBM APIs
5. Persistent storage mounts available for RDC storage path
6. Callback handler in RDC ready to receive RBM callbacks

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via RDC | Return Value = 0 (RBM_ok); Version string returned | Return Value = 0 (RBM_ok); Version string returned |
| 2 | Call RBM_ReqCbk() via RDC | Callback received: RBM_StorSize with storage size | Callback received: RBM_StorSize with storage size |
| 3 | Call RBM_GetState() via RDC | Return Value = 0 (RBM_ok); RBM state = RBM_Init or RBM_Standby | Return Value = 0 (RBM_ok); RBM state = RBM_Init or RBM_Standby |
| 4 | Call RBM_GetRDCPrmntStorgPth() via RDC | Return Value = 0 (RBM_ok); Storage path returned | Return Value = 0 (RBM_ok); Storage path returned |

Post-Condition:
1. Verify RBM is in expected state
2. Unregister RDC callbacks and restore RDC to pre-test state
3. Ensure storage handles/paths are closed

Source: examples/diagrams/rbm_init.puml
