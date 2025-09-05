# NNSCTF 2025/Crypto-Live Laugh Love
Writeup for the Challenge "Live Laugh Love" crypto category in NNFCTF 2025


***

**Category:** Crypto

**Author:** Zukane

**Descritopn:** Multiple unknowns and only a single equation... You are doomed!

**Flag Format:** NNS{*}


## Challenge

We are given `source.py` and an `output.txt` containing huge integers `a, b, c` and a ciphertext `ct`.

The encryption script looks like this:

```python
a     = bytes_to_long(os.urandom(128))
b     = bytes_to_long(os.urandom(128))
key   = bytes_to_long(os.urandom(16))
iv    = bytes_to_long(os.urandom(16))
noise = bytes_to_long(os.urandom(16))

c = a * iv + b * key + noise

cipher = AES.new(bytes.fromhex(f"{key:x}"), AES.MODE_CBC, bytes.fromhex(f"{iv:x}"))
ct     = cipher.encrypt(pad(flag, 16)).hex()
```

We only know `a, b, c, ct`. The flag is hidden inside the AES ciphertext.


### Step 1 — The math

The relation is:

