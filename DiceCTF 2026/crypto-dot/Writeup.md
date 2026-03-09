# DiceCTF 2026/crypto-dot

Writeup for the challenge "dot" [crypto] in DiceCTF 2026 playing with THEM?!

------------------------------------------------------------------------

**Category:** Crypto  
**Author:** defund
**Description:** dot dot dot
**Flag Format:** `dice{*}`

## Challenge

We were given a remote service:

```text
nc dot.chals.dicec.tf 1337
```

and a [tar.gz archive](https://github.com/paveledits/Writeups/blob/main/DiceCTF%202026/crypto-dot/crypto_dot.tar.gz) with the SNARG code, the circuit, and `crs.bin`.

The server asks for random 64-bit additions. For each round it expects:

1. an answer `c`
2. a 66-byte proof, encoded as two compressed P-256 points

If the proof is valid and the answer is wrong, the streak goes up. After 20 of those in a row, the flag is printed.

The important files were:

- `server.py`
- `snarg.py`
- `dpp.py`
- `add.py`
- `crs.bin`

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

The first important observation is that this is a designated-verifier SNARG.

The verifier does not check a whole witness directly. It only checks whether a single elliptic-curve point lands in a precomputed table:

```python
p = h2 - sk * h1
p += input_sum * G
return encode(p) in table
```

So the proof is really just controlling one hidden scalar in the exponent.

The second important observation is that the CRS gives us everything the prover needs. We can build honest proofs for any statement we know how to evaluate, because `crs.bin` contains the prover-side points.

For a correct statement, the full dot product has the form

```text
k + b * (k^2 - val)
```

where `b = trace_len * BOUND1 + 1 = 162817`, and the answer table stores exactly those values for all small enough `k`.

For a wrong statement, the natural proof from the wrong trace still satisfies the tensor structure and all gate constraints, but it violates the final output constraint. So we only need to understand how to cancel that one missing term.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

The adder circuit ends in a final `AndGate`. In this challenge instance, that last gate uses:

- output wire `out`
- left input wire `l`
- right input wire `r`
- constrained pair entry `pair(l, r)`

There is also a huge set of pair coordinates that never appear in any constraint at all. For those free pair coordinates, the corresponding query coefficient is just:

```text
b * q2_i
```

with no extra random constraint term mixed in.

That makes the honest proof a very nice oracle.

If I take a correct proof and add one free pair CRS entry, then subtract `b * t * G`, the modified proof stays valid exactly when that free pair has `q2_i = t`.

That means I can recover specific hidden `q2` values without ever learning the verifier secret key.

I only needed four small values from the hidden vector `v`:

- `|v_out|`
- `|v_l|`
- `|v_r|`
- one nonzero reference value `|v_ref|`

The diagonals of free pair coordinates give `v_i^2`, so I recovered each absolute value by brute forcing `0..256` against a correct proof.

Then I used two free off-diagonal pairs:

- `(l, ref)`
- `(r, ref)`

to recover the signs of `v_l * v_ref` and `v_r * v_ref`.

From those two signs I get the sign of `v_l * v_r`, and therefore I recover:

```text
q2_last = 2 * v_l * v_r
```

This is the only nontrivial number the final exploit needs.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

Now the key algebra.

Let:

- `q_out` be the query coefficient at the final output wire
- `q_lastpair` be the query coefficient at the constrained pair of the last gate
- `q2_last = 2 * v_l * v_r`

For the last gate, the combination

```text
q_out - q_lastpair + b * q2_last
```

simplifies to

```text
v_out + b * r_out
```

where `r_out` is exactly the random coefficient attached to the final output constraint.

That is the whole break.

For a wrong answer `c' = c xor 1`, the honest proof from the wrong trace is off by exactly `-b * r_out`, because only the final output constraint fails.

So if we add

```text
q_out - q_lastpair + b * q2_last - v_out
```

to that wrong proof, the missing term is cancelled and the proof becomes valid again.

At the point level, the correction is:

```text
CRS[out] - CRS[last_pair] + (b * q2_last - v_out) * G
```

The only remaining ambiguity is the sign of `v_out`. I did not need to recover it during precomputation. I just tried both signs once on the first forged round, kept the one that worked, and reused it for the next 19 rounds.

The final solver is [solve.py](https://github.com/paveledits/Writeups/blob/main/DiceCTF%202026/crypto-dot/solve.py).

Run it with:

```bash
python3 solve.py
```

It:

1. builds one honest correct proof
2. recovers `|v_out|`, `|v_l|`, `|v_r|`, and a nonzero reference value
3. reconstructs `q2_last`
4. tries both signs of `v_out` once
5. sends 20 wrong but valid proofs

---

## Flag

```text
dice{operation_spot_by_odd_part_of_drug_city}
```

---

## Notes

The big lesson here is that the designated-verifier structure is doing too much work in one hidden scalar.

Once I noticed that free pair coordinates act like a clean oracle for the hidden `q2` values, the problem stopped being “break a SNARG” and became “recover a few small integers and splice in the exact correction term.”
