#!/usr/bin/env python3
import sys
import socket
import subprocess
from typing import List, Tuple, Callable, Dict


p = 2**255 - 19


def modinv(a: int, m: int) -> int:
    return pow(a, -1, m)


def find_order_12_element() -> int:
    exp = (p - 1) // 12
    for a in range(2, 500):
        h = pow(a, exp, p)
        if h == 1:
            continue
        if pow(h, 12, p) != 1:
            continue
        if pow(h, 6, p) == 1:
            continue
        if pow(h, 4, p) == 1:
            continue
        if pow(h, 3, p) == 1:
            continue
        return h
    raise RuntimeError("Failed to find order-12 element")


def compute_E12_coeff_sums(xs: List[int], ys: List[int], g: int) -> List[int]:
    assert len(xs) == 12 and len(ys) == 12
    d = {x: y for x, y in zip(xs, ys)}
    yseq = [d[pow(g, j, p)] for j in range(12)]
    inv12 = modinv(12, p)
    E = []
    for k in range(12):
        acc = 0
        for j in range(12):
            w = pow(g, (-k * j) % (p - 1), p)
            acc = (acc + yseq[j] * w) % p
        E.append((acc * inv12) % p)
    return E


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def modinv_int(a: int, m: int) -> int:
    g, x, y = egcd(a % m, m)
    if g != 1:
        raise ZeroDivisionError("no inverse")
    return x % m


def recover_secret_from_E(E: List[int]) -> int:
    v: Dict[int, int] = {i: E[i] % p for i in range(12)}
    idxs = list(range(3, 12))
    best_secret = None

    def compute_gcd_deltas(cvals: Dict[int, int]) -> int:
        G = 0
        L = list(range(3, 11))
        m = len(L)
        for a1 in range(m - 2):
            i = L[a1]
            for a2 in range(a1 + 1, min(m - 1, a1 + 4)):
                j = L[a2]
                for a3 in range(a2 + 1, min(m, a2 + 4)):
                    k = L[a3]
                    d1 = (cvals[i + 1] - cvals[j + 1])
                    d2 = (cvals[j] - cvals[k])
                    e1 = (cvals[j + 1] - cvals[k + 1])
                    e2 = (cvals[i] - cvals[j])
                    Delta = d1 * d2 - e1 * e2
                    Delta = abs(Delta)
                    if Delta == 0:
                        continue
                    if G == 0:
                        G = Delta
                    else:
                        G = gcd(G, Delta)
        return G

    for mask in range(1 << len(idxs)):
        cvals = {}
        for i in idxs:
            bit = (mask >> (i - 3)) & 1
            cvals[i] = v[i] + (bit * p)
        G = compute_gcd_deltas(cvals)
        if G == 0:
            continue
        G = G // gcd(G, p)
        if G.bit_length() < 240:
            continue
        a_candidate = None
        ok = True
        pairs = []
        for i in range(3, 11):
            for j in range(i + 1, 11):
                num = (cvals[i + 1] - cvals[j + 1]) % G
                den = (cvals[i] - cvals[j]) % G
                if den % G == 0:
                    continue
                try:
                    aij = (num * modinv_int(den, G)) % G
                except ZeroDivisionError:
                    continue
                pairs.append(aij)
        if not pairs:
            continue
        a0 = pairs[0]
        for aij in pairs[1:10]:
            if (aij - a0) % G != 0:
                ok = False
                break
        if not ok:
            continue
        a_candidate = a0
        if gcd(a_candidate, G) != 1:
            continue
        ainv = modinv_int(a_candidate, G)
        i0 = 3
        b_candidate = (cvals[i0 + 1] - (a_candidate * cvals[i0]) % G) % G
        c2 = (ainv * (cvals[3] - b_candidate)) % G
        c1 = (ainv * (c2 - b_candidate)) % G
        c0 = (ainv * (c1 - b_candidate)) % G
        c11 = cvals[11] % G
        c12 = (a_candidate * c11 + b_candidate) % G
        c13 = (a_candidate * c12 + b_candidate) % G
        c14 = (a_candidate * c13 + b_candidate) % G
        if (c0 + c12) % p != v[0]:
            continue
        if (c1 + c13) % p != v[1]:
            continue
        if (c2 + c14) % p != v[2]:
            continue
        best_secret = c0 % p
        break

    if best_secret is None:
        raise RuntimeError("Failed to recover secret via lifting search")
    return best_secret


def run_local() -> None:
    proc = subprocess.Popen([sys.executable, "server.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def recv_line() -> str:
        assert proc.stdout is not None
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("Server closed unexpectedly")
        return line

    def send_line(s: str) -> None:
        assert proc.stdin is not None
        proc.stdin.write(s + "\n")
        proc.stdin.flush()

    _ = recv_line().strip()
    g = find_order_12_element()
    xs12 = [pow(g, j, p) for j in range(12)]
    ys12 = []
    for x in xs12:
        send_line(str(x))
        ys12.append(int(recv_line().strip()))
    E = compute_E12_coeff_sums(xs12, ys12, g)
    secret = recover_secret_from_E(E)
    print(f"Recovered SECRET: {secret}")
    for _ in range(2):
        send_line("1")
        _ = recv_line()
    send_line(str(secret))
    try:
        out = recv_line().strip()
        if out:
            print(out)
    except RuntimeError:
        pass
    proc.terminate()


def run_remote(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=10) as s:
        s_file = s.makefile('rwb', buffering=0)

        def recv_until_newline() -> str:
            data = b""
            while True:
                ch = s_file.read(1)
                if not ch:
                    break
                data += ch
                if ch == b"\n":
                    break
            return data.decode(errors='ignore')

        def recv_int_line() -> int:
            while True:
                line = recv_until_newline()
                if not line:
                    raise RuntimeError("Connection closed while waiting for int line")
                txt = line.strip()
                try:
                    return int(txt)
                except ValueError:
                    continue

        def send_line(txt: str):
            s_file.write(txt.encode() + b"\n")
            s_file.flush()

        _ = recv_until_newline()
        g = find_order_12_element()
        xs12 = [pow(g, j, p) for j in range(12)]
        ys12 = []
        for x in xs12:
            send_line(str(x))
            ys12.append(int(recv_int_line()))
        E = compute_E12_coeff_sums(xs12, ys12, g)
        secret = recover_secret_from_E(E)
        print(f"Recovered SECRET: {secret}")
        for _ in range(2):
            send_line("1")
            _ = recv_int_line()
        send_line(str(secret))
        while True:
            line = recv_until_newline()
            if not line:
                break
            print(line.strip())


def main():
    if len(sys.argv) == 1 or sys.argv[1] == "--local":
        run_local()
    elif sys.argv[1] == "--remote":
        host = "ssssp.challs.sekai.team"
        port = 1337
        run_remote(host, port)
    else:
        print("Usage: solver.py [--local|--remote]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
