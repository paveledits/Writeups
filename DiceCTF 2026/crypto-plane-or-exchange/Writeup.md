# DiceCTF 2026/crypto-plane-or-exchange

Writeup for the challenge "plane-or-exchange" [crypto] in DiceCTF 2026 playing with THEM?!

------------------------------------------------------------------------

**Category:** Crypto </br>
**Author:** AdnanSlef </br>
**Description:** Alice and Bob had a brief exchange, and now they know something which I do not. Would you please help me to drop some Eves? </br>
**Flag Format:** `dice{*}`

## Challenge

The challenge shipped two files packed in an [archive](https://github.com/paveledits/Writeups/blob/main/DiceCTF%202026/crypto-plane-or-exchange/crypto_plane-or-exchange.tar.gz):

- `protocol.py`
- `public.txt`

`protocol.py` implements a custom key exchange built on pairs of permutations. The public data looked like this:

- Alice's public key
- Bob's public key
- shared public info
- ciphertext

The important part of the protocol was:

- `derive_public_key(my_priv, public_info) = scramble(connect(public_info, my_priv), 1000)`
- `derive_shared_secret(my_priv, their_pub) = sha256(str(normalize(calculate(connect(my_priv, their_pub))))).hexdigest()`

So the whole challenge comes down to this question:

Can we compute the same `normalize(calculate(...))` value that Alice and Bob hash, using only public data?

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

My first pass was just reading the protocol and separating the real math from the noise.

The noisy part is `scramble()`. It repeatedly applies:

- `slide1`
- `slide2`
- `shuffle`

Those functions only rearrange the representation. They do not feed directly into the hash. The thing that actually matters is this invariant-looking pipeline:

```python
normalize(calculate(point))
```

`calculate()` builds a determinant from a matrix made out of `mine(point)`, and then `normalize()` removes powers of `t` and fixes the sign. That already looks like the challenge is hiding some kind of knot or grid-diagram invariant.

At that point, the attack direction became:

1. Understand what `scramble()` preserves.
2. Understand how `connect()` changes the invariant.
3. Express the shared secret in terms of public values only.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

The key observation is that `scramble()` is not creating new information. It is just applying allowed moves to the same underlying object. Since the shared secret is based on `normalize(calculate(...))`, the public keys only matter through that normalized polynomial.

So define:

```
I(X) = normalize(calculate(X))
```

Then the protocol becomes much easier to read.

Because the public key is built as:

```
PubA = scramble(connect(PublicInfo, PrivA))
PubB = scramble(connect(PublicInfo, PrivB))
```

and `scramble()` preserves the invariant, we get:

```
I(PubA) = I(connect(PublicInfo, PrivA))
I(PubB) = I(connect(PublicInfo, PrivB))
```

The next useful fact is that `connect()` behaves multiplicatively on this invariant. In other words:

```
I(connect(X, Y)) = I(X) * I(Y)
```

That gives:

```
I(PubA) = I(PublicInfo) * I(PrivA)
I(PubB) = I(PublicInfo) * I(PrivB)
```

Now look at the value that Alice hashes:

```
I(connect(PrivA, PubB))
```

Using multiplicativity again:

```
I(connect(PrivA, PubB)) = I(PrivA) * I(PubB)
                        = I(PrivA) * I(PublicInfo) * I(PrivB)
```

But from the two public keys we also have:

```
I(PubA) * I(PubB) / I(PublicInfo)
= [I(PublicInfo) * I(PrivA)] * [I(PublicInfo) * I(PrivB)] / I(PublicInfo)
= I(PublicInfo) * I(PrivA) * I(PrivB)
```

That is exactly the same value.

So we do not need either private key at all.

The final exploit is:

```
shared_poly = I(AlicePub) * I(BobPub) / I(PublicInfo)
shared_secret = sha256(str(shared_poly)).hexdigest()
plaintext = ciphertext XOR expanded_key
```

The only practical issue is speed. Computing the determinant directly with Sympy for the larger public keys is slow. I used Sage's exact polynomial arithmetic for the determinant step and then converted the result back into the same normalized `sympy` form that the challenge hashes.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

Now run the final [solver](https://github.com/paveledits/Writeups/blob/main/DiceCTF%202026/crypto-plane-or-exchange/solve.py):

`python3 solve.py`

Running it gives:

```
Shared polynomial: 2*t**22 - 31*t**21 + 234*t**20 - 1136*t**19 + 3959*t**18 - 10514*t**17 + 22120*t**16 - 37997*t**15 + 54813*t**14 - 68477*t**13 + 76653*t**12 - 79253*t**11 + 76653*t**10 - 68477*t**9 + 54813*t**8 - 37997*t**7 + 22120*t**6 - 10514*t**5 + 3959*t**4 - 1136*t**3 + 234*t**2 - 31*t + 2
Shared secret: 4ce5bc3bb44ed4018cae38ffcda94bc08b85d79f0e71a012a74549c82ac91a82
Flag: dice{plane_or_planar_my_w0rds_4r3_411_knotted_up}
```

---

## Flag

```
dice{plane_or_planar_my_w0rds_4r3_411_knotted_up}
```

---

## Notes

The intended mistake is not weak randomness or bad XOR usage by itself. The real bug is that the protocol exposes a public invariant that survives scrambling and composes multiplicatively under `connect()`. Once that happens, the shared secret stops being private, because it can be reconstructed from the two public keys and the shared public info.

The exploit is:

```
I(AlicePub), I(BobPub), I(PublicInfo)
shared_poly = I(AlicePub) * I(BobPub) / I(PublicInfo)
shared_secret = sha256(str(shared_poly))
```

Pretty easy challenge overall, but def fun.
