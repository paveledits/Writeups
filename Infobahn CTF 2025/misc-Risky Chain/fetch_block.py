#!/usr/bin/env python3

import socket, argparse, time, re, binascii, sys, os
DEFAULT_HOST = "riskychain.challs.infobahnc.tf"
DEFAULT_PORT = 1337
OUT_PATH = "block_preview.txt"
HEX_DECODE_PATH = "block_hex_blob.bin"
def recv_until_marker(s, marker="Nonce (as hex):", timeout=4.0):
    s.settimeout(0.5)
    buf = b""
    t0 = time.time()
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            if marker.encode() in buf:
                return buf
        except socket.timeout:
            pass
        if time.time() - t0 > timeout:
            return buf
    return buf
def find_hex_blobs(text):
    candidates = re.findall(r'[0-9a-fA-F]{32,}', text)
    return candidates
def main():
    parser = argparse.ArgumentParser(description="Fetch block banner & extract hex blobs")
    parser.add_argument('--host', default=DEFAULT_HOST)
    parser.add_argument('--port', default=DEFAULT_PORT, type=int)
    args = parser.parse_args()
    print(f"Connecting to {args.host}:{args.port} ...")
    try:
        with socket.create_connection((args.host, args.port), timeout=8) as s:
            data = recv_until_marker(s, marker="Nonce (as hex):", timeout=4.0)
            if not data:
                print("(no banner received)")
                return
            try:
                text = data.decode(errors='ignore')
            except:
                text = repr(data[:400])
            with open(OUT_PATH, "wb") as f:
                f.write(data)
            print(f"Saved banner to {OUT_PATH}\n")
            print("Banner preview:\n" + "-"*40)
            print(text)
            print("-"*40)
            blobs = find_hex_blobs(text)
            if not blobs:
                print("No long hex blobs detected in the banner.")
                return
            for i, hb in enumerate(blobs):
                print(f"Hex blob #{i+1}: length {len(hb)} chars")
            chosen = blobs[0]
            print("\nDecoding first blob and writing to", HEX_DECODE_PATH)
            try:
                raw = binascii.unhexlify(chosen)
                with open(HEX_DECODE_PATH, "wb") as f:
                    f.write(raw)
                null_positions = [i for i, b in enumerate(raw) if b == 0]
                print(f"Decoded {len(raw)} bytes; null bytes count: {len(null_positions)}")
                if null_positions:
                    print("First 10 null positions:", null_positions[:10])
                else:
                    print("No null bytes found in decoded blob.")
            except Exception as e:
                print("Failed to decode hex blob:", e)
                return
    except Exception as e:
        print("Connection error:", e)
        sys.exit(1)
if __name__ == '__main__':
    main()
