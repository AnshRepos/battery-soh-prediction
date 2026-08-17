Test Case Name: TCS_RingBufferManagement_RBMInit_SDSOM

Description: Verify the initialization, FIFO creation, and storage path retrieval of the SC_1430_SDSOM client with RBM.

Pre-Conditions:
1. Power Supply (PPS) is connected and set to 12V.
2. ECU is power cycled and boot is complete.
3. SSH connection to ECU is established.
4. SDSOM stub is launched.

Test Case Design:
Architecture Baseline Version: v0.3.1

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call `RBM_GetVersion` API from SDSOM | RBM returns Version Info successfully | RBM returns Version Info successfully |
| 2 | Call register callback and verify status | RBM returns status `RBM_ok` | RBM returns status `RBM_ok` |
| 3 | Call `RBM_ReqCbk` API from SDSOM | RBM triggers callback for `RBM_StorSize` | RBM triggers callback for `RBM_StorSize` |
| 4 | Call `RBM_GetState` to retrieve current state | RBM returns state `RBM_Init` | RBM returns state `RBM_Init` |
| 5 | Call `RBM_GetOMFIFOpath` to query FIFO path | RBM returns valid FIFO path (`fifopath`) | RBM returns valid FIFO path (`fifopath`) |
| 6 | Call `RBM_OpenOMFIFO` from SDSOM | FIFO path is opened successfully and returns `fifopath` | FIFO path is opened successfully and returns `fifopath` |
| 7 | Call `RBM_GetOMPrmntStorgPth` to query OM storage path | RBM returns valid storage path (`storgPth`) | RBM returns valid storage path (`storgPth`) |

Post-Condition:
1. Disconnect SSH from ECU.
2. Disconnect PPS power supply.

Source: examples/diagrams/rbm_init.puml
Generated: Tuesday, August 11, 2026
Platform Type: uP (Microprocessor)