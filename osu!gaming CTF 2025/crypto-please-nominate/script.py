from Crypto.Util.number import *

FLAG = open("flag.txt").read()

BNS = ["Plus4j", "Mattay", "Dailycore"]
print(len(FLAG))

for BN in BNS:
    print("message for", BN)
    message = bytes_to_long(
        (f"hi there {BN}, " + FLAG).encode()
    )
    n = getPrime(727) * getPrime(727)
    e = 3
    print(n)
    print(pow(message, e, n))