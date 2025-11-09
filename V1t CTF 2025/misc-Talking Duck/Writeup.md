# V1t CTF 2025/misc-Talking Duck

Writeup for the challenge **"Talking Duck"** misc in V1t CTF 2025, playing with THEM?!

---

**Category:** Misc  
**Author:** Rawr  
**Description:**  

> Bro this duck is talking to me or something? I'm high or what??  
>
> Attachment:
> https://drive.google.com/file/d/1XOVJwPqHTZBRRUiuve8E1VwBSmMyB4Us/view?usp=sharing

**Flag Format:** v1t{*}

---

## Challenge

We received an audio clip of a duck repeatedly quacking. At first glance, it sounded random, but my instincs were telling me something different.

---

## Step 1 --- Generating the Spectrogram

Using sox, I converted the audio into a spectrogram (you can also use audacity or similar tools):

```zsh
sox duck_sound.wav -n spectrogram -o duck_spectro.png
```

The resulting image revealed evenly spaced bursts corresponding to each quack. However, unlike typical spectrogram-text challenges, no visible characters appeared. The pattern was purely rhythmic, like morse code!

<img width="944" height="591" alt="duck_spectro" src="https://github.com/user-attachments/assets/092a66cf-baff-41ee-9db0-222abd765618" />

---

## Step 2 --- Identifying the Pattern

Each quack had a consistent spacing and duration, with short and long bursts separated by pauses.

By analyzing the spectrogram columns:
- Short bursts corresponded to **dots `.`**  
- Long bursts corresponded to **dashes `-`**  
- Medium gaps separated letters  
- Large gaps separated words

After mapping those timing intervals into bits, the decoded Morse output was:

```
...- .---- -   -.. ..- -.-. -.-   ... ----- ...   ... ----- ...
```

---

## Step 3 --- Decoding Morse

Translating that Morse sequence gives:

```
v1t duck s0s s0s
```

---

## Flag

Combining the decoded text into the standard flag format:

```
v1t{DUCK_S0S_S0S}
```

---

## Notes

It's important to note that the author used `0`'s instead of `O`'s, possibly just to confuse solvers or just to partly implement [1337 (leet speech)](https://en.wikipedia.org/wiki/Leet). Granted he didnt turn other characters like `S`'s into `5`'s, which is very common in leet speech.
