Test Case Name: TCS_RBM_Init_RDC
Architecture Baseline Version: v1.0.0
Source: c:\Users\NNR3COB\Documents\SWE - 5 IT Agent\Integration_Test_Agent\examples\diagrams\rbm_init.puml

Pre-Conditions:
1. ECU is powered on.
2. SSH connection is established.

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | RDC -> RBM: RBM_GetVersion | RBM returns the version information to RDC. | |
| 2 | RDC -> RBM: RBM_RegCallBack | RBM returns `RBM_ok`. | |
| 3 | RDC -> RBM: RBM_ReqCbk | RBM sends a callback with `RBM_StorSize`. | |
| 4 | RDC -> RBM: RBM_GetState | RBM returns its state as `RBM_Init`. | |
| 5 | RDC -> RBM: RBM_GetRDCPrmntStorgPth | RBM returns the storage path `storgPth`. | |

Post-Condition:
1. RDC has successfully initialized its interaction with RBM.
2. SSH connection is closed.
