#!/usr/bin/env python3

from ast import literal_eval
import hashlib
import os
import shutil
import subprocess
import sympy as sp

from protocol import mine

try:
    from sage.all import Matrix, PolynomialRing, ZZ
except ModuleNotFoundError:
    if os.environ.get("CRYPTO_PLANE_REEXEC") == "1":
        raise
    sage = shutil.which("sage")
    if not sage:
        raise SystemExit("Sage is required to run solve.py")
    env = dict(os.environ)
    env["CRYPTO_PLANE_REEXEC"] = "1"
    raise SystemExit(subprocess.run([sage, "-python", __file__], env=env).returncode)


T = sp.Symbol("t", real=True, positive=True)


def parse_public_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        lines = [line.strip() for line in handle if line.strip()]

    return {
        "alice_pub": literal_eval(lines[0].split(": ", 1)[1]),
        "bob_pub": literal_eval(lines[1].split(": ", 1)[1]),
        "public_info": literal_eval(lines[2].split(": ", 1)[1]),
        "ciphertext": bytes.fromhex(lines[3].split(": ", 1)[1]),
    }


def normalized_invariant(point):
    ring = PolynomialRing(ZZ, "u")
    u = ring.gen()
    rows = mine(point)

    shifted_rows = []
    for row in rows:
        shift = max(0, -min(row))
        shifted_rows.append([u ** (value + shift) for value in row])

    matrix = Matrix(ring, shifted_rows)
    numerator = matrix.det()
    quotient, remainder = numerator.quo_rem((u - 1) ** (len(point[0]) - 1))
    if remainder != 0:
        raise ValueError("Invariant division failed")

    expr = 0
    for degree, coeff in quotient.dict().items():
        expr += int(coeff) * T ** (quotient.degree() - degree)
    expr = sp.expand(expr)
    if sp.Poly(expr, T).coeff_monomial(T**0) < 0:
        expr = -expr
    return expr


def xor_decrypt(ciphertext, shared_secret_hex):
    key = bytes.fromhex(shared_secret_hex)
    while len(key) < len(ciphertext):
        key += hashlib.sha256(key).digest()
    return bytes(a ^ b for a, b in zip(ciphertext, key))


def main():
    data = parse_public_file("public.txt")

    alice_pub = normalized_invariant(data["alice_pub"])
    bob_pub = normalized_invariant(data["bob_pub"])
    public_info = normalized_invariant(data["public_info"])

    shared_poly, remainder = sp.div(
        sp.Poly(sp.expand(alice_pub * bob_pub), T),
        sp.Poly(public_info, T),
    )
    if remainder != 0:
        raise ValueError("Shared polynomial is not integral")

    shared_poly = shared_poly.as_expr()
    shared_secret = hashlib.sha256(str(shared_poly).encode()).hexdigest()
    plaintext = xor_decrypt(data["ciphertext"], shared_secret).decode()

    print(f"Shared polynomial: {shared_poly}")
    print(f"Shared secret: {shared_secret}")
    print(f"Flag: {plaintext}")


if __name__ == "__main__":
    main()
