#!/usr/bin/env python3
from pwn import remote
from Crypto.Util.number import *
from math import gcd

HOST = "78e84fc82e417a3a.chal.ctf.ae"
PORT = 443

M64 = 1 << 64
E   = 65537

def is_hex(s):
    return all(c in b"0123456789abcdef" for c in s.lower())

def bytes_to_states(b):
    return [int.from_bytes(b[i:i+8], "big") for i in range(0, len(b), 8)]

def recover_lcg_params(states):
    xs = states
    for i in range(len(xs)-2):
        x0,x1,x2 = xs[i], xs[i+1], xs[i+2]
        diff = (x1-x0) % M64
        if diff % 2 == 0:
            continue
        inv = pow(diff, -1, M64)
        a = ((x2-x1) * inv) % M64
        c = (x1 - a*x0) % M64
        ok = True
        for j in range(len(xs)-1):
            if (a*xs[j] + c) % M64 != xs[j+1]:
                ok=False
                break
        if ok:
            return a,c
    raise Exception("LCG recovery failed")

def read_line(r):
    """ Read one line safely, return stripped. """
    data = r.recvline(timeout=2)
    if not data:
        return b""
    print("[recv]", repr(data))
    return data.strip()

def read_hex_line(r):
    """ Keep reading until we see a hex token in a line. """
    while True:
        s = read_line(r)
        if not s:
            continue
        parts = s.split()
        for part in reversed(parts):
            if is_hex(part):
                print("[hex token]", part)
                return part

def read_int_line(r):
    """ Keep reading until we see a valid integer line. """
    while True:
        s = read_line(r)
        try:
            x = int(s)
            print("[int found]", x)
            return x
        except:
            pass

def main():
    print("[*] Connecting...")
    r = remote(HOST, PORT, ssl=True, sni=HOST)

    print("[*] Reading initial banner (if any)...")
    try:
        banner = r.recv(timeout=1)
        print("[banner]", repr(banner))
    except:
        print("[banner] no initial data")

    print("[*] Sending option 1")
    r.sendline(b"1")

    print("[*] Waiting for encrypted flag...")
    enc_flag_hex = read_hex_line(r)
    enc_flag = bytes.fromhex(enc_flag_hex.decode())

    print("[*] Waiting for modulus n...")
    n = read_int_line(r)

    print("[OK] Got encrypted flag:", enc_flag_hex)
    print("[OK] n =", n)

    print("[*] Sending option 2 (empty message)")
    r.sendline(b"2")
    r.sendline(b"")

    print("[*] Waiting for keystream segment...")
    seg_hex = read_hex_line(r)
    seg = bytes.fromhex(seg_hex.decode())
    states_9_12 = bytes_to_states(seg)

    print("[OK] states_9_12 =", [hex(x) for x in states_9_12])

    a,c = recover_lcg_params(states_9_12)
    print("[OK] LCG a =", hex(a), " c =", hex(c))

    states = {}
    states[9],states[10],states[11],states[12] = states_9_12
    inv_a = pow(a,-1,M64)

    for i in range(9,1,-1):
        states[i-1] = (inv_a * (states[i] - c)) % M64

    ks_flag = b''.join(states[i].to_bytes(8,'big') for i in range(1,9))
    Cflag = bytes(x^y for x,y in zip(enc_flag, ks_flag))
    Cflag_int = bytes_to_long(Cflag)

    print("[OK] Recovered Cflag")

    max_queries = 5
    start_idx = 13
    end_idx = 12 + 4 * max_queries
    for i in range(start_idx, end_idx + 1):
        states[i] = (a*states[i-1] + c) % M64

    messages = [b"2", b"3", b"5", b"7", b"11"]
    g = 1
    p = q = None

    for qi, m_bytes in enumerate(messages):
        print("[*] Querying oracle with m =", m_bytes)
        r.sendline(b"2")
        r.sendline(m_bytes)

        oracle_hex = read_hex_line(r)
        oracle_ct = bytes.fromhex(oracle_hex.decode())

        ks = b''.join(states[i].to_bytes(8,'big') for i in range(13 + 4*qi, 17 + 4*qi))
        C_p = bytes_to_long(bytes(x^y for x,y in zip(oracle_ct, ks)))
        C_n = pow(bytes_to_long(m_bytes), E, n)

        print("[OK] C_p =", C_p)
        print("[OK] C_n =", C_n)

        g = gcd((C_n - C_p) % n, n)
        if g != 1 and g != n:
            print("[OK] Nontrivial gcd found with m =", m_bytes)
            p = g
            q = n // g
            break
        else:
            print("[!!] Bad gcd with m =", m_bytes, "- trying next message")

    if p is None or q is None:
        print("[!!] Failed to factor n after all messages, aborting")
        return

    phi = (p-1)*(q-1)
    d = pow(E,-1,phi)
    M = pow(Cflag_int, d, n)
    flag = long_to_bytes(M)

    print("[FLAG]", flag.decode(errors='ignore'))
    r.close()

if __name__ == "__main__":
    main()
