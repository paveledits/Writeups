# PwnSec CTF 2025/crypto-Opera

Writeup for the Challenge "Opera" crypto category in PwnSec CTF 2025 playing  
with The Hackers Elite Movement

------------------------------------------------------------------------

**Category:** Crypto  
**Author:** solaire  
**Description:** Writer was too lazy to write a description, so here's this video: https://www.youtube.com/watch?v=lVlgMEFu1PI  
**Flag Format:** flag{*}

## Challenge

We are given a TCP-based challenge running on port 443. There is no web UI, only a raw socket service. Upon connecting, the server prints a banner and then shows this menu:

```
1) get encrypted flag
2) encrypt your input
3) exit
```

Option 1 returns:
- The encrypted flag (RSA ciphertext, 64 bytes, hex encoded)
- The RSA modulus n

Option 2 is an encryption oracle, but incorrectly encrypts under **p** (one of the RSA primes) instead of **n**, then XORs the result with bytes from a 64-bit LCG keystream.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

Initial observations:

- The encrypted flag is `RSA(flag)` XOR `LCG_stream`.
- The oracle returns `(m^e mod p)` XOR new LCG output.
- If the LCG keystream is recovered, then the flag ciphertext can be unmasked.
- If `(m^e mod p)` can be obtained in the clear, it can be combined with `(m^e mod n)` to factor n.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

### Breaking the LCG
Sending an empty message to option 2 results in the oracle computing `0^e mod p = 0`, so the returned bytes are pure LCG output. From four consecutive 64-bit outputs, the LCG parameters `a` and `c` can be solved by exploiting:

```
x1 = a*x0 + c mod 2^64
x2 = a*x1 + c mod 2^64
```

Once `a` and `c` are known, the LCG state can be rewound to recover the keystream used for the encrypted flag and fast-forwarded for subsequent oracle calls.

### Using the Oracle to Factor n
For a chosen small plaintext m, we compute:

- `C_p = m^e mod p` (from oracle after XOR removal)
- `C_n = m^e mod n` (computed locally)

Since `p | (C_n - C_p)`, we compute:

```
g = gcd(C_n - C_p, n) = p
```

If gcd fails (returns 1 or n), another plaintext (e.g., 2, 3, 5, 7, 11) is tried.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

The solve process:

1. Connect to the server using TLS with SNI.
2. Choose option 1 to retrieve encrypted flag and n.
3. Choose option 2 with an empty message to extract LCG outputs and recover LCG parameters.
4. Reconstruct the flag keystream and unmask `RSA(flag)`.
5. Query the oracle with several small messages m. For each:
   - Recover `C_p` by removing the correct keystream.
   - Compute `C_n` locally.
   - Attempt `g = gcd(C_n - C_p, n)`.
   - Stop when a nontrivial gcd is found.
6. Recover p, compute q, derive the private key, and decrypt `RSA(flag)`.
7. Retrieve the final flag.

------------------------------------------------------------------------

## Additional Notes Before Flag

The full exploit script used for solving this challenge is included in the **same directory** as this writeup. The challenge uses a **dynamic flag implementation**, meaning each instance generates its own flag.

## Flag

```
flag{95d02b85d6216ae3}
```

------------------------------------------------------------------------

## Notes

- The full exploit script is included in the **same directory** as this writeup.
- The challenge uses a **dynamic flag implementation**, so each deployed instance produces a different flag.


- The challenge mixes RSA mis-implementation with a reversible XOR-based LCG stream.
- The TLS/SNI requirement is necessary to avoid the 400 HTTP frontend.
- One empty oracle query completely breaks the LCG.
- One correct gcd computation fully factors n.

