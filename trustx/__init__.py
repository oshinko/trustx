import hashlib

import base58
import ecdsa

curve = ecdsa.SECP256k1
hashfunc = hashlib.sha256


def get_address_from_verifying_key(vk, encoding='compressed'):
    enc = vk.to_string(encoding)
    rip = hashlib.new('ripemd160', hashfunc(enc).digest())
    keyhash = b'\0' + rip.digest()
    checksum = hashfunc(hashfunc(keyhash).digest()).digest()[:4]
    return base58.b58encode(keyhash + checksum).decode()
