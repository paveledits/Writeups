# NNSCTF 2025/rev-breaker

Writeup for the Challenge "breaker" rev category in NNSCTF 2025 playing
with THEM?!

------------------------------------------------------------------------

**Category:** Rev

**Author:** fantomet

**Description:** Did you know that "breaking" a program can mean more
than one thing? GDB certainly has its own idea of what that means.
Unfortunately, a cat ran across my keyboard in the middle of debugging,
and now everything looks like nonsense. Can you make sense of the chaos
and recover the flag?

**Flag Format:** NNS{*}

## Challenge

We are given a binary inside `breaker.tar.gz`.\
The binary copies two arrays from `.rodata` and runs a loop:

    c[i] = A[i] ^ B[i % 77]

The result is the flag, but it is sent to a dummy function and never
printed.

------------------------------------------------------------------------

## Step 1 --- First thoughts

The challenge mentions GDB "chaos", but looking at the disassembly shows
a clear XOR loop.\
The task is to dump the arrays from `.rodata` and reconstruct the flag.

------------------------------------------------------------------------

## Step 2 --- Recovering the arrays

From the binary:

-   `A` has 90 integers\
-   `B` has 77 integers

The flag is produced by XORing `A[i]` with `B[i % 77]`.

------------------------------------------------------------------------

## Step 3 --- Exploit script

``` python
import struct

bin_path = "rev"
RODATA_VADDR  = 0x473000
RODATA_OFFSET = 0x73000

A_VADDR = 0x4731a0
B_VADDR = 0x473320

with open(bin_path, "rb") as f:
    f.seek(RODATA_OFFSET + (A_VADDR - RODATA_VADDR))
    A = list(struct.unpack("<90i", f.read(90*4)))

    f.seek(RODATA_OFFSET + (B_VADDR - RODATA_VADDR))
    B = list(struct.unpack("<76i", f.read(76*4)))
    f.seek(RODATA_OFFSET + (B_VADDR - RODATA_VADDR) + 76*4)
    B.append(struct.unpack("<i", f.read(4))[0])

C = [A[i] ^ B[i % 77] for i in range(90)]
s = bytes(c & 0xff for c in C).decode("latin1")
print(s.split("}")[0] + "}")
```

------------------------------------------------------------------------

## Step 4 --- Result

Running the script gives:

    NNS{moves_like_jagger_but_rev}

------------------------------------------------------------------------

## Flag

    NNS{moves_like_jagger_but_rev}

------------------------------------------------------------------------

## Notes

At first I thought the challenge wanted some GDB trickery because of the
description, but it turned out much simpler.\
It was basically just about noticing the XOR loop and grabbing the data
from `.rodata`. Once the arrays were dumped, the flag fell out right
away. Pretty fun warm‑up style reversing task.

