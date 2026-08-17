# Test Cases for RBM Init

## ADISS Success Path

| Test Step | Action | Expected Result | Comment |
|---|---|---|---|
| 1 | `Suite Setup` | - | `uP-aurix` |
| 2 | `Connect via SSH` | Connection successful | - |
| 3 | `Call RBM_GetVersion()` | RBM version is returned | Check for non-empty string |
| 4 | `Call RBM_EnterStandby()` | `RBM_OK` is returned | - |
| 5 | `Disconnect SSH` | Disconnection successful | - |

## ADISS Failure Path

| Test Step | Action | Expected Result | Comment |
|---|---|---|---|
| 1 | `Suite Setup` | - | `uP-aurix` |
| 2 | `Connect via SSH`| Connection successful | - |
| 3 | `Call RBM_GetVersion()` | RBM version is returned | Check for non-empty string |
| 4 | `Call RBM_EnterStandby()` | `RBM_NOK` is returned | Simulate failure |
| 5 | `Disconnect SSH` | Disconnection successful | - |

## RDC Path

| Test Step | Action | Expected Result | Comment |
|---|---|---|---|
| 1 | `Suite Setup` | - | `uP-aurix` |
| 2 | `Connect via SSH`| Connection successful | - |
| 3 | `Call RBM_GetVersion()` | RBM version is returned | Check for non-empty string |
| 4 | `Disconnect SSH` | Disconnection successful | - |

## SDSOM Path

| Test Step | Action | Expected Result | Comment |
|---|---|---|---|
| 1 | `Suite Setup` | - | `uP-aurix` |
| 2 | `Connect via SSH`| Connection successful | - |
| 3 | `Call RBM_GetVersion()` | RBM version is returned | Check for non-empty string |
| 4 | `Disconnect SSH` | Disconnection successful | - |
