#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import hashlib
import socket
import subprocess

from srdnlengarble import BinaryCircuit, BinaryGate
import common
from srdnlengarble.garble.evaluator import Evaluator

P = 2**255 - 19
A_CURVE = 19298681539552699237261830834781317975544997444273427339909597334573241639236
B_CURVE = 55751746669818908907645289078257140818241103727901012315294400837956729358436
Q = 2**252 + 27742317777372353535851937790883648493

def inv(n):
    return pow(n, P - 2, P)

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_infinity = (x is None and y is None)

    def __add__(self, other):
        if self.is_infinity: return other
        if other.is_infinity: return self
        if self.x == other.x and self.y != other.y: return Point(None, None)
        if self.x == other.x and self.y == other.y: return self.double()
        m = ((other.y - self.y) * inv(other.x - self.x)) % P
        x3 = (m**2 - self.x - other.x) % P
        y3 = (m * (self.x - x3) - self.y) % P
        return Point(x3, y3)

    def double(self):
        if self.is_infinity: return self
        m = ((3 * self.x**2 + A_CURVE) * inv(2 * self.y)) % P
        x3 = (m**2 - 2 * self.x) % P
        y3 = (m * (self.x - x3) - self.y) % P
        return Point(x3, y3)

    def __mul__(self, k):
        assert isinstance(k, int)
        k = k % Q
        result = Point(None, None)
        addend = self
        while k:
            if k & 1: result = result + addend
            addend = addend.double()
            k >>= 1
        return result
        
    def __rmul__(self, k):
        return self.__mul__(k)

G = Point(19298681539552699237261830834781317975544997444273427339909597334652188435546,
          14781619447589544791020593568409986887264606134616475288964881837755586237401)

def point_to_bytes(point):
    if point.is_infinity:
        return b'\x00' * 32
    return (point.x | ((point.y & 1) << 255)).to_bytes(32, 'little')

