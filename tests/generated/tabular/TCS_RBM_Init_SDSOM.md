Test Case Name: TCS_RBM_Init_SDSOM

Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench; ensure SSH access to the ECU
4. SDSOM process is running and able to call RBM APIs
5. Persistent storage mounts available for SDSOM storage path and OM FIFO
6. Callback handler in SDSOM ready to receive RBM callbacks

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via SDSOM | Return Value = 0 (RBM_ok); Version string returned | Return Value = 0 (RBM_ok); Version string returned |
| 2 | Call RBM_ReqCbk() via SDSOM | Callback received: RBM_StorSize with storage size | Callback received: RBM_StorSize with storage size |
| 3 | Call RBM_GetState() via SDSOM | Return Value = 0 (RBM_ok); RBM state = RBM_Init or RBM_Standby | Return Value = 0 (RBM_ok); RBM state = RBM_Init or RBM_Standby |
| 4 | Call RBM_GetOMFIFOpath() via SDSOM | Return Value = 0 (RBM_ok); OM FIFO path returned | Return Value = 0 (RBM_ok); OM FIFO path returned |
| 5 | Call RBM_OpenOMFIFO() via SDSOM using returned path | Return Value = 0 (RBM_ok); FIFO opened and handle returned | Return Value = 0 (RBM_ok); FIFO opened and handle returned |
| 6 | Call RBM_GetOMPrmntStorgPth() via SDSOM | Return Value = 0 (RBM_ok); Storage path returned | Return Value = 0 (RBM_ok); Storage path returned |

Post-Condition:
1. Close OM FIFO handles and release resources
2. Unregister SDSOM callbacks and restore SDSOM to pre-test state
3. Ensure storage handles/paths are closed

Source: examples/diagrams/rbm_init.puml
