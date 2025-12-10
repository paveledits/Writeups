# WannaGame 2026/web3-WickedCraft

Writeup for the Challenge "WickedCraft" [web3] in WannaGame 2026 playing  
with THEM?!

------------------------------------------------------------------------

**Category:** web3  
**Description:** 
**Flag Format:** W1{*}

## Challenge

We are provided with the source code for a DeFi-like challenge involving three smart contracts:
- `Setup.sol`: Deploys the challenge environment.
- `Aggregator.sol`: A contract that executes swaps and other commands based on custom calldata.
- `WannaCoin.sol`: An ERC20 token with `Multicall` functionality.

The goal is to solve the challenge, which is determined by the `isSolved()` function in `Setup.sol`.
```solidity
    function isSolved() external view returns (bool) {
        return coin.balanceOf(address(coin)) > 10_000 * 10 ** coin.decimals();
    }
```
Initially, the `Setup` contract holds the tokens (minted in constructor). We need to move these tokens to the `WannaCoin` contract address itself.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

The `Setup` contract approves the `Aggregator` to spend its `WannaCoin` tokens:
```solidity
    coin.approve(address(aggregator), type(uint256).max);
```
This means the `Aggregator` contract has the authority to transfer tokens *from* the `Setup` contract.

The `Aggregator` contract has a `swap` function that takes a byte array as input. It parses this data to execute a series of commands. One of the commands is `CommandAction.Call`, which allows making arbitrary external calls.

However, there is a specific check in `executeCommandCall` that blacklists the `transferFrom` selector:
```solidity
            case 0x23b872dd {
                // Blacklist transferFrom in custom calls
                // InvalidTransferFromCall
                mstore(
                    0,
                    0x1751a8e400000000000000000000000000000000000000000000000000000000
                )
                revert(0, 4)
            }
```
This prevents us from directly commanding the `Aggregator` to call `WannaCoin.transferFrom(Setup, ...)` to move the funds.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

The `WannaCoin` contract inherits from `Multicall`:
```solidity
contract WannaCoin is ERC20, Multicall { ... }
```
The `Multicall` contract (from OpenZeppelin) provides a `multicall(bytes[] calldata data)` function that iterates over the provided data and performs delegatecalls or calls to itself. Crucially, `Multicall.multicall` wraps other function calls.

If we command the `Aggregator` to call `WannaCoin.multicall(...)`, the selector seen by the `Aggregator`'s blacklist check will be `multicall`'s selector, not `transferFrom`. Inside the `multicall` execution (which happens in the context of `WannaCoin` but initiated by `Aggregator`), `WannaCoin` will execute the payload we provide.

Wait, `Multicall` usually executes a `delegatecall` to itself or just a function call. In OpenZeppelin's `Multicall`, it calls `address(this).delegatecall` (if not implemented) or simply loops and calls functions on `this`. Since `WannaCoin` is the target, calling `multicall` on it allows us to batch calls to `WannaCoin`.

By wrapping the forbidden `transferFrom` call inside a `multicall` payload, we bypass the `Aggregator`'s shallow inspection. The `Aggregator` sees a call to `multicall`, allows it, and then `WannaCoin` executes the inner `transferFrom`. Since `Aggregator` is the caller of `multicall`, `msg.sender` inside `transferFrom` (if it were a direct call) would be `Aggregator`. But wait, `Multicall` executes calls on the contract itself. `transferFrom` is an external function of `ERC20`.

The chain of execution is:
1. `Aggregator` calls `WannaCoin.multicall(payload)`.
2. `WannaCoin` executes `this.functionCall(payload[i])`.
3. `WannaCoin.transferFrom(Setup, WannaCoin, amount)` is executed.
   - `msg.sender` for this call is `Aggregator`.
   - `Aggregator` has allowance from `Setup`.
   - The transfer succeeds.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

The exploit involves manually constructing the raw calldata for the `Aggregator.swap` function to trigger this sequence. The `Aggregator` uses a custom binary format for commands and sequences involving pointers and explicit lengths.

The `solver.py` script implements `build_exploit_calldata` to construct this complex byte array. It sets up:
1. A generic `CommandAction.Call`.
2. A sequence that provides the `multicall` selector and the logical data payload (which contains the encoded `transferFrom`).
3. Correct offsets and lengths as required by the `Aggregator`'s assembly parsing logic.

---

## Flag

```
W1{*}
```
