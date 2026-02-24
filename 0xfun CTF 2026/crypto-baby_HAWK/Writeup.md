# 0xfun CTF 2026/crypto-baby_HAWK

Writeup for the Challenge "baby_HAWK" [crypto] in 0xfun CTF 2026 playing  
with THEM?!

------------------------------------------------------------------------

**Category:** Crypto  
**Author:** Hadi  
**Description:** hawk meets his cousin can they find the right basis?  
**Flag Format:** 0xfun{*}

## Challenge

We are given `hawk.zip` containing:

- `babyHAWK.sage`: generator for the challenge.
- `hawk.sage`: HAWK-related helper code.
- `output.txt`: public values (`q0,q1,q2` and `s0,s1,s2`) plus `iv` and `enc`.

`babyHAWK.sage` builds a secret basis

`B = [[f, F], [g, G]]`

over `K = Q(zeta_256)` (degree 128), and then prints:

- `Q = B.H * B` (Hermitian Gram matrix)
- `S = B * B.H`

along with an AES-CBC encryption of the flag using:

`key = sha256(str(sk))` where `sk = (f,g,F,G)`.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

The key observation is that `Q` and `S` are Gram matrices of the same secret basis `B`:

- `Q = B.H * B`
- `S = B * B.H`

If we could recover `B` (i.e., the secret polynomials `f,g,F,G`), we can recompute the AES key and decrypt.

My first attempt was the “standard” lattice approach: build a lattice from `(q0,q1)` and run LLL/BKZ to find a short vector that corresponds to `(f,g)` (since `q0 = f*bar(f) + g*bar(g)` and the constant term `q0[0]` equals `||f||^2 + ||g||^2`).

This works on small toy dimensions, but for the real dimension `n=128` it required very large BKZ block sizes and was too slow for the time limit.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

I pivoted to using **both** `Q` and `S` to create an exact linear-algebra problem first.

**1) Determinant trick (gives inverses “for free”)**
Because `det(B) = f*G - g*F = 1` in this scheme, we also have:

- `det(Q) = det(B.H*B) = 1`
- `det(S) = det(B*B.H) = 1`

So for the public 2x2 Hermitian matrices, the inverses are:

- `Q^{-1} = [[q2, -q1], [-conj(q1), q0]]`
- `S^{-1} = [[s2, -s1], [-conj(s1), s0]]`

**2) Linear equations in (f,g,F,G)**
We can write two equal expressions for `B^{-H}` (inverse of the conjugate-transpose):

- `B * Q^{-1} = B^{-H}`
- `S^{-1} * B = B^{-H}`

And because `det(B)=1`, we also know explicitly:

`B^{-H} = [[conj(G), -conj(g)], [-conj(F), conj(f)]]`.

Equating these gives 8 polynomial equations that are **linear** in the unknowns `(f,g,F,G)` when `q*unknown` is treated as “multiply by a known public polynomial”.

**3) Make it fast with negacyclic convolution matrices**
In `K = Q(zeta_256)` we have `zeta_256^128 = -1`, so multiplication in the power basis is just **negacyclic convolution mod `x^128+1`**.

That means “multiply by `q0`” is a fixed `128x128` integer matrix `M(q0)`.
Also complex conjugation on coefficient vectors is a fixed signed-permutation matrix.

Putting it together, the 8 linear equations become one big integer system:

- `A * x = 0` over `ZZ`
- `A` has shape `1024 x 512`
- `x` is the concatenation of coefficient vectors for `f,g,F,G` (each length 128)

This system is underdetermined (kernel dimension 128), but now the problem becomes:

> Find the “short” integer vector in that kernel corresponding to the real secret basis.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

1. Build the integer matrix `A` encoding the linear relations derived from `Q` and `S`.
2. Compute an integer basis for the right-kernel of `A` (a lattice of solutions).
3. Run LLL on that kernel basis.
4. Scan the reduced basis for a vector whose split `(f,g)` and `(F,G)` norms match `||f||^2 + ||g||^2 = q0[0] = 910` and `||F||^2 + ||G||^2 = q2[0] = 8149`.
5. Verify the candidate exactly by recomputing `Q` and `S` from `B=[[f,F],[g,G]]` and checking equality.
6. Handle the final ambiguity: multiplying the whole secret by a 256th root of unity keeps `Q,S` identical, but changes `str(sk)` and therefore the AES key. Brute-force `u = zeta256^k` for `k=0..255` until AES-CBC unpadding succeeds.

The solver is provided separately:
`solve.py`

From the challenge folder, run:
`sage -python solve.py`

---

## Flag

```
0xfun{f0r_th3_c000LLL_baby_th4nk5_d$128}
```

---

## Notes

- The initial “BKZ on a 256-dim lattice” approach is conceptually standard, but was too slow for `n=128` under time pressure.
- The key speedup was converting the problem to a linear system over `ZZ` using both `Q` and `S`, then doing LLL only on the kernel lattice (dimension 128).
- The final AES-key mismatch was caused by the root-of-unity ambiguity: `B` and `u*B` have the same Gram matrices, but produce different `sha256(str(sk))`. Brute-forcing `k` fixed it (the correct one was `k=128`, i.e. `u=-1`).
