# osu!gaming CTF 2025/crypto-please-nominate

Writeup for the challenge `please-nominate` `crypto` category

------------------------------------------------------------------------

**Category:** Crypto

**Author:** wwm

**Descritopn:** ok this time i'm going to be a bit more nice and personal when sending my message

**Flag Format:** osu{*}

## Challenge

We are provided two files:

- `script.py`: the challenge generator that encrypts a message for 3 recipients with RSA e=3 and prints the moduli and ciphertexts.
- `output.txt`: the concrete instance we must solve (flag length, three moduli, and three ciphertexts).

The relevant `output.txt` starts with the flag length (147), then, for each addressee, prints the modulus `n` and the ciphertext `c`:

```
147
message for Plus4j
<n1>
<c1>
message for Mattay
<n2>
<c2>
message for Dailycore
<n3>
<c3>
```

------------------------------------------------------------------------

## Step 1 --- First thoughts

- Same message structure to 3 recipients: each plaintext is `m_i = ("hi there NAME, " || FLAG)` as bytes, then interpreted as a big integer.
- Public exponent is small (`e = 3`), moduli are independent (distinct 727-bit primes squared -> ~1454-bit `n_i`).
- The greeting prefix depends on NAME, but is known. Only the suffix `FLAG` is unknown and its length is given: `|FLAG| = 147` bytes.
- This screams Håstad’s broadcast attack with known linear padding or, more directly, a univariate Coppersmith small-root problem:
  - For each recipient, define `f_i(x) = (x + t_i)^3 - c_i (mod n_i)` where `t_i` is the known greeting prefix times `B = 256^|FLAG|`.
  - The true unknown `x = FLAG_as_integer` is a common root of all `f_i` modulo their respective `n_i`.
  - Combine the congruences via CRT into a single polynomial `f(x) ≡ 0 (mod N)` with `N = n1*n2*n3`. Since `x < B` and `B ≈ 2^(8*147) = 2^1176` and `N^(1/3) ≈ 2^1454`, the small-root condition `x < N^(1/3)` holds comfortably.
  - Apply univariate Coppersmith to find the small integer root `x` of `f(x) ≡ 0 (mod N)`.

------------------------------------------------------------------------

## Step 2 --- Analysis

Let `B = 256^k` with `k = 147` and let `p_i = b"hi there NAME_i, "` be the known greeting prefix for each recipient. Define

- `t_i = bytes_to_long(p_i) * B`
- `m_i = t_i + F` where `F` is the flag as an integer, `0 ≤ F < B`.
- `c_i = m_i^3 mod n_i` with `e = 3`.

For each i:

`f_i(x) = (x + t_i)^3 - c_i ≡ 0 (mod n_i)`

By CRT on coefficients we can build a single polynomial `f(x) ≡ 0 (mod N)` where `N = n1*n2*n3`. Because `deg f = 3` and the true root satisfies `x = F < B`, and crucially `B < N^(1/3)`, univariate Coppersmith (Howgrave-Graham bound for univariate modular polynomials) guarantees recovery of the small root in polynomial time.

Why this works here:

- Each modulus is a product of two 727-bit primes, so `log2 n_i ≈ 1454`. `log2 N = log2(n1*n2*n3) ≈ 3*1454 = 4362`.
- `log2 B = 8 * 147 = 1176` and thus `B < 2^1454 ≈ N^(1/3)`.
- Therefore, the small-root condition holds with significant slack, making the lattice step easy.

------------------------------------------------------------------------

## Step 3 --- Exploit script

I implemented two solvers in this repository; keeping the write-up code-free to stay concise:

- `solve.py` - Python prototype that constructs the CRT‑combined cubic and documents the approach.
- `solve.sage` - SageMath solver that applies `small_roots` and recovers the flag end‑to‑end.

Usage: run `sage solve.sage`.

------------------------------------------------------------------------

## Step 4 --- Result

Running the Sage solver:

```
$ sage solve.sage
guys please play resplendence https://osu.ppy.sh/beatmapsets/2436259#osu/5311353 6 digit represent osu{0mg_my_m4p_f1n4lly_g0t_r4nk3d_1m_s0_h4ppy!!}
```

------------------------------------------------------------------------

## Flag

    osu{0mg_my_m4p_f1n4lly_g0t_r4nk3d_1m_s0_h4ppy!!}

------------------------------------------------------------------------

## Notes

- The problem is a textbook univariate Coppersmith setup once you notice the known linear padding and the provided length of the unknown suffix.
- A tempting linear-combination trick to isolate `F^3` by solving for weights `α_i` such that `Σ α_i = 1`, `Σ α_i t_i = 0`, `Σ α_i t_i^2 = 0 (mod N)` did not yield a perfect cube when implemented naively; doing everything per-modulus and CRT-ing the final `S` is delicate and easy to get wrong. The Sage small_roots approach was faster and more reliable.
- Key bound check: with k=147, `B = 256^147 ≈ 2^1176` and `N^(1/3) ≈ 2^1454`, comfortably satisfying the small-root requirement `X < N^(1/deg)` for `deg = 3`.
- If SymPy/LLL are your only tools, you can still succeed by hand-rolling a small LLL basis for Howgrave–Graham, but Sage’s `small_roots` is the cleanest here.

