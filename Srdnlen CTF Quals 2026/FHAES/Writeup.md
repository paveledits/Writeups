# srdnlen CTF Quals 2026/crypto-FHAES

Writeup for the Challenge "FHAES" [crypto] in srdnlen CTF 2026 playing with THEM?!

------------------------------------------------------------------------

**Category:** crypto  
**Author:** lrnzsir  
**Description:** 
Here it is! Fully Homomorphic AES encryption finally made practical.

This is a remote challenge, you can connect to the service with: `nc fhaes.challs.srdnlen.it 1337`

**Flag Format:** srdnlen{*}

## Challenge

We are given a Python service running over the network that implements a custom AES evaluation using Garbled Circuits via Oblivious Transfer (OT). The service allows us to provide a custom garbled circuit definition.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

The server lets us supply an arbitrary `custom_circuit` and evaluates it using its own `Garbler` instance. The critical observation is that the Garbler reuses the same secret $\Delta$ label for the Free-XOR optimization. The `add_equality_constraint` logic and predictable hashing within `__garble_and_gate` make the circuit structures completely deterministic locally.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

In order to recover the master AES key, we need to extract the Garbler's secret $\Delta$. We can bypass the secure evaluation boundary by supplying a minimal custom circuit:
1. `Z = XOR(x_0, x_0)`: Gives a wire whose zero-label is exactly $0$.
2. `O = NOT(Z)`: Gives a wire whose zero-label is exactly $\Delta$.
3. `Z_AND_O = AND(Z, O)`: When the Garbler hashes these inputs, the zero labels cancel out the random scalar $r$ exactly such that $gate0 \oplus gate1 = \Delta$.

Once $\Delta$ is extracted, we can passively ungarble the AES encryption AND gates locally to track the semantic values. Because the initial AES layer xors the plaintext with the master key, the ungarbled gates give us 2640 linear equations over $GF(2)$ for the key bits.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

We formulate a GF(2) matrix of these states and solve it constraints to recover the AES key, then submit it back to the server to get the flag.

The final exploit solves the linear equations to correctly extract the key.

---

## Flag

```
srdnlen{I_hope_you_didn't_slop_this_one...although_I_don't_know_if_you_can_slop_it...}
```

---

## Notes

- The challenge featured local Pure Python libraries for ECDSA, required an offline solver for determining semantic bits of AES gates, and constructed equations dynamically directly off of AES states.
