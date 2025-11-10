# Risky Chain 2025 / risc-v

Writeup for the Challenge "Risky Chain" misc category in InfobahnCTF 2025 playing with THEM?!

---

**Category:** misc

**Author:** vielite

**Description:**

> Metal to the future!  
> nc riskychain.challs.infobahnc.tf 1337

## Challeng

Given is a network service which simulates a tiny blockchain VM. The service prints a mined block summary and asks you to submit:

- Nonce (hex)
- A RISC-V assembly contract, terminated by an empty line

You can interact via netcat or a socket client. An ELF binary was provided for local analysis.

---

## Step 1 --- Initial analysis

- I ran the provided ELF locally to inspect prompts and behavior. The binary prints a block summary and asks for the nonce and the RISC-V assembly contract. The service reads the assembly until it receives a completely empty line, then assembles and validates the block.
- Static inspection (strings, nm, objdump) revealed symbols for the ecall handler, block validation, hash calculation, and the RISC-V assembler/executor.

Observed prompt sequence:

```
Submit your new block's data.
Nonce (as hex):
Enter your RISC-V assembly contract (end with a blank line):
```

---

## Step 2 --- Key reversing notes

- `is_block_valid` contains a short-circuit: if the block's nonce equals `0xdeadbeef` the function returns valid immediately, bypassing PoW and other checks.
- `ecall_handler` checks a register for the syscall id. If the syscall id equals `1337`, it prints a message and reads `flag.txt` then prints it. The rodata contains the string `ECALL 1337: Nice! Here's your flag!`.
- The assembler accepts a subset of RISC-V (including `addi` and `ecall`). The server requires the contract input to be terminated by a blank line; otherwise it waits for more input.

Attack idea: submit the magic nonce to bypass validation, then submit a tiny RISC-V contract that sets the ECALL number to 1337 and calls `ecall`.

---

## Step 3 --- Exploit / manual solve

Manual steps using `nc` (interactive):

1. Connect:

```
nc riskychain.challs.infobahnc.tf 1337
```

2. When prompted, submit the nonce (hex):

```
deadbeef
```

3. Then submit the contract lines, and remember to end with one extra blank line so the server knows the contract is finished:

```
addi x10, x0, 1337
ecall

```

Why this works:

- `addi x10, x0, 1337` sets register x10 to 1337. The ECALL handler reads the syscall number from x10.
- `ecall` triggers the handler. With the block validated via `0xdeadbeef`, the handler prints the flag when it sees syscall 1337.

```python
# illustrate what to send
s.sendall(b"deadbeef\n")
s.sendall(b"addi x10, x0, 1337\n")
s.sendall(b"ecall\n\n")
```

---

## Flag

```
infobahn{Th3_futur3_15_m3t4l1c_4nd_RISC-V}
```

---

## Notes

- The intentional backdoor is the `0xdeadbeef` nonce in `is_block_valid`. That is the designed path to the flag for this challenge.
- The RISC-V interpreter executes the contract after block validation, and ECALL 1337 discloses the flag.
- Remember the final blank line to terminate the contract input.

