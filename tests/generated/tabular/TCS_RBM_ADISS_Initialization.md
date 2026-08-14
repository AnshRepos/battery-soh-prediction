### 📋 **Test Case Name**: TCS_RBM_ADISS_Initialization

**Description**: Verifies the initialization sequence of the RBM component by the ADISS client.

**Platform**: uP (Microprocessor)

**Pre-Conditions:**
1. RBM component is running.
2. ADISS component is running.
3. System is in a state where RBM initialization is required.

**Test Case Design:**
Architecture Baseline Version: v0.1.0

| Steps | Input Operations | Expected Result | Actual Results |
|:---|:---|:---|:---|
| 1 | Call `RBM_GetVersion()` via ADISS | Return value contains RBM version information. | Return value contains RBM version information. |
| 2 | Call `RBM_RegCallBack()` via ADISS | Return value is `RBM_ok`. | Return value is `RBM_ok`. |
| 3 | Call `RBM_ReqCbk()` via ADISS | An asynchronous callback is received with the `RBM_StorSize` event. | An asynchronous callback is received with the `RBM_StorSize` event. |
| 4 | Call `RBM_GetState()` via ADISS | Return value is `RBM_Init`. | Return value is `RBM_Init`. |
| 5 | Call `RBM_CreateBufswContent()` via ADISS | Return value is `RBM_ok`. | Return value is `RBM_ok`. |
| 6 | Call `RBM_GetADISSPrmntStorgPth()` via ADISS | Return value contains the storage path `storgPth`. | Return value contains the storage path `storgPth`. |
| 7 | Call `RBM_EnterStandby()` via ADISS | **If isTimeSyncValid is true:**<br>- Return value is `RBM_ok`.<br>- Asynchronous callback `RBM_StateChange` is received with state `RBM_Standby`.<br><br>**If isTimeSyncValid is false:**<br>- Return value is `RBM_NoTSync`. | **If isTimeSyncValid is true:**<br>- Return value is `RBM_ok`.<br>- Asynchronous callback `RBM_StateChange` is received with state `RBM_Standby`.<br><br>**If isTimeSyncValid is false:**<br>- Return value is `RBM_NoTSync`. |

**Post-Condition:**
1. ADISS client has successfully registered its callbacks with RBM.
2. If TimeSync was valid, the RBM state for the ADISS client is `Standby`.
3. If TimeSync was invalid, the RBM state for the ADISS client remains `Init`.
4. The ADISS client has received the permanent storage path.

**Source**: `examples/diagrams/rbm_init.puml` (Flow: ADISS Initialization)
