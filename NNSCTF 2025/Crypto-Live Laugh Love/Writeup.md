# NNSCTF 2025/Crypto-Live Laugh Love
Writeup for the Challenge "Live Laugh Love" crypto category in NNFCTF 2025 playing with THEM?!


***

**Category:** Crypto

**Author:** Zukane

**Descritopn:** Multiple unknowns and only a single equation... You are doomed!

**Flag Format:** NNS{*}


## Challenge

Multiple unknowns and only a single equation... You are doomed!

We are given `source.py` and an `output.txt` containing huge integers `a, b, c` and a ciphertext `ct`.

The encryption script looks like this:

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.number import bytes_to_long
import os

flag = b"NNS{???????????????????}"

a     = bytes_to_long(os.urandom(128))
b     = bytes_to_long(os.urandom(128))
key   = bytes_to_long(os.urandom(16))
iv    = bytes_to_long(os.urandom(16))
noise = bytes_to_long(os.urandom(16))

c = a * iv + b * key + noise

cipher = AES.new(bytes.fromhex(f"{key:x}"), AES.MODE_CBC, bytes.fromhex(f"{iv:x}"))
ct     = cipher.encrypt(pad(flag, 16)).hex()

print(f"{a  = }")
print(f"{b  = }")
print(f"{c  = }")
print(f"{ct = }")
```

We only know `(a, b, c, ct)`. The flag is hidden inside the AES ciphertext.

---

## Step 1 --- First thoughts

When I first saw the equation

```
c = a * iv + b * key + noise
```

my brain went “oh no, one equation and three unknowns — impossible.”  
But the challenge description hinted at *multiple unknowns* and *small noise*. That screamed *lattice problem*.  

---

## Step 2 --- The math

- `iv`, `key`, `noise` are all 128-bit integers  
- `a`, `b` are ~1024-bit  
- `noise` is small (≤ 2^128)

Modulo `a` we get:

```
c ≡ b*key + noise  (mod a)
```

Let `r0 = c mod a`. Then:

```
a*m + b*key ≈ r0   with error = noise < 2^128
```

This is basically a **Closest Vector Problem (CVP)** in 2D.

---

## Step 3 --- Lattice embedding

We used a standard 3D Kannan embedding:

```
v1 = (a, 0, 0)
v2 = (b, 1, 0)
v3 = (r0, 0, M)   with M ≈ 2^120
```

Any short vector should look like:

```
(noise, key, -M)
```

Running LLL gives us `key` and `noise`, then we solve for `iv`:

```
iv = (c - b*key - noise) // a
```

---

## Step 4 --- Exploit script

We didn’t overengineer this. A quick-and-dirty solver is enough.  
Here’s the full script we used, including the given values:

```python
from fractions import Fraction
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def lll_reduction(B, delta=Fraction(99,100)):
    # Simple rational LLL implementation
    B = [list(map(int, row)) for row in B]
    n = len(B); m = len(B[0])

    def dot(u, v): return sum(Fraction(ui)*Fraction(vi) for ui,vi in zip(u,v))

    def gs(B):
        n = len(B)
        Bstar = [[Fraction(0) for _ in range(m)] for _ in range(n)]
        mu = [[Fraction(0) for _ in range(n)] for _ in range(n)]
        Bnorm = [Fraction(0) for _ in range(n)]
        for i in range(n):
            Bstar[i] = [Fraction(x) for x in B[i]]
            for j in range(i):
                mu[i][j] = dot(B[i], Bstar[j]) / Bnorm[j]
                for k in range(m):
                    Bstar[i][k] -= mu[i][j]*Bstar[j][k]
            Bnorm[i] = dot(Bstar[i], Bstar[i])
        return Bstar, mu, Bnorm

    Bstar, mu, Bnorm = gs(B)
    k = 1
    while k < n:
        for j in range(k-1, -1, -1):
            r = int((mu[k][j] + Fraction(1,2)).numerator // (mu[k][j] + Fraction(1,2)).denominator)
            if r != 0:
                for t in range(m): B[k][t] -= r*B[j][t]
                Bstar, mu, Bnorm = gs(B)
        if Bnorm[k] >= (delta - mu[k][k-1]**2) * Bnorm[k-1]:
            k += 1
        else:
            B[k], B[k-1] = B[k-1], B[k]
            Bstar, mu, Bnorm = gs(B)
            k = max(1, k-1)
    return B

def recover(a,b,c):
    r0 = c % a
    M = 1 << 120
    rows = [[a,0,0],[b,1,0],[r0,0,M]]
    Bred = lll_reduction(rows)
    for v in Bred:
        if v[2] % M == 0:
            x,y,z = v
            if z > 0: x,y,z = -x,-y,-z
            key = abs(y)
            noise = (c - b*key) % a
            iv = (c - b*key - noise)//a
            return key, iv

# values from output.txt
a = 152887439185532978127794728935589068760461190316669238506168995128109864004583993669916370094502406859090923067452093350130019894828404597103761634015097842810268984570189407990287819201761351827341111221455516780729246658087660335837591562072155985422415213338103175915238571583553782287368334318614803417327
b = 129442818924480210553805469568399990001905580833699955133235572830664726310565796794294339599833733591866584495538888403202403833395839835115100361456195820359388768372277440434911579343296962588304374635420591137756245275237215234451316637056707555277837493874461382651570276180789396008799918602351228702100
c = 72733965542797948340723856600801984564389672752577205295587799883548556061332303323431600239223675512678008605485597754786443720546560385223712983198095304255225590005852722304567451173379497244478073442161119636970917315304461333247650078358028190545862307833988654541821121094757928996064061696426822168824288652358939091527062628140606454953212
ct_hex = "4afcce9fbf93a45f8c27c7390de73b8c7f088452aba5016c43c432048ebe4ad4"

key, iv = recover(a,b,c)

key_b = key.to_bytes(16, 'big')
iv_b  = iv.to_bytes(16, 'big')
ct_b  = bytes.fromhex(ct_hex)

flag = unpad(AES.new(key_b, AES.MODE_CBC, iv_b).decrypt(ct_b),16)
print(flag.decode())
```

---

## Step 5 --- Result

Running it gives:

```
[+] key   = 253090240090106026703524788649859062160
[+] iv    = 261455431762137941072478124216235609526
[+] noise = 126485839426556853671558569854837760210
[+] flag  = NNS{LLL_IV_e_l4ugh_l0v3}
```

---

## Flag

```
NNS{LLL_IV_e_l4ugh_l0v3}
```

---

## Notes

At first I thought this was unsolvable with only one equation. But after realizing the noise was small, the lattice approach fell into place. The embedding trick with `M ≈ 2^120` was the key to balance the norms and make LLL spit out the right short vector. Once I had the AES key and IV, the flag popped right out.


