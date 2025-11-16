#!/usr/bin/env python3
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes
from pwn import xor
import os, sys, random

FLAG = os.getenv("FLAG", "flag{b3n34th_th3_m45k_pwnsecsocool}").encode()
    
class LCG:
    def __init__(self, m=1<<64):
        self.m = m
        self.a = random.getrandbits(64)|1
        self.c = random.getrandbits(64)|1
        self.x = random.getrandbits(64)
    def next(self): 
        self.x=(self.a*self.x+self.c)%self.m
        return self.x
    def stream(self, n):
        out=b""
        while len(out)<n: out+=self.next().to_bytes(8,"big")
        return out[:n]

class RSA:
    def __init__(self, bits=512, e=65537):
        self.e=e
        self.p=getPrime(bits//2)
        self.q=getPrime(bits//2)
        self.n=self.p*self.q
    def enc(self, m_bytes, mod):
        k=(mod.bit_length()+7)//8
        m=bytes_to_long(m_bytes)
        assert m<mod
        return long_to_bytes(pow(m,self.e,mod),k)

def main():
    random.seed(os.urandom(16))
    rsa, lcg = RSA(bits=512), LCG()
    Cflag = rsa.enc(FLAG, rsa.n)
    enc_flag = xor(Cflag, lcg.stream(len(Cflag)))

    banner = """                                                                                                                                         
       *%@@@@@@@@@@@@@@@@%   
     +%%%%%%%%%%%%%%%%%%%%*  
    *#%%%%%%%%%%%%%%%%%%%%#  
    *#%%%%%%%%%%%%%%%%%%%%*  
   **#%%%%%%%%%%%%%%%%%%%%   
   +*#################***    
   +*##=      **##%#****     
   +*#*        #%%@%%#       
   +*####*  ####%%@%#        
   +#######%%%%%%%%%%        
   +####%%%%%%%%%%%%%*       
   +*#########%%#%%%%%       
   -**#########***++***      
    +**#######*-=+==         
    =+**##########*+         
     +***######=             
     =+****+                 
      =+**                   
       =+-                   
                                                                         
        welcome to the opera! unveil the mask and reveal the secret hidden within.
    """
    print(banner)
    menu="1) get encrypted flag\n2) encrypt your input\n3) exit\n> "
    while True:
        try:
            c=input(menu).strip()
            if c=="1":
                print(enc_flag.hex())
                print(rsa.n)  
            elif c=="2":
                s=input("> ")
                m=s.encode()
                if bytes_to_long(m)>=rsa.p: 
                    print("too long")
                    continue
                C=rsa.enc(m, rsa.p)
                print(xor(C, lcg.stream(len(C))).hex())  
            elif c=="3":
                print("bye")
                return
            else: 
                print("don't waste our time")
                return
        except:
            print("error")
            sys.exit(0)

if __name__=="__main__": main()