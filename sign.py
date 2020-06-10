import hashlib
import pathlib
import sys

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


verbose = '--verbose' in sys.argv[1:] or '-v' in sys.argv[1:]

if 'gen' in sys.argv[1:2]:
    sk = ecdsa.SigningKey.generate(curve, hashfunc=hashfunc)
    assert sk == ecdsa.SigningKey.from_string(sk.to_string(), curve, hashfunc)
    print(sk.to_string().hex())
    exit()

data = """
word:
  level: 3
excel:
  level: 3
""".strip().encode('utf8')

try:
    i = sys.argv.index('--data')
except ValueError:
    pass
else:
    if len(sys.argv[1:]) >= i + 1:
        data = pathlib.Path(sys.argv[i + 1]).read_bytes()

pk = bytes.fromhex(input().strip())
sk = ecdsa.SigningKey.from_string(pk, curve, hashfunc)
vk = sk.verifying_key

compressed_public_key = vk.to_string('compressed')

vk_ = ecdsa.VerifyingKey.from_string(compressed_public_key, curve, hashfunc)
assert vk == vk_

sig = sk.sign(data)
b58sig = base58.b58encode(sig).decode('ascii')

assert vk.verify(sig, data)

sk2 = ecdsa.SigningKey.generate(curve, hashfunc=hashfunc)
sig2 = sk2.sign(data)

try:
    vk.verify(sig2, data)
except ecdsa.BadSignatureError:
    pass
else:
    assert False

if verbose:
    print('data (hash)', hashfunc(data).hexdigest())
    print('public key', vk.to_string().hex())
    print('public key (uncompressed, hex)', vk.to_string('uncompressed').hex())
    print('public key (compressed, hex)', compressed_public_key.hex())
    print('address (uncompressed, b58)',
          get_address_from_verifying_key(vk, 'uncompressed'))
    print('address (compressed, b58)', get_address_from_verifying_key(vk))
    print('signature (hex)', sig.hex())
    print('signature (b58)', b58sig)
else:
    print(b58sig)
