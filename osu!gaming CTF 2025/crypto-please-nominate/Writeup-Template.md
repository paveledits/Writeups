# osu! CTF 2025/`crypto`{=html}-`please-nominate`{=html}

Writeup for the challenge "`please-nominate`{=html}"
`crypto`{=html} category

------------------------------------------------------------------------

**Category:** `Crypto`{=html}

**Author:** `wwm`{=html}

**Descritopn:** "ok this time i'm going to be a bit more nice and personal when sending my message" — three personalized RSA messages with the same small public exponent e=3 and a known greeting prefix addressed to different people. We are given the modulus and ciphertext for each recipient, and the length of the secret flag appended to each greeting. The goal is to recover the flag.

**Flag Format:** osu{\*}

## Challenge

We are provided two files:

- `script.py`: the challenge generator that encrypts a message for 3 recipients with RSA e=3 and prints the moduli and ciphertexts.
- `output.txt`: the concrete instance we must solve (flag length, three moduli, and three ciphertexts).

Challenge generator (`script.py`):

```python
from Crypto.Util.number import *

FLAG = open("flag.txt").read()

BNS = ["Plus4j", "Mattay", "Dailycore"]
print(len(FLAG))

for BN in BNS:
    print("message for", BN)
    message = bytes_to_long(
        (f"hi there {BN}, " + FLAG).encode()
    )
    n = getPrime(727) * getPrime(727)
    e = 3
    print(n)
    print(pow(message, e, n))
```

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

I implemented two solvers:

1) A Python prototype that constructs the CRT-combined cubic and attempts a basic small-root recovery. This is useful for documentation but relies on SymPy and a simple LLL that may be fragile.

2) A robust SageMath solver that uses `small_roots` on the univariate cubic modulo `N`. This solved the instance instantly and is the recommended approach.

Python version (`solve.py`):

```python
#!/usr/bin/env python3

from typing import List, Tuple
from Crypto.Util.number import bytes_to_long

def crt(residues: List[int], moduli: List[int]) -> Tuple[int, int]:
    M = 1
    for m in moduli:
        M *= m
    x = 0
    for r, m in zip(residues, moduli):
        Mi = M // m
        ei = pow(Mi, -1, m)
        x = (x + r * Mi * ei) % M
    return x, M

def parse_output(path: str):
    with open(path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    k = int(lines[0])
    entries = []
    i = 1
    while i < len(lines):
        if lines[i].startswith('message for'):
            name = lines[i].split('message for', 1)[1].strip()
            n = int(lines[i+1]); c = int(lines[i+2])
            entries.append((name, n, c))
            i += 3
        else:
            i += 1
    return k, entries

def build_coeffs(k: int, entries):
    prefixes = [f"hi there {name}, ".encode() for name,_,_ in entries]
    B = pow(256, k)
    a2_res, a1_res, a0_res, moduli = [], [], [], []
    for pref, (_, n, c) in zip(prefixes, entries):
        t = bytes_to_long(pref) * B
        a2_res.append((3 * t) % n)                 # for x^2
        a1_res.append((3 * (t % n) * (t % n)) % n) # for x
        a0_res.append((pow(t % n, 3, n) - c) % n)  # constant term
        moduli.append(n)
    a2, N = crt(a2_res, moduli)
    a1, _ = crt(a1_res, moduli)
    a0, _ = crt(a0_res, moduli)
    return (1, a2, a1, a0), N

def main():
    k, entries = parse_output('output.txt')
    coeffs, N = build_coeffs(k, entries)
    # For a robust solve, use the Sage script below.
    print('Built cubic over Z_N: x^3 + a2 x^2 + a1 x + a0 ≡ 0 (mod N)')
    print('Use solve.sage for small_roots to recover x.')

if __name__ == '__main__':
    main()
```

SageMath version (`solve.sage`):

```python
#!/usr/bin/env sage

from sage.all import Zmod, PolynomialRing, crt

def bytes_to_long(b: bytes) -> int:
    return int.from_bytes(b, 'big')

def long_to_bytes(n: int, length: int = None) -> bytes:
    if n == 0:
        b = b"\x00"
    else:
        l = (n.bit_length() + 7) // 8
        b = n.to_bytes(l, 'big')
    if length is not None:
        if len(b) > length:
            b = b[-length:]
        elif len(b) < length:
            b = b"\x00" * (length - len(b)) + b
    return b

def parse_output(path: str):
    with open(path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    k = int(lines[0])
    entries = []
    i = 1
    while i < len(lines):
        if lines[i].startswith('message for'):
            name = lines[i].split('message for', 1)[1].strip()
            n = int(lines[i + 1])
            c = int(lines[i + 2])
            entries.append((name, n, c))
            i += 3
        else:
            i += 1
    return k, entries

def main():
    k, entries = parse_output('output.txt')
    B = pow(256, k)
    ns = [n for _, n, _ in entries]
    cs = [c for _, _, c in entries]
    prefixes = [f"hi there {name}, ".encode() for name, _, _ in entries]
    ts = [bytes_to_long(p) * B for p in prefixes]

    # Build f_i(x) = (x + t_i)^3 - c_i in Z_n[x]
    polys = []
    for t, n, c in zip(ts, ns, cs):
        R.<x> = PolynomialRing(Zmod(n))
        f = (x + (t % n))^3 - c
        polys.append(f)

    # CRT-combine coefficients to modulus N
    N = 1
    for n in ns:
        N *= n
    R.<x> = PolynomialRing(Zmod(N))
    deg = max(f.degree() for f in polys)
    coeffs = []
    for j in range(deg + 1):
        residues = [int(f.list()[j]) if j < len(f.list()) else 0 for f in polys]
        cj = crt(residues, ns) % N
        coeffs.append(cj)
    fN = sum((coeffs[j] % N) * x^j for j in range(deg + 1))

    # Small roots search with a few parameter sweeps
    roots = []
    for beta in [1.0, 0.9, 0.8, 0.7]:
        for m in [1, 2, 3]:
            for t in [1, 2, 3, 4]:
                try:
                    roots = fN.small_roots(X=B, beta=beta, m=m, t=t)
                except Exception:
                    roots = []
                if roots:
                    break
            if roots:
                break
        if roots:
            break
    if not roots:
        print("No small root found")
        return
    F = int(roots[0])
    print(long_to_bytes(F, k).decode(errors='replace'))

if __name__ == '__main__':
    main()
```

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
