#!/usr/bin/env python3


from __future__ import annotations

from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from sage.all import CyclotomicField, Matrix, ZZ, GF, matrix 

from fpylll import FPLLL, GSO, IntegerMatrix, LLL


def parse_output(path: str = "output.txt"):
    n = 128
    K = CyclotomicField(2 * n, "zeta256")
    zeta256 = K.gen()

    scope = {"zeta256": zeta256}
    lines = open(path, "r").read().splitlines()
    exec(lines[0], {}, scope)  
    exec(lines[1], {}, scope)  
    exec(lines[2].replace("^", "**"), {}, scope)  
    exec(lines[3].replace("^", "**"), {}, scope)  

    iv = bytes.fromhex(scope["iv"])
    enc = bytes.fromhex(scope["enc"])
    q0, q1, q2 = scope["q0"], scope["q1"], scope["q2"]
    s0, s1, s2 = scope["s0"], scope["s1"], scope["s2"]
    return K, zeta256, iv, enc, q0, q1, q2, s0, s1, s2


def coeff_vec(a, n: int):
    v = list(a)
    if len(v) < n:
        v += [0] * (n - len(v))
    return [ZZ(c) for c in v]


def conj_coeff(v):
    n = len(v)
    w = [ZZ(0)] * n
    w[0] = v[0]
    for j in range(1, n):
        w[j] = -v[n - j]
    return w


def mul_mat(p):
    n = len(p)
    M = Matrix(ZZ, n, n)
    for j in range(n):
        for i in range(n):
            if i >= j:
                M[i, j] = p[i - j]
            else:
                M[i, j] = -p[n + i - j]
    return M


def conj_mat(n: int):
    C = Matrix(ZZ, n, n)
    C[0, 0] = 1
    for j in range(1, n):
        C[j, n - j] = -1
    return C


def set_block(A, rblk: int, cblk: int, M, n: int):
    A[rblk * n : (rblk + 1) * n, cblk * n : (cblk + 1) * n] = M


def build_system(q0, q1, q2, s0, s1, s2, n: int):
    Mq0 = mul_mat(coeff_vec(q0, n))
    Mq1 = mul_mat(coeff_vec(q1, n))
    Mq2 = mul_mat(coeff_vec(q2, n))
    Mq1b = mul_mat(conj_coeff(coeff_vec(q1, n)))

    Ms0 = mul_mat(coeff_vec(s0, n))
    Ms1 = mul_mat(coeff_vec(s1, n))
    Ms2 = mul_mat(coeff_vec(s2, n))
    Ms1b = mul_mat(conj_coeff(coeff_vec(s1, n)))

    C = conj_mat(n)

    A = Matrix(ZZ, 8 * n, 4 * n)

    set_block(A, 0, 0, Mq1, n)
    set_block(A, 0, 1, -C, n)
    set_block(A, 0, 2, -Mq0, n)

    set_block(A, 1, 0, C, n)
    set_block(A, 1, 1, Mq1, n)
    set_block(A, 1, 3, -Mq0, n)

    set_block(A, 2, 0, -Mq2, n)
    set_block(A, 2, 2, Mq1b, n)
    set_block(A, 2, 3, C, n)

    set_block(A, 3, 1, -Mq2, n)
    set_block(A, 3, 2, -C, n)
    set_block(A, 3, 3, Mq1b, n)

    set_block(A, 4, 0, Ms2, n)
    set_block(A, 4, 1, -Ms1, n)
    set_block(A, 4, 3, -C, n)

    set_block(A, 5, 0, -Ms1b, n)
    set_block(A, 5, 1, Ms0, n)
    set_block(A, 5, 2, C, n)

    set_block(A, 6, 1, C, n)
    set_block(A, 6, 2, Ms2, n)
    set_block(A, 6, 3, -Ms1, n)

    set_block(A, 7, 0, -C, n)
    set_block(A, 7, 2, -Ms1b, n)
    set_block(A, 7, 3, Ms0, n)

    return A


def decrypt(iv: bytes, enc: bytes, sk):
    key = sha256(str(sk).encode()).digest()
    cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
    return unpad(cipher.decrypt(enc), 16)


def main():
    n = 128
    K, z, iv, enc, q0, q1, q2, s0, s1, s2 = parse_output()

    print("[+] Building linear system A (1024 x 512)...")
    A = build_system(q0, q1, q2, s0, s1, s2, n)

    p = 1000003
    r = Matrix(GF(p), A).rank()
    print(f"[+] rank(A) mod {p}: {r}  (nullity={4*n - r})")

    print("[+] Computing integer right kernel basis...")
    Kmat = A.right_kernel_matrix(algorithm="flint", basis="computed")
    print(f"[+] kernel basis shape: {Kmat.nrows()} x {Kmat.ncols()}")

    print("[+] LLL-reducing kernel basis (mpfr, prec=250)...")
    FPLLL.set_precision(250)
    IM = IntegerMatrix.from_matrix(Kmat)
    M = GSO.Mat(IM, float_type="mpfr")
    M.update_gso()
    LLL.Reduction(M)()

    q0_const = int(q0[0])
    q2_const = int(q2[0])

    print("[+] Scanning reduced basis for (||f||^2+||g||^2, ||F||^2+||G||^2) match...")
    for i in range(IM.nrows):
        row = [int(IM[i, j]) for j in range(IM.ncols)]
        if all(x == 0 for x in row):
            continue

        f_vec = row[0:n]
        g_vec = row[n : 2 * n]
        F_vec = row[2 * n : 3 * n]
        G_vec = row[3 * n : 4 * n]

        nf = sum(x * x for x in f_vec) + sum(x * x for x in g_vec)
        nF = sum(x * x for x in F_vec) + sum(x * x for x in G_vec)
        if nf != q0_const or nF != q2_const:
            continue

        f = K(f_vec)
        g = K(g_vec)
        F = K(F_vec)
        G = K(G_vec)

        B = matrix([[f, F], [g, G]])
        if (B.H * B)[0, 0] != q0 or (B.H * B)[0, 1] != q1 or (B.H * B)[1, 1] != q2:
            continue
        if (B * B.H)[0, 0] != s0 or (B * B.H)[0, 1] != s1 or (B * B.H)[1, 1] != s2:
            continue

        print(f"[+] Found basis at row {i+1}")
        print("[+] det(B)==1:", (f * G - g * F) == 1)

        for k in range(256):
            u = z ** k
            sk = (f * u, g * u, F * u, G * u)
            try:
                pt = decrypt(iv, enc, sk)
            except Exception:
                continue
            print(f"[+] root-of-unity k={k}")
            print("[+] PLAINTEXT:", pt)
            try:
                print("[+] FLAG:", pt.decode())
            except Exception:
                pass
            return 0

    print("[-] No valid secret found (unexpected).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

