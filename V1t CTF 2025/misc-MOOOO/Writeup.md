# V1t CTF 2025/misc-MOOOO

Writeup for the Challenge "MOOOO" misc category in V1t CTF 2025 playing  
with THEM?!

------------------------------------------------------------------------

**Category:** misc  
**Description:** I really like **Cows **  
**Flag Format:** v1t{*}

## Challenge

I Ire given a single JPEG file named `MOOOO.jpeg` along with a short description.  
The title and description hinted at something related to the word **MOO**

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

Starting with a quick metadata and structure inspection:

```zsh
file MOOOO.jpeg
exiftool MOOOO.jpeg
strings MOOOO.jpeg | less
binwalk MOOOO.jpeg
```

`exiftool` and `strings` revealed an unusual **Comment** field filled with long repeating `MOO`, `moO`, and similar patterns, clearly not human text. The content looked identical to source code in the **COW esolang**, which uses only variations of the word "moo" for instructions.

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

Since the JPEG comment looked like COW code, I ran it through an online **COW interpreter** (any standard COW interpreter or online tool would do). When executed, the output was:

```
thismaybeapasswordbutwhoreallyknowsimjustmessginitisapassword
```

That output was a **steganography password**.

Next, I tried extracting hidden data from the JPEG using **steghide**:

```bash
steghide extract -sf MOOOO.jpeg -p 'thismaybeapasswordbutwhoreallyknowsimjustmessginitisapassword'
```

The extraction succeeded, producing a ZIP archive named `secret.zip`.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

After unzipping `secret.zip`, I found two files: `extract.txt` and `TRYYY.txt`.

`extract.txt` just said:
```
TRY HARDERRR
```
which served as a hint to dig deeper.

The second file, `TRYYY.txt`, contained only spaces and tabs which is a strong indicator of **whitespace steganography**.

To confirm, I used **stegsnow**:

```bash
sudo apt install -y stegsnow
stegsnow -C TRYYY.txt
```

That command revealed the final flag:

```
v1t{D0wn_Th3_St3gN0_R4bb1t_H0l3}
```

------------------------------------------------------------------------

## Flag

```
v1t{D0wn_Th3_St3gN0_R4bb1t_H0l3}
```

------------------------------------------------------------------------

## Notes

The challenge combined **esoteric language decoding (COW)** with **classic image steganography (steghide)** and **whitespace stego (SNOW)**.
