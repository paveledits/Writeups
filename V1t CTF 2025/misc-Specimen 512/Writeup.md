# V1t CTF 2025/misc-Specimen 512

Writeup for the Challenge "Specimen 512" misc category in V1t CTF 2025 playing
with THEM?!

------------------------------------------------------------------------

**Category:** misc  
**Author:** Shah Ji  
**Description:** An unmarked data file was recovered from an abandoned research server labeled only as **Specimen 512**. No accompanying documentation, no metadata, and no obvious contents — just a massive file filled with strange sequences. Some say it hides a _secret_

**Flag Format:** v1t{*}

------------------------------------------------------------------------

## Challenge

We received a single archive: `Specimen_512.zip`.  
Inside was only one file, `Specimen_512.fasta`, a 5 MB text full of A/C/G/T sequences and a few comment lines such as:

```
; hint: encoding=base64->triplet-codon (lexicographic AAA..TTT => b64 idx 0..63)
; pad_count=2  ; note: base64 padding removed from stream
```

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

Opening the FASTA revealed it wasn’t biological data but an encoded stream.  
The comments clearly hinted that each DNA triplet (AAA, AAC, … TTT) represents one Base64 index from 0 to 63.  
So decoding meant mapping 64 possible codons -> the standard Base64 alphabet.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

I wrote a short Python script to:
1. Concatenate all A/C/G/T lines.  
2. Split into triplets.  
3. Map each triplet lexicographically (A,C,G,T) to its Base64 character.  
4. Append the missing padding (`==`) per the hint and Base64-decode the result.

That produced a ~1.3 MB binary blob.  
Hex inspection showed high entropy, but at offset 534288 the magic bytes `PK 03 04` appeared, a ZIP signature.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

I carved the embedded ZIP starting at that offset and opened it:

```python
from itertools import product
import base64, zipfile

# build codon->b64 map
alphabet = ['A','C','G','T']
codons = [''.join(p) for p in product(alphabet, repeat=3)]
b64alp = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
codon_map = dict(zip(codons, b64alp))

# read sequence
seq = ''.join(l.strip() for l in open("Specimen_512.fasta") if not l.startswith((">", ";")))
b64 = ''.join(codon_map[seq[i:i+3]] for i in range(0,len(seq)-2,3))
decoded = base64.b64decode(b64 + "==")

# extract embedded zip
start = decoded.find(b"PK\x03\x04")
end   = decoded.find(b"PK\x05\x06", start)
open("inner.zip","wb").write(decoded[start:end+22])

with zipfile.ZipFile("inner.zip") as z:
    z.extractall(".")
```

Inside `inner.zip` were:

```
flag.txt
readme.txt
```

`flag.txt` contained the solution.

---

## Flag

```
v1t{30877432d1026706d7e805da846a32c3}
```

---

## Notes

- The comment lines inside FASTA provided every hint needed, no brute-forcing.  
- Entropy ≈ 2 for DNA (typical GC ratio) vs ≈ 8 for decoded blob -> confirmed compression/encryption.  
- A clean example of multi-layer encoding: DNA -> Base64 -> ZIP -> flag.

