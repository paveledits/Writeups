#!/usr/bin/env python3

from typing import List, Tuple
from fractions import Fraction


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


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def invmod(a: int, m: int) -> int:
    g, x, _ = egcd(a, m)
    if g != 1:
        raise ValueError("no inverse")
    return x % m


def crt(residues: List[int], moduli: List[int]) -> Tuple[int, int]:
    M = 1
    for m in moduli:
        M *= m
    x = 0
    for r, m in zip(residues, moduli):
        Mi = M // m
        ei = invmod(Mi % m, m)
        x = (x + r * Mi * ei) % M
    return x, M


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


def matrix_inv_mod3(A: List[List[int]], m: int) -> List[List[int]]:
    n = 3
    M = [[A[i][j] % m for j in range(n)] for i in range(n)]
    I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for col in range(n):
        pivot = None
        for r in range(col, n):
            if M[r][col] % m != 0 and egcd(M[r][col] % m, m)[0] == 1:
                pivot = r
                break
        if pivot is None:
            raise ValueError("Matrix not invertible modulo m")
        if pivot != col:
            M[col], M[pivot] = M[pivot], M[col]
            I[col], I[pivot] = I[pivot], I[col]
        inv_p = invmod(M[col][col] % m, m)
        for j in range(n):
            M[col][j] = (M[col][j] * inv_p) % m
            I[col][j] = (I[col][j] * inv_p) % m
        for r in range(n):
            if r == col:
                continue
            factor = M[r][col] % m
            if factor:
                for j in range(n):
                    M[r][j] = (M[r][j] - factor * M[col][j]) % m
                    I[r][j] = (I[r][j] - factor * I[col][j]) % m
    return I


