import argparse
import hashlib
import mmap
import re
import socket
from dataclasses import dataclass
from typing import Iterable

from Crypto.PublicKey import ECC

import add
import dpp


HOST = "dot.chals.dicec.tf"
PORT = 1337

P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
Q = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
G = ECC._curves["P-256"].G.copy()

N = 64
CIRCUIT = add.build_adder(N)
NUM_INPUTS = len(CIRCUIT.inputs)
TRACE_LEN = dpp.trace_len(CIRCUIT)
PROOF_LEN = dpp.proof_len(CIRCUIT)
BOUND1 = 2**8
BASE_B = TRACE_LEN * BOUND1 + 1

OUT_IDX = TRACE_LEN - 1
LAST_GATE = CIRCUIT.gates[-1]
LAST_LEFT_IDX = LAST_GATE.left.index
LAST_RIGHT_IDX = LAST_GATE.right.index
LAST_PAIR_IDX = dpp.pair_index(CIRCUIT, LAST_GATE.left.index, LAST_GATE.right.index)


def neg(point: ECC.EccPoint) -> ECC.EccPoint:
    return ECC.EccPoint(point.x, (-int(point.y)) % P, curve="P-256")


def point_mul(point: ECC.EccPoint, scalar: int) -> ECC.EccPoint:
    if scalar < 0:
        return (-scalar) * neg(point)
    return scalar * point


def point_from_xy(x: int, y: int) -> ECC.EccPoint:
    return ECC.EccPoint(x, y, curve="P-256")