def point_from_bytes(data):
    if data == b'\x00' * 32:
        return Point(None, None)
    x = int.from_bytes(data, 'little')
    bit, x = x >> 255, x & ((1 << 255) - 1)
    y2 = (pow(x, 3, P) + A_CURVE * x + B_CURVE) % P
    y = pow(y2, (P + 3) // 8, P)
    if pow(y, 2, P) == y2:
        pass
    elif pow(y, 2, P) == (-y2) % P:
        y = (y * pow(2, (P - 1) // 4, P)) % P
    else:
        raise ValueError("invalid point encoding")
    if (y & 1) != bit:
        y = P - y
    return Point(x, y)

def hash_point(point, tweak):
    data = point_to_bytes(point) + tweak
    digest = hashlib.shake_128(data).digest(16)
    return int.from_bytes(digest, 'big')

class ProxyIO:
    def __init__(self, in_pipe, out_fd):
        self.in_pipe = in_pipe
        self.out_fd = out_fd
    def sendall(self, data):
        self.in_pipe.write(data)
        self.in_pipe.flush()
    def recv(self, n):
        import os
        data = b''
        while len(data) < n:
            c = os.read(self.out_fd, n - len(data))
            if not c: break
            data += c
        return data

from srdnlengarble.garble.channel import Channel
class SocketChannel(Channel):
    def __init__(self, io_wrapper):
        self.io = io_wrapper
    def send_wire(self, wire):
        data = wire.to_bytes(16, 'big')
        self.io.sendall(data.hex().encode() + b'\n')
    def read_wire(self):
        line = recvuntil(self.io, b'\n').strip()
        return int(line.decode(), 16)
    def send_point(self, point):
        data = point_to_bytes(point)
        try:
            self.io.sendall(data.hex().encode() + b'\n')
        except BrokenPipeError:
            import os
            print("Broken pipe! Server output:", os.read(self.io.out_fd, 4096).decode(errors='replace'))
            raise
    def read_point(self):
        line = recvuntil(self.io, b'\n').strip()
        data = bytes.fromhex(line.decode())
        return point_from_bytes(data)

class MyReceiver:
    def __init__(self, channel):
        self.channel = channel
        self.P_raw = recvuntil(self.channel.io, b'\n').strip()
        print("Received P:", self.P_raw.decode())
        self.P = point_from_bytes(bytes.fromhex(self.P_raw.decode()))
        self.counter = 0

    def receive(self, choices):
        ks = []
        import secrets
        for bit in choices:
            r = secrets.randbelow(Q - 1) + 1
            if bit:
                R = r * G + self.P
            else:
                R = r * G
            self.channel.send_point(R)
            k = hash_point(r * self.P, self.counter.to_bytes(16, 'little'))
            ks.append(k)
            self.counter += 1
            
        wires = []
        for k, bit in zip(ks, choices):
            c0 = self.channel.read_wire()
            c1 = self.channel.read_wire()
            wire = c1 ^ k if bit else c0 ^ k
            wires.append(wire)
        return wires


def get_hash(wires, tweak):
    if not isinstance(wires, list): wires = [wires]
    hashed_labels = []
    for wire in wires:
        hasher = hashlib.shake_128()
        hasher.update(wire.to_bytes(16, 'big'))
        hasher.update(tweak)
        hashed_labels.append(int.from_bytes(hasher.digest(16), 'big'))
    return hashed_labels

def ungarble_and_gate(A_actual, B_actual, gate0, gate1, gate_num, delta):
    g = gate_num.to_bytes(16, 'big')
    
    B_LSB = B_actual & 1
    if B_LSB == 0:
        B0, B1 = B_actual, B_actual ^ delta
    else:
        B0, B1 = B_actual ^ delta, B_actual
        
    hashB0 = get_hash([B0], g)[0]
    hashB1 = get_hash([B1], g)[0]
    
    A0 = gate1 ^ hashB1 ^ hashB0
    A1 = A0 ^ delta
    
    if A_actual == A0:
        v_A = 0
    elif A_actual == A1:
        v_A = 1
    else:
        v_A = None
        
    v_B = None
    if v_A is not None:
        hashA0 = get_hash([A0], g)[0]
        hashA1 = get_hash([A1], g)[0]
        alpha = A0 & 1
        for r_guess in (0, 1):
            X = hashA0 ^ (delta if (alpha * r_guess % 2 == 1) else 0)
            idx = r_guess if alpha == 0 else 0
            gate0_guess = hashA1 ^ (X if idx == 0 else X ^ delta)
            if gate0_guess == gate0:
                v_B = B_LSB ^ r_guess
                break
                
    return A0, v_A, v_B

wire_lineage = {}

def apply_monkey_patch(bc: BinaryCircuit):
    bc._and_gate_count = 0
    orig_add_and = bc.add_and_gate
    def hooked_add_and(left, right):
        out = orig_add_and(left, right)
        bc._and_gate_count += 1
        wire_lineage[out] = (set(), 0, False) 
        return out
    bc.add_and_gate = hooked_add_and

    orig_add_xor = bc.add_xor_gate
    def hooked_add_xor(left, right):
        out = orig_add_xor(left, right)
        wl_left, c_left, lin_left = wire_lineage.get(left, (set(), 0, True))
        wl_right, c_right, lin_right = wire_lineage.get(right, (set(), 0, True))
        wire_lineage[out] = (wl_left ^ wl_right, c_left ^ c_right, lin_left and lin_right)
        return out
    bc.add_xor_gate = hooked_add_xor

    orig_add_not = bc.add_not_gate
    def hooked_add_not(left):
        out = orig_add_not(left)
        wl_left, c_left, lin_left = wire_lineage.get(left, (set(), 0, True))
        wire_lineage[out] = (wl_left.copy(), c_left ^ 1, lin_left)
        return out
    bc.add_not_gate = hooked_add_not
    
def solve_gf2(A, b):
    matrix = [row + [val] for row, val in zip(A, b)]
    rank = 0
    rows = len(matrix)
    cols = len(matrix[0]) - 1
    
    for col in range(cols):
        pivot = -1
        for row in range(rank, rows):
            if matrix[row][col]:
                pivot = row
                break
        if pivot != -1:
            matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
            for row in range(rank + 1, rows):
                if matrix[row][col]:
                    for c in range(cols + 1):
                        matrix[row][c] ^= matrix[rank][c]
            rank += 1
            
    ans = [0] * cols
    for i in range(rank - 1, -1, -1):
        for j in range(cols):
            if matrix[i][j]:
                val = matrix[i][-1]
                for k in range(j + 1, cols):
                    if matrix[i][k]:
                        val ^= ans[k]
                ans[j] = val
                break
    return ans

def recvuntil(io, token):
    data = b''
    while token not in data:
        c = io.recv(1)
        if not c: break
        data += c
    return data

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'remote':
        host, port = sys.argv[2], sys.argv[3]
        p = subprocess.Popen(['nc', host, port], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        io_wrapper = ProxyIO(p.stdin, p.stdout.fileno())
    else:
        p = subprocess.Popen(['python3', 'server.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        io_wrapper = ProxyIO(p.stdin, p.stdout.fileno())

    import time
    t0 = time.time()
    def tprint(msg):
        print(f"[{time.time() - t0:.2f}s] {msg}")

    tprint("Connected. Generating local circuit...");
    recvuntil(io_wrapper, b'Enter circuit name and args (hex encoded JSON): ')
    
    circuit = []
    circuit.append({"type": "XOR", "inputs": ["x0", "x0"], "output": "Z"})
    circuit.append({"type": "NOT", "inputs": ["Z"], "output": "O"})
    circuit.append({"type": "AND", "inputs": ["Z", "O"], "output": "Z_AND_O"})
    
    for i in range(128):
        circuit.append({"type": "XOR", "inputs": [f"x{i}", "Z"], "output": f"y{i}"})
        
    fhaes = common.FHAES()
    apply_monkey_patch(fhaes.binary_circuit)
    
    for i, w in enumerate(fhaes.key):
        for j, wire_id in enumerate(w.wires):
            wire_lineage[wire_id] = ({i*8 + j}, 0, True)
    
    ct_gf2e = fhaes.evaluator_bytes(16)
    ct_new = fhaes.output_bytes(16)
    tprint("Decrypting ct..."); pt = fhaes.decrypt(ct_gf2e)
    
    bc = fhaes.binary_circuit
    C_OUT_GATES = {}
    
    wires_map = dict()
    for i, byte in enumerate(pt):
        for j in range(8):
            wires_map[f"x{i * 8 + j}"] = byte.wires[j]
            
    add_gate = {
        'EQ': bc.add_equality_constraint, 
        'NOT': bc.add_not_gate, 
        'AND': bc.add_and_gate, 
        'XOR': bc.add_xor_gate
    }
    
    for gate in circuit:
        gate_type = gate.get('type')
        inputs = gate.get('inputs')
        inputs = [wires_map[label] for label in inputs]
        output = gate.get('output')
        wires_map[output] = add_gate[gate_type](*inputs)
        if gate_type == 'AND':
            C_OUT_GATES[output] = bc._and_gate_count - 1
            
    pt_new = []
    from srdnlengarble.wires import GF2E
    for i in range(len(pt)):
        ws = [wires_map[f"y{i * 8 + j}"] for j in range(8)]
        pt_new.append(GF2E(bc, ws, fhaes.modulus))
        
    for x, y in zip(fhaes.encrypt(pt_new), ct_new):
        x == y
        
    circuit_json = json.dumps(circuit).encode().hex()
    tprint("Sending JSON..."); io_wrapper.sendall(f"custom_circuit {circuit_json}\n".encode())
    
    channel = SocketChannel(io_wrapper)
    evaluator = Evaluator(channel)
    key_evaluator = [channel.read_wire() for _ in range(128)]
    
    receiver = MyReceiver(channel)
    evaluator_wires = []
    
    ct_bytes = b'\x00' * 16
    choices = common.bytes_to_bits(ct_bytes)
    
    recvuntil(io_wrapper, b"Sending evaluator input wires for ct (128 bits)...\n")
    wires = receiver.receive(choices)
    evaluator_wires.extend(wires)
    
    recvuntil(io_wrapper, b"Evaluating circuit...\n")
    
    wire_map_online = {}
    for i, wire_id in enumerate(bc.garbler_inputs):
        wire_map_online[wire_id] = key_evaluator[i]
    for i, wire_id in enumerate(bc.evaluator_inputs):
        wire_map_online[wire_id] = evaluator_wires[i]
        
    gate_count = 0
    gate_results = []
    
    for gate in bc.gates:
        if isinstance(gate, BinaryGate.Xor):
            wire_map_online[gate.output_wire] = wire_map_online[gate.input_left] ^ wire_map_online[gate.input_right]
        elif isinstance(gate, BinaryGate.Not):
            wire_map_online[gate.output_wire] = wire_map_online[gate.input_wire]
        elif isinstance(gate, BinaryGate.EqualityConstraint):
            lhs = wire_map_online.get(gate.lhs, None)
            rhs = wire_map_online.get(gate.rhs, None)
            if lhs is not None and rhs is not None:
                pass
            elif lhs is not None:
                wire_map_online[gate.rhs] = lhs
            elif rhs is not None:
                wire_map_online[gate.lhs] = rhs
        elif isinstance(gate, BinaryGate.And):
            gate0 = channel.read_wire()
            gate1 = channel.read_wire()
            
            gate_results.append({
                'A': wire_map_online[gate.input_left],
                'B': wire_map_online[gate.input_right],
                'gate0': gate0,
                'gate1': gate1,
                'gate_num': gate_count,
                'left_wire': gate.input_left,
                'right_wire': gate.input_right
            })
            
            A = wire_map_online[gate.input_left]
            B = wire_map_online[gate.input_right]
            g = gate_count.to_bytes(16, 'big')
            hashA, hashB = get_hash([A, B], g)
            L = hashA if (A & 1) == 0 else hashA ^ gate0
            R = hashB if (B & 1) == 0 else hashB ^ gate1
            wire_map_online[gate.output_wire] = L ^ R ^ (A * (B & 1))
            
            gate_count += 1
            
    for _ in bc.outputs:
        channel.read_wire()
        channel.read_wire()
        
    g_ZO = gate_results[C_OUT_GATES["Z_AND_O"]]
    delta = g_ZO['gate0'] ^ g_ZO['gate1']
    print(f"[*] Extracted Delta: {hex(delta)}")
    
    wire_semantics = {}
    for i, w in enumerate(fhaes.key):
        for j, wire_id in enumerate(w.wires):
            wire_semantics[wire_id] = ({i*8 + j}, 0)
            
    equations = []
    vals = []
 
    gate_count = 0
    tprint(f"Tracking semantics through 1500 gates...")
    for gate in bc.gates:
        if isinstance(gate, BinaryGate.Xor):
            sL_set, sL_c = wire_semantics.get(gate.input_left, (set(), 0))
            sR_set, sR_c = wire_semantics.get(gate.input_right, (set(), 0))
            wire_semantics[gate.output_wire] = (sL_set ^ sR_set, sL_c ^ sR_c)
        elif isinstance(gate, BinaryGate.Not):
            sL_set, sL_c = wire_semantics.get(gate.input_wire, (set(), 0))
            wire_semantics[gate.output_wire] = (sL_set.copy(), sL_c ^ 1)
        elif isinstance(gate, BinaryGate.EqualityConstraint):
            lhs = wire_semantics.get(gate.lhs, None)
            rhs = wire_semantics.get(gate.rhs, None)
            if lhs is not None and rhs is not None: pass
            elif lhs is not None: wire_semantics[gate.rhs] = lhs
            elif rhs is not None: wire_semantics[gate.lhs] = rhs
        elif isinstance(gate, BinaryGate.And):
            gr = gate_results[gate_count]
            A_actual = gr['A']
            B_actual = gr['B']
            A0, v_A, v_B = ungarble_and_gate(A_actual, B_actual, gr['gate0'], gr['gate1'], gr['gate_num'], delta)
            
            sL_set, sL_c = wire_semantics.get(gate.input_left, (set(), 0))
            sR_set, sR_c = wire_semantics.get(gate.input_right, (set(), 0))
            
            if len(sL_set) > 0 and v_A is not None:
                row = [1 if i in sL_set else 0 for i in range(128)]
                equations.append(row)
                vals.append(v_A ^ sL_c)
            if len(sR_set) > 0 and v_B is not None:
                row = [1 if i in sR_set else 0 for i in range(128)]
                equations.append(row)
                vals.append(v_B ^ sR_c)
                
            wire_semantics[gate.output_wire] = (set(), v_A & v_B if v_A is not None and v_B is not None else 0)
            
            gate_count += 1
                
    tprint(f"[*] Collected {len(equations)} linear equations over GF(2) after tracing semantic bits")

    print(f"[*] Collected {len(equations)} linear equations over GF(2)")
    
    key_bits = solve_gf2(equations, vals)
    key_bytes = common.bits_to_bytes(key_bits)
    
    print(f"[*] Extracted Key (local/remote): {key_bytes.hex()}")
    
    print(f"[*] Extracted Key (local/remote): {key_bytes.hex()}")
    
    import time
    time.sleep(1)
    
    tprint("Breaking server loop...")
    io_wrapper.sendall(b'\n')
    
    time.sleep(1)
    tprint("Sending key guess...")
    io_wrapper.sendall(key_bytes.hex().encode() + b'\n')
    
    time.sleep(1)
    try:
        resp = io_wrapper.recv(4096)
        print("Server response:", resp.decode(errors='ignore'))
    except Exception as e:
        print("Exception reading response:", e)

if __name__ == '__main__':
    main()