def integer_cuberoot(n: int) -> Tuple[int, bool]:
    if n < 0:
        raise ValueError("negative not supported")
    if n == 0:
        return 0, True
    x = 1 << ((n.bit_length() + 2) // 3)
    while True:
        y = (2 * x + n // (x * x)) // 3
        if y >= x:
            r = x
            break
        x = y
    return r, r * r * r == n


def recover_flag_via_linear_combo(k: int, entries: List[Tuple[str, int, int]]):
    B = pow(256, k)
    names = [name for name, _, _ in entries]
    ns = [n for _, n, _ in entries]
    cs = [c for _, _, c in entries]
    ts = [bytes_to_long(f"hi there {name}, ".encode()) * B for name in names]
    alphas_mod = []
    for m in ns:
        A = [[1 % m, 1 % m, 1 % m], [t % m for t in ts], [((t % m) * (t % m)) % m for t in ts]]
        try:
            Ainv = matrix_inv_mod3(A, m)
        except ValueError:
            return None
        bvec = [1 % m, 0, 0]
        alpha = [sum(Ainv[i][j] * bvec[j] for j in range(3)) % m for i in range(3)]
        alphas_mod.append(alpha)
    N = 1
    for m in ns:
        N *= m
    alphas = []
    for idx in range(3):
        residues = [am[idx] for am in alphas_mod]
        a, _ = crt(residues, ns)
        alphas.append(a)
    S = 0
    for a, c in zip(alphas, cs):
        S = (S + (a % N) * (c % N)) % N
    for a, t in zip(alphas, ts):
        S = (S - (a % N) * pow(t % N, 3, N)) % N
    r, exact = integer_cuberoot(S)
    if not exact:
        return None
    flag_bytes = long_to_bytes(r, k)
    try:
        return flag_bytes.decode()
    except UnicodeDecodeError:
        return flag_bytes.decode(errors='replace')


def build_coeffs(k: int, entries: List[Tuple[str, int, int]]):
    prefixes = [f"hi there {name}, ".encode() for name, _, _ in entries]
    B = pow(256, k)
    a2_res = []
    a1_res = []
    a0_res = []
    moduli = []
    for pref, (_, n, c) in zip(prefixes, entries):
        t = bytes_to_long(pref) * B
        a2_res.append((3 * t) % n)
        a1_res.append((3 * (t % n) * (t % n)) % n)
        a0_res.append((pow(t % n, 3, n) - c) % n)
        moduli.append(n)
    a2, N = crt(a2_res, moduli)
    a1, _ = crt(a1_res, moduli)
    a0, _ = crt(a0_res, moduli)
    def center(x: int) -> int:
        if x > N // 2:
            return x - N
        return x
    a2c = center(a2)
    a1c = center(a1)
    a0c = center(a0)
    return (1, a2c, a1c, a0c), N


def lll_reduction(basis: List[List[int]], delta: Fraction = Fraction(3, 4)) -> List[List[int]]:
    n = len(basis)
    m = len(basis[0])
    Bm = [list(map(int, row)) for row in basis]
    def dot(u, v):
        return sum(int(ui) * int(vi) for ui, vi in zip(u, v))
    def gram_schmidt(Bb):
        n = len(Bb)
        U = [[Fraction(0) for _ in range(n)] for _ in range(n)]
        bstar = [[Fraction(0) for _ in range(m)] for _ in range(n)]
        B_norm = [Fraction(0) for _ in range(n)]
        for i in range(n):
            bstar[i] = [Fraction(x) for x in Bb[i]]
            for j in range(i):
                mu = Fraction(dot(Bb[i], bstar[j]), dot(bstar[j], bstar[j])) if dot(bstar[j], bstar[j]) != 0 else Fraction(0)
                U[i][j] = mu
                for k in range(m):
                    bstar[i][k] -= mu * bstar[j][k]
            B_norm[i] = Fraction(dot(bstar[i], bstar[i]))
        return U, bstar, B_norm
    def size_reduce(Bb, U, i, j):
        mu = U[i][j]
        r = int(round(mu))
        if r != 0:
            for k in range(m):
                Bb[i][k] -= r * Bb[j][k]
            for k in range(j + 1):
                U[i][k] -= Fraction(r) * U[j][k]
    i = 1
    U, bstar, B_norm = gram_schmidt(Bm)
    while i < n:
        for j in range(i - 1, -1, -1):
            size_reduce(Bm, U, i, j)
        U, bstar, B_norm = gram_schmidt(Bm)
        lhs = B_norm[i]
        rhs = (delta - U[i][i - 1] * U[i][i - 1]) * B_norm[i - 1]
        if lhs >= rhs:
            i += 1
        else:
            Bm[i], Bm[i - 1] = Bm[i - 1], Bm[i]
            i = max(i - 1, 1)
            U, bstar, B_norm = gram_schmidt(Bm)
    return Bm


def small_root_hg(coeffs: Tuple[int, int, int, int], N: int, X: int):
    a3, a2, a1, a0 = coeffs
    assert a3 == 1
    try:
        import sympy as sp
    except ModuleNotFoundError:
        return None
    x = sp.symbols('x')
    def build_basis(m: int, t: int):
        f_vec = [a0, a1 * X, a2 * (X ** 2), (X ** 3)]
        def poly_mul(p, q):
            r = [0] * (len(p) + len(q) - 1)
            for i, pi in enumerate(p):
                if pi == 0:
                    continue
                for j, qj in enumerate(q):
                    if qj == 0:
                        continue
                    r[i + j] += pi * qj
            return r
        rows = []
        max_deg = 0
        fps = [[1]]
        if m >= 1:
            fps.append(f_vec[:])
        for i in range(2, m + 1):
            fps.append(poly_mul(fps[-1], f_vec))
        for i in range(m):
            for j in range(3):
                p = fps[i][:]
                if j:
                    p = [0] * j + p
                if j:
                    for k in range(len(p)):
                        p[k] *= (X ** j)
                scalar = pow(N, m - i)
                p = [coeff * scalar for coeff in p]
                rows.append(p)
                max_deg = max(max_deg, len(p) - 1)
        if m >= 1:
            p = fps[m][:]
            for j in range(t):
                vec = p[:] if j == 0 else ([0] * j + p[:])
                rows.append(vec)
                max_deg = max(max_deg, len(vec) - 1)
        L = max_deg + 1
        basis = [row + [0] * (L - len(row)) for row in rows]
        return basis, L
    for m, t in ((1, 1), (2, 1)):
        basis, L = build_basis(m, t)
        red = None
        try:
            from mpmath import mp
            mp.dps = 200
            Bm = [row[:] for row in basis]
            n = len(Bm)
            mcols = len(Bm[0])
            def dotf(u, v):
                return sum(mp.mpf(ui) * mp.mpf(vi) for ui, vi in zip(u, v))
            def gram_schmidt_float(Bb):
                n = len(Bb)
                bstar = [[mp.mpf(0) for _ in range(mcols)] for _ in range(n)]
                mu = [[mp.mpf(0) for _ in range(n)] for _ in range(n)]
                Bnorm = [mp.mpf(0) for _ in range(n)]
                for i in range(n):
                    bstar[i] = [mp.mpf(xv) for xv in Bb[i]]
                    for j in range(i):
                        denom = dotf(bstar[j], bstar[j])
                        mu[i][j] = dotf(Bb[i], bstar[j]) / denom if denom != 0 else mp.mpf(0)
                        for k in range(mcols):
                            bstar[i][k] -= mu[i][j] * bstar[j][k]
                    Bnorm[i] = dotf(bstar[i], bstar[i])
                return mu, bstar, Bnorm
            i = 1
            mu, bstar, Bnorm = gram_schmidt_float(Bm)
            deltaf = mp.mpf('0.99')
            while i < n:
                for j in range(i - 1, -1, -1):
                    rint = int(mp.nint(mu[i][j]))
                    if rint != 0:
                        for k in range(mcols):
                            Bm[i][k] -= rint * Bm[j][k]
                        for k in range(j + 1):
                            mu[i][k] -= rint * mu[j][k]
                mu, bstar, Bnorm = gram_schmidt_float(Bm)
                if Bnorm[i] >= (deltaf - mu[i][i - 1] * mu[i][i - 1]) * Bnorm[i - 1]:
                    i += 1
                else:
                    Bm[i], Bm[i - 1] = Bm[i - 1], Bm[i]
                    i = max(i - 1, 1)
                    mu, bstar, Bnorm = gram_schmidt_float(Bm)
            red = Bm
        except Exception:
            red = lll_reduction(basis, delta=Fraction(3, 4))
        try:
            import sympy as sp
            x = sp.symbols('x')
            for v in red:
                H_coeffs = [int(v[L - 1 - i] * (X ** i)) for i in range(L)]
                poly = sum(H_coeffs[i] * x ** (L - 1 - i) for i in range(L))
                poly = sp.Poly(poly, x, domain=sp.ZZ)
                fac = sp.factor_list(poly)
                for base, exp in fac[1]:
                    if base.degree() == 1:
                        a, b = base.all_coeffs()
                        if a == 0:
                            continue
                        root = -b // a
                        if poly.eval(root) == 0 and 0 <= root < X:
                            return int(root)
        except ModuleNotFoundError:
            pass
    return None


def main():
    k, entries = parse_output('output.txt')
    flag = recover_flag_via_linear_combo(k, entries)
    if flag:
        print(flag)
        return
    coeffs, N = build_coeffs(k, entries)
    X = pow(256, k)
    root = small_root_hg(coeffs, N, X)
    if not root:
        print('Failed to recover flag')
        return
    print(long_to_bytes(root, k).decode(errors='replace'))


if __name__ == '__main__':
    main()

