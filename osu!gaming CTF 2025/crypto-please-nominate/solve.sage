#!/usr/bin/env sage -python

# Sage solver using univariate Coppersmith (small_roots)

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
        if not lines[i].startswith('message for'):
            i += 1
            continue
        name = lines[i].split('message for', 1)[1].strip()
        n = int(lines[i + 1])
        c = int(lines[i + 2])
        entries.append((name, n, c))
        i += 3
    return k, entries

def main():
    k, entries = parse_output('output.txt')
    B = pow(256, k)
    ns = [n for _, n, _ in entries]
    cs = [c for _, _, c in entries]
    prefixes = [f"hi there {name}, ".encode() for name, _, _ in entries]
    ts = [bytes_to_long(p) * B for p in prefixes]

    # Construct f_i(x) in Zmod(n_i)[x]
    polys = []
    for t, n, c in zip(ts, ns, cs):
        R.<x> = PolynomialRing(Zmod(n))
        f = (x + (t % n))^3 - c
        polys.append(f)

    # Combine to modulus N via CRT coefficient-wise
    N = 1
    for n in ns:
        N *= n
    R.<x> = PolynomialRing(Zmod(N))
    coeffs = []
    deg = max(f.degree() for f in polys)
    for j in range(deg + 1):
        residues = [int(f.list()[j]) if j < len(f.list()) else 0 for f in polys]
        cj = crt(residues, ns)
        coeffs.append(cj % N)
    fN = sum((coeffs[j] % N) * x^j for j in range(deg + 1))
    # Small roots search: try a few parameter sets
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