def sqrt_mod(a: int) -> int:
    return pow(a, (P + 1) // 4, P)


def compress(point: ECC.EccPoint) -> bytes:
    prefix = 3 if int(point.y) & 1 else 2
    return bytes([prefix]) + int(point.x).to_bytes(32, "big")


def decompress(buf: bytes) -> ECC.EccPoint:
    if len(buf) != 33 or buf[0] not in (2, 3):
        raise ValueError("bad compressed point")
    x = int.from_bytes(buf[1:], "big")
    y_sq = (pow(x, 3, P) - 3 * x + B) % P
    y = sqrt_mod(y_sq)
    if (y * y - y_sq) % P != 0:
        raise ValueError("point is not on curve")
    if (y & 1) != (buf[0] & 1):
        y = (-y) % P
    return point_from_xy(x, y)


def hash_to_point(i: int) -> ECC.EccPoint:
    for ctr in range(256):
        x = int.from_bytes(
            hashlib.sha256(i.to_bytes(8, "little") + bytes([ctr])).digest(),
            "big",
        ) % P
        y_sq = (pow(x, 3, P) - 3 * x + B) % P
        y = sqrt_mod(y_sq)
        if (y * y - y_sq) % P == 0:
            return point_from_xy(x, y)
    raise ValueError(f"hash_to_point failed for {i}")


def point_offset(proof_index: int) -> int:
    return proof_index - NUM_INPUTS


def build_constraint_used_set() -> set[int]:
    used: set[int] = set()
    constraints: Iterable[dpp.LinearConstraint] = (
        list(dpp.input_constraints(CIRCUIT))
        + list(dpp.gate_constraints(CIRCUIT))
        + list(dpp.output_constraints(CIRCUIT))
    )
    for constraint in constraints:
        for idx, _ in constraint.scalars:
            used.add(idx)
    return used


USED_INDICES = build_constraint_used_set()
REF_CANDIDATES = [
    idx
    for idx in range(TRACE_LEN)
    if dpp.pair_index(CIRCUIT, idx, idx) not in USED_INDICES
    and dpp.pair_index(CIRCUIT, LAST_LEFT_IDX, idx) not in USED_INDICES
    and dpp.pair_index(CIRCUIT, LAST_RIGHT_IDX, idx) not in USED_INDICES
]


@dataclass
class Proof:
    h1: ECC.EccPoint
    h2: ECC.EccPoint

    def add(self, other: "Proof") -> "Proof":
        return Proof(self.h1 + other.h1, self.h2 + other.h2)

    def with_h2_shift(self, shift: ECC.EccPoint) -> "Proof":
        return Proof(self.h1.copy(), self.h2 + shift)

    def encode(self) -> bytes:
        return compress(self.h1) + compress(self.h2)


class CRS:
    def __init__(self, path: str):
        self.fp = open(path, "rb")
        self.mm = mmap.mmap(self.fp.fileno(), 0, access=mmap.ACCESS_READ)
        self.point_cache: dict[int, ECC.EccPoint] = {}
        self.hash_cache: dict[int, ECC.EccPoint] = {}

    def close(self) -> None:
        self.mm.close()
        self.fp.close()

    def crs_point(self, offset: int) -> ECC.EccPoint:
        point = self.point_cache.get(offset)
        if point is None:
            start = 33 * offset
            point = decompress(self.mm[start : start + 33])
            self.point_cache[offset] = point
        return point.copy()

    def hash_point(self, offset: int) -> ECC.EccPoint:
        point = self.hash_cache.get(offset)
        if point is None:
            point = hash_to_point(offset)
            self.hash_cache[offset] = point
        return point.copy()


def proof_offsets_for_inputs(inputs: list[int]) -> tuple[list[int], list[int]]:
    outputs, trace = CIRCUIT.evaluate(inputs)
    ones = [idx for idx, bit in enumerate(trace) if bit]
    offsets = [point_offset(idx) for idx in ones if idx >= NUM_INPUTS]
    for pos, idx1 in enumerate(ones):
        for idx2 in ones[: pos + 1]:
            offsets.append(point_offset(dpp.pair_index(CIRCUIT, idx1, idx2)))
    return outputs, offsets


def build_proof(crs: CRS, inputs: list[int]) -> Proof:
    outputs, offsets = proof_offsets_for_inputs(inputs)
    h1 = ECC.EccPoint(0, 0, curve="P-256")
    h2 = ECC.EccPoint(0, 0, curve="P-256")
    for offset in offsets:
        h1 += crs.hash_point(offset)
        h2 += crs.crs_point(offset)
    if any(outputs):
        return Proof(h1, h2)
    return Proof(h1, h2)


def proof_delta_from_offset(crs: CRS, offset: int, sign: int = 1) -> Proof:
    if sign == 1:
        return Proof(crs.hash_point(offset), crs.crs_point(offset))
    return Proof(neg(crs.hash_point(offset)), neg(crs.crs_point(offset)))


class Remote:
    def __init__(self, host: str, port: int):
        self.sock = socket.create_connection((host, port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.buf = b""

    def close(self) -> None:
        self.sock.close()

    def recv_until(self, marker: bytes) -> bytes:
        while marker not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise EOFError("server closed the connection")
            self.buf += chunk
        idx = self.buf.index(marker) + len(marker)
        out = self.buf[:idx]
        self.buf = self.buf[idx:]
        return out

    def recv_prompt(self) -> tuple[int, int]:
        blob = self.recv_until(b"answer: ")
        match = re.search(rb"what is (\d+) \+ (\d+)\? \(mod 2\^64\)", blob)
        if match is None:
            raise ValueError(blob.decode(errors="replace"))
        return int(match.group(1)), int(match.group(2))

    def submit(self, answer: int, proof: Proof) -> bytes:
        self.sock.sendall(f"{answer}\n".encode())
        self.recv_until(b"proof: ")
        self.sock.sendall(proof.encode().hex().encode() + b"\n")
        while True:
            while b"\n" in self.buf:
                line, self.buf = self.buf.split(b"\n", 1)
                if line.startswith((b"dice{", b"flag{")):
                    return line
                if line in (b"wrong...", b"correct! but that was obvious...", b"huh?"):
                    return line
            chunk = self.sock.recv(4096)
            if not chunk:
                raise EOFError("server closed the connection")
            self.buf += chunk


def correct_and_wrong_inputs(a: int, b: int) -> tuple[int, list[int], int, list[int]]:
    correct = (a + b) & ((1 << N) - 1)
    wrong = correct ^ 1
    in_correct = add.int_to_bits(a, N) + add.int_to_bits(b, N) + add.int_to_bits(correct, N)
    in_wrong = add.int_to_bits(a, N) + add.int_to_bits(b, N) + add.int_to_bits(wrong, N)
    return correct, in_correct, wrong, in_wrong


def test_free_weight(
    io: Remote,
    correct: int,
    proof_correct: Proof,
    delta: Proof,
    target: int,
) -> bool:
    candidate = proof_correct.add(delta).with_h2_shift(neg(point_mul(G, BASE_B * target)))
    result = io.submit(correct, candidate)
    return result.startswith(b"correct! but that was obvious...")


def find_abs_v(crs: CRS, io: Remote, correct: int, proof_correct: Proof, trace_idx: int) -> int:
    diag_idx = dpp.pair_index(CIRCUIT, trace_idx, trace_idx)
    diag_delta = proof_delta_from_offset(crs, point_offset(diag_idx))
    for abs_v in range(257):
        if test_free_weight(io, correct, proof_correct, diag_delta, abs_v * abs_v):
            return abs_v
    raise RuntimeError(f"failed to recover |v[{trace_idx}]|")


def recover_q2_last(crs: CRS, io: Remote, correct: int, proof_correct: Proof) -> tuple[int, int]:
    abs_out = find_abs_v(crs, io, correct, proof_correct, OUT_IDX)
    abs_left = find_abs_v(crs, io, correct, proof_correct, LAST_LEFT_IDX)
    abs_right = find_abs_v(crs, io, correct, proof_correct, LAST_RIGHT_IDX)

    ref_idx = None
    abs_ref = 0
    for candidate in REF_CANDIDATES:
        abs_ref = find_abs_v(crs, io, correct, proof_correct, candidate)
        if abs_ref != 0:
            ref_idx = candidate
            break
    if ref_idx is None:
        raise RuntimeError("failed to find a non-zero reference v entry")

    left_ref_delta = proof_delta_from_offset(
        crs, point_offset(dpp.pair_index(CIRCUIT, LAST_LEFT_IDX, ref_idx))
    )
    right_ref_delta = proof_delta_from_offset(
        crs, point_offset(dpp.pair_index(CIRCUIT, LAST_RIGHT_IDX, ref_idx))
    )
    left_ref_mag = 2 * abs_left * abs_ref
    right_ref_mag = 2 * abs_right * abs_ref

    sign_left_ref = 1 if test_free_weight(io, correct, proof_correct, left_ref_delta, left_ref_mag) else -1
    sign_right_ref = 1 if test_free_weight(io, correct, proof_correct, right_ref_delta, right_ref_mag) else -1
    q2_last = 2 * (sign_left_ref * sign_right_ref) * abs_left * abs_right
    return abs_out, q2_last


def forge_proof(crs: CRS, wrong_inputs: list[int], q2_last: int, abs_v_out: int, out_sign: int) -> Proof:
    proof_wrong = build_proof(crs, wrong_inputs)
    out_delta = proof_delta_from_offset(crs, point_offset(OUT_IDX), sign=1)
    last_pair_delta = proof_delta_from_offset(crs, point_offset(LAST_PAIR_IDX), sign=-1)
    shift = point_mul(G, BASE_B * q2_last - out_sign * abs_v_out)
    return proof_wrong.add(out_delta).add(last_pair_delta).with_h2_shift(shift)


def recover_correction(crs: CRS, host: str, port: int) -> tuple[int, int]:
    io = Remote(host, port)
    try:
        a, b = io.recv_prompt()
        correct, in_correct, wrong, in_wrong = correct_and_wrong_inputs(a, b)
        proof_correct = build_proof(crs, in_correct)
        return recover_q2_last(crs, io, correct, proof_correct)
    finally:
        io.close()


def run_final(crs: CRS, host: str, port: int, abs_v_out: int, q2_last: int) -> str:
    io = Remote(host, port)
    try:
        streak = 0
        out_sign = None
        while streak < 20:
            a, b = io.recv_prompt()
            _, _, wrong, in_wrong = correct_and_wrong_inputs(a, b)
            if out_sign is None:
                for guess in (1, -1):
                    proof = forge_proof(crs, in_wrong, q2_last, abs_v_out, guess)
                    result = io.submit(wrong, proof)
                    if result.startswith(b"huh?"):
                        out_sign = guess
                        streak += 1
                        break
                if out_sign is None:
                    raise RuntimeError("failed to recover sign(v_out)")
                continue
            proof = forge_proof(crs, in_wrong, q2_last, abs_v_out, out_sign)
            result = io.submit(wrong, proof)
            if result.startswith(b"huh?"):
                streak += 1
            elif result.startswith((b"dice{", b"flag{")):
                return result.decode()
            else:
                raise RuntimeError(f"unexpected response during final run: {result!r}")
        if b"dice{" in io.buf or b"flag{" in io.buf:
            match = re.search(rb"(dice\{.*?\}|flag\{.*?\})", io.buf)
            if match:
                return match.group(1).decode()
        while True:
            chunk = io.sock.recv(4096)
            if not chunk:
                raise EOFError(f"flag not received; leftover={io.buf!r}")
            io.buf += chunk
            match = re.search(rb"(dice\{.*?\}|flag\{.*?\})", io.buf)
            if match:
                return match.group(1).decode()
    finally:
        io.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--crs", default="crs.bin")
    args = parser.parse_args()

    crs = CRS(args.crs)
    try:
        abs_v_out, q2_last = recover_correction(crs, args.host, args.port)
        flag = run_final(crs, args.host, args.port, abs_v_out, q2_last)
        print(flag)
    finally:
        crs.close()


if __name__ == "__main__":
    main()
