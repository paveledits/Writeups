# V1T CTF 2025/rev-Duck RPG

Writeup for the Challenge "Duck RPG" rev category in V1T CTF 2025 playing  
with THEM?!

------------------------------------------------------------------------

**Category:** Reverse Engineering  
**Description:** Can you patch the batch to get the secret ending of the game ?
**Flag Format:** v1t{*}

## Challenge

We received a zip archive named `duck_rpg.zip` containing two batch scripts: `game.bat` and `result.bat`. Running `game.bat` starts a small text-based RPG battle, while the mysterious `result.bat` is called at the end to display something based on the hash of the main script.

------------------------------------------------------------------------

## Step 1 --- Initial Analysis

Looking at `game.bat`, the game logic defines three battles (`Angry Duck`, `Duck Mage`, `Mother Goose`) and sets fragments `frag1`, `frag2`, and `frag3` to words that combine into a keyword. The final section calls:

```bat
call result.bat !full! !hash!
```

The `result.bat` file is heavily obfuscated with weird `%Bc:~x,1%` indexing expressions, which reconstruct hidden text using the variable `Bc` defined as:

```
@1lYWZUrksK9Mwxd2PLGypH68fOStF4Abaq3zXDeuJNRc Bo7h0gvni5IjmCTQVE
```

------------------------------------------------------------------------

## Step 2 --- Digging Deeper

To see what `result.bat` actually prints, I extracted all those `%Bc:~x,1%` indices and rebuilt them using a small Python script. The decoded sections showed multiple conditional blocks checking the first argument:

- `if "%~1"=="unlocktheduck"` → echoes one message
- `if "%~1"=="unlockthegoose"` → echoes another

The `unlockthegoose` branch simply printed a joke: *"Well that was fun but there no flag here"*.

But the `unlocktheduck` branch revealed something far more interesting:

```
echo v1tp4tchth3b4tcht0g3tth3s3cr3t3nd1ng
```

So the secret ending wasn’t part of normal gameplay, it was hidden in a branch never reached naturally.

------------------------------------------------------------------------

## Step 3 --- Exploit / Solution

We could trigger the hidden branch manually by modifying the start of `game.bat` to call it directly:

```bat
call result.bat unlocktheduck
```

Once executed, the batch printed:

```
v1tp4tchth3b4tcht0g3tth3s3cr3t3nd1ng
```

This looked like a leetspeak phrase for the flag. After normalizing it with underscores, the final flag became:

```
v1t{p4tch_th3_b4tch_t0_g3t_th3_s3cr3t_3nd1ng}
```

---

## Flag

```
v1t{p4tch_th3_b4tch_t0_g3t_th3_s3cr3t_3nd1ng}
```

---

## Notes

- Obfuscated batch challenges can often hide printable text using character slicing with environment variables.
- It’s safer to decode statically instead of running them directly, as they might execute arbitrary commands.
- The challenge title and the echo line nicely hint at the method: *patch the batch to get the secret ending!*

