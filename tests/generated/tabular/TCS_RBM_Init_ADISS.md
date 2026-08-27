Test Case Name: TCS_RBM_Init_ADISS

Pre-Conditions:
1. Power-up the ECU, Voltage=12V, KL30 is connected
2. Flash the Release SW using the flashing script
3. Check if PUTTY is available in Testbench; ensure SSH access to the ECU
4. ADISS process is running and able to call RBM APIs
5. Persistent storage mounts available for ADISS storage path
6. Callback handler in ADISS ready to receive RBM callbacks

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call RBM_GetVersion() via ADISS | Return Value = 0 (RBM_ok); Version string returned | Return Value = 0 (RBM_ok); Version string returned |
| 2 | ADISS registers callback via RBM_RegCallBack() | Return Value = 0 (RBM_ok) | Return Value = 0 (RBM_ok) |
| 3 | ADISS requests callback using RBM_ReqCbk() | Callback received: RBM_StorSize with storage size | Callback received: RBM_StorSize with storage size |
| 4 | Call RBM_GetState() via ADISS | Return Value = 0 (RBM_ok); RBM state = RBM_Init or RBM_Standby as applicable | Return Value = 0 (RBM_ok); RBM state = RBM_Init or RBM_Standby as applicable |
| 5 | Call RBM_CreateBufswContent(arg0) via ADISS | Return Value = 0 (RBM_ok); Buffer content created for arg0 | Return Value = 0 (RBM_ok); Buffer content created for arg0 |
| 6 | Call RBM_GetADISSPrmntStorgPth() via ADISS | Return Value = 0 (RBM_ok); Storage path returned | Return Value = 0 (RBM_ok); Storage path returned |
| 7 | Call RBM_EnterStandby() via ADISS | Return Value = 0 (RBM_ok); If time-sync valid → RBM enters Standby and callback RBM_StateChange(RBM_Standby) is observed; else RBM_NoTSync | Return Value = 0 (RBM_ok); Observed state-change or RBM_NoTSync |

Post-Condition:
1. Verify RBM is in RBM_Standby using RBM_GetState() or callback
2. Unregister ADISS callback and restore ADISS to pre-test state
3. Ensure storage handles/paths are closed

Source: examples/diagrams/rbm_init.puml
